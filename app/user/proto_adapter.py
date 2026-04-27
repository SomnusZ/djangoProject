"""
proto_adapter.py  —  用户模块 Protobuf 适配层

职责：
    1. 响应方向（Renderer 侧）：
       将视图返回的 Python dict（success_response / error_response 的输出）
       转换为用户模块专属的强类型 protobuf 消息对象。
       入口：get_user_builder(action, method) -> builder 函数

    2. 请求方向（Parser 侧）：
       根据 action + method 返回对应的 proto 请求消息类，
       由 ProtobufParser 用来反序列化客户端发来的二进制请求体。
       入口：get_user_request_message_class(action, method) -> 消息类

与视图层的关系：
    视图层（views.py）完全不感知 protobuf，仍然使用 success_response / error_response
    返回 dict。protobuf 的转换在 ProtobufRenderer 调用 adapter 时发生，
    即在响应被序列化输出之前的最后一步。

    请求方向同理：视图层通过 request.data 获取数据，
    ProtobufParser 已在更早阶段将二进制解析为 dict，视图无感知。
"""

from app.proto.user_pb2 import (
    # 响应消息类
    UserResponse,
    UserLoginResponse,
    # 响应内嵌结构
    UserInfo,
    LoginData,
    TokenPair,
    # 请求消息类
    CreateUserRequest,
    LoginRequest,
    UpdateUserRequest,
)


# =============================================================================
# 内部工具函数（Internal helpers）
# 仅在本模块内使用，不对外暴露。
# =============================================================================

def _fill_user_info(dst: UserInfo, src: dict) -> None:
    """将 dict 中的用户字段写入 proto UserInfo 消息对象。

    参数：
        dst : 目标 UserInfo proto 对象（原地修改）
        src : 来自 UserSerializer(user).data 的 dict，
              包含 user_id / user_name / user_profile_picture /
              user_phone_number / user_mail_address 等字段。

    注意：
        - 用 `or ""` / `or 0` 处理 None 值，确保 proto 字段始终为合法类型。
          proto3 不允许 None，所有字段都有默认值（int→0, string→""）。
        - user_password 不在 UserSerializer 中暴露，无需处理。
    """
    if not isinstance(src, dict):
        return
    dst.user_id              = int(src.get("user_id") or 0)
    dst.user_name            = str(src.get("user_name") or "")
    dst.user_profile_picture = str(src.get("user_profile_picture") or "")
    dst.user_phone_number    = str(src.get("user_phone_number") or "")
    dst.user_mail_address    = str(src.get("user_mail_address") or "")
    dst.user_status          = int(src.get("user_status") or 0)
    dst.user_role            = int(src.get("user_role") or 0)


def _fill_token_pair(dst: TokenPair, src: dict) -> None:
    """将 dict 中的 JWT 令牌字段写入 proto TokenPair 消息对象。

    参数：
        dst : 目标 TokenPair proto 对象（原地修改）
        src : 包含 access_token / refresh_token 的 dict，
              由视图层调用 RefreshToken.for_user(user) 生成。
    """
    if not isinstance(src, dict):
        return
    dst.access_token  = str(src.get("access_token") or "")
    dst.refresh_token = str(src.get("refresh_token") or "")


def _fill_login_data(dst: LoginData, src: dict) -> None:
    """将登录响应的 data dict 写入 proto LoginData 消息对象。

    登录响应的 data 结构（JSON）：
        {
            "user":  { "user_id": 1, "user_name": "...", ... },
            "token": { "access_token": "...", "refresh_token": "..." }
        }

    参数：
        dst : 目标 LoginData proto 对象（原地修改）
        src : 上述结构的 Python dict
    """
    if not isinstance(src, dict):
        return
    user_obj  = src.get("user")
    token_obj = src.get("token")
    if isinstance(user_obj, dict):
        _fill_user_info(dst.user, user_obj)
    if isinstance(token_obj, dict):
        _fill_token_pair(dst.token, token_obj)


def _set_message_content(msg, raw) -> None:
    """填充响应消息的 oneof message_content 字段。

    proto 定义（UserResponse / UserLoginResponse 共用）：
        oneof message_content {
            string          text  = 4;   // 纯文本消息
            ValidationError error = 5;   // 字段级校验错误
        }

    规则：
        - str  -> msg.text  = raw
          适用于：业务成功消息（"注册成功"）、单条错误（"密码错误"、"用户不存在"）
        - dict -> msg.error （DRF 序列化器校验错误格式）
          DRF 校验错误结构（JSON）：{"user_phone_number": ["手机号已存在"], ...}
          转换方式：对 dict 的每个 key（字段名），
                    在 msg.error.fields[key] 中追加对应的字符串列表。
                    google.protobuf.ListValue 的每个元素用 .string_value 赋值。
        - None / 其他 -> msg.text = ""（默认空文本，避免 proto 字段未赋值）

    参数：
        msg : UserResponse 或 UserLoginResponse 的实例（原地修改）
        raw : payload.get("message") 的原始值，可能为 str / dict / None
    """
    if isinstance(raw, str):
        # 最常见情况：纯文本消息，直接赋值给 text 分支
        msg.text = raw
    elif isinstance(raw, dict):
        # DRF 字段级校验错误：{"field_name": ["error1", "error2"], ...}
        for field_name, errors in raw.items():
            # msg.error.fields 是 map<string, ListValue>，直接用 key 访问会自动创建条目
            lv = msg.error.fields[field_name]
            if isinstance(errors, list):
                for err in errors:
                    # ListValue.values 是 repeated Value，追加一个 string_value 元素
                    lv.values.add().string_value = str(err)
            else:
                # 极少数情况下 errors 不是列表（如 non_field_errors 直接是字符串）
                lv.values.add().string_value = str(errors)
    else:
        # None 或其他不可预期类型：降级为空字符串，不让 oneof 留空
        msg.text = str(raw) if raw is not None else ""


# =============================================================================
# 响应方向：Builder 函数
# 每个函数对应一组接口，负责将 dict payload 构造为强类型 proto 消息。
# =============================================================================

def build_user_response(payload: dict) -> UserResponse:
    """构建用户注册 / 修改 / 查询接口的 proto 响应消息。

    对应接口：
        POST /api/users/createUser/  （注册）
        PUT  /api/users/updateUser/  （修改用户名）
        GET  /api/users/dirUser/     （查询用户信息）

    参数：
        payload : success_response 或 error_response 返回的 dict，结构为：
                  { "result": "success"|"fail", "success": bool,
                    "data": dict|None, "message": str|dict }
    返回：
        UserResponse proto 消息对象，调用方执行 .SerializeToString() 输出二进制。
    """
    msg = UserResponse()
    msg.result  = str(payload.get("result", "success"))
    msg.success = bool(payload.get("success", True))
    _set_message_content(msg, payload.get("message"))

    # data 只有在操作成功且不为 None 时才有用户信息
    data = payload.get("data")
    if isinstance(data, dict):
        _fill_user_info(msg.data, data)
    return msg


def build_user_login_response(payload: dict) -> UserLoginResponse:
    """构建用户登录接口的 proto 响应消息。

    对应接口：POST /api/users/dirUser/（login_type=password 或 login_type=code）

    参数：
        payload : 同 build_user_response，但 data 结构不同：
                  { "result": ..., "success": ...,
                    "data": { "user": {...}, "token": {...} }, "message": ... }
    返回：
        UserLoginResponse proto 消息对象。
    """
    msg = UserLoginResponse()
    msg.result  = str(payload.get("result", "success"))
    msg.success = bool(payload.get("success", True))
    _set_message_content(msg, payload.get("message"))

    data = payload.get("data")
    if isinstance(data, dict):
        _fill_login_data(msg.data, data)
    return msg


# =============================================================================
# 响应方向：Builder 分发函数（供 proto_registry 调用）
# =============================================================================

def get_user_builder(action: str, method: str):
    """根据 DRF action + HTTP method 返回对应的响应 builder 函数。

    由 proto_registry.get_builder() 调用，返回值再由 ProtobufRenderer 调用。

    映射规则：
        dir_user  + POST  -> build_user_login_response （登录）
        create_user + POST -> build_user_response       （注册）
        update_user + PUT|PATCH -> build_user_response  （修改）
        dir_user  + GET   -> build_user_response        （查询）

    参数：
        action : DRF ViewSet action 名称（由 @action 装饰器 + url_path 决定）
        method : HTTP 方法字符串（由 ProtobufRenderer 从 request 中取出）
    返回：
        Callable[[dict], protobuf.Message] 或 None（无匹配时回退通用 ApiEnvelope）
    """
    method = (method or "").upper()
    if action == "dir_user" and method == "POST":
        return build_user_login_response
    if action in {"create_user", "update_user"}:
        return build_user_response
    if action == "dir_user" and method == "GET":
        return build_user_response
    return None


# =============================================================================
# 请求方向：消息类分发函数（供 proto_registry 调用）
# =============================================================================

def get_user_request_message_class(action: str, method: str):
    """根据 DRF action + HTTP method 返回对应的 proto 请求消息类。

    由 proto_registry.get_request_message_class() 调用，
    返回值再由 ProtobufParser 用来实例化并反序列化请求体二进制。

    映射规则：
        create_user + POST      -> CreateUserRequest
        dir_user    + POST      -> LoginRequest
        update_user + PUT|PATCH -> UpdateUserRequest
        dir_user    + GET       -> None（GET 通过 URL 参数，无请求体）

    参数：
        action : DRF ViewSet action 名称
        method : HTTP 方法字符串
    返回：
        proto 消息类（class 对象本身，如 CreateUserRequest），
        或 None（无需请求体时，ProtobufParser 返回空 dict）
    """
    method = (method or "").upper()
    if action == "create_user" and method == "POST":
        return CreateUserRequest       # 注册：手机号、密码、确认密码、验证码
    if action == "dir_user" and method == "POST":
        return LoginRequest            # 登录：手机号、登录方式、密码或验证码
    if action == "update_user" and method in ("PUT", "PATCH"):
        return UpdateUserRequest       # 修改用户名
    return None                        # GET 查询接口：通过 URL query params，无请求体
