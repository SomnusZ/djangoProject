"""
renderer.py  —  Protobuf 响应渲染器（DRF Renderer）

职责：
    接管 DRF 的内容协商流程，当客户端请求头包含
    Accept: application/x-protobuf 时，将视图返回的 dict 序列化为 protobuf 二进制。
    JSON 路径（Accept: application/json 或缺省）完全不受影响。

工作流程：
    1. DRF 内容协商检测到 Accept: application/x-protobuf。
    2. 调用 ProtobufRenderer.render(data, ...)。
    3. 尝试通过 registry 查找该视图的强类型 builder（_build_typed_message）：
       - 找到 builder → 调用 builder(data) 得到强类型 proto 消息 → SerializeToString()
       - 未找到      → 回退通用 ApiEnvelope，将 data/message 包装为 Value 类型
    4. 返回二进制字节，DRF 作为 HTTP 响应体输出。

两级渲染策略：
    强类型（typed）：
        当前仅 user 模块已定义专属 proto 消息（UserResponse / UserLoginResponse），
        能精确表达字段类型，客户端反序列化后可直接使用强类型字段。
    通用兜底（generic fallback）：
        其他模块（pet_action / pet_model / user_task / user_task_action_relation）
        尚未定义专属消息，统一用 ApiEnvelope 包装。ApiEnvelope 使用
        google.protobuf.Value 作为 data / message 的类型，
        等效于"带类型标签的 JSON"，灵活但不够精确。

懒加载说明：
    _get_proto_runtime() 将 protobuf 相关导入推迟到第一次实际请求时执行。
    原因：Django 启动时会注册 renderer 类，若此时 protobuf 未安装，
    不应导致整个服务启动失败（JSON 接口仍可正常使用）。
    只有当客户端真正发起 protobuf 请求时，才触发 protobuf 导入，
    若此时依赖缺失则抛出明确的 RuntimeError 而非隐晦的 ImportError。
"""

import json

from rest_framework.renderers import BaseRenderer


class ProtobufRenderer(BaseRenderer):
    """将 DRF 响应 dict 渲染为 protobuf 二进制。

    通过 DRF 内容协商机制按需启用：
        Accept: application/json        -> JSONRenderer（默认，保持不变）
        Accept: application/x-protobuf -> ProtobufRenderer（本类）
    """

    # DRF 内容协商使用此 MIME 类型与请求头 Accept 匹配。
    media_type = 'application/x-protobuf'

    # DRF format 参数：允许通过 ?format=protobuf 显式指定格式（可选）。
    format = 'protobuf'

    # protobuf 是纯二进制格式，无字符集概念。
    # 设为 None 让 DRF 在 Content-Type 响应头中省略 charset 参数。
    charset = None

    # 提示 DRF Browsable API：此渲染器输出二进制，不应尝试用 HTML 展示。
    render_style = 'binary'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """将 DRF 视图返回的 data dict 转换为 protobuf 二进制字节。

        参数：
            data               : 视图通过 Response(data) 传入的 Python dict，
                                 通常由 success_response / error_response 生成，
                                 结构为 {result, success, data, message}。
            accepted_media_type: 已协商的 MIME 类型（本渲染器下固定为 application/x-protobuf）
            renderer_context   : DRF 上下文，包含 view / request / response 等，
                                 用于查找当前视图对应的强类型 builder。
        返回：
            bytes —— protobuf 序列化后的二进制字节流，作为 HTTP 响应体输出。
        """
        if data is None:
            return b''

        # 第一步：尝试强类型渲染（user 模块等已定义专属 proto 消息的模块）。
        # 成功则直接返回，跳过通用 fallback。
        typed_msg = self._build_typed_message(data, renderer_context)
        if typed_msg is not None:
            return typed_msg.SerializeToString()

        # 第二步：通用 ApiEnvelope fallback（用于尚未定义专属消息的模块）。
        ApiEnvelope, json_format, Value = self._get_proto_runtime()
        envelope = ApiEnvelope()

        if isinstance(data, dict):
            # 按项目统一响应格式填充信封字段
            envelope.result = str(data.get('result', 'success'))
            envelope.success = bool(data.get('success', True))
            # data 和 message 使用动态 Value 类型，通过 JSON 中转支持任意结构
            envelope.data.CopyFrom(self._to_value(data.get('data'), json_format, Value))
            envelope.message.CopyFrom(self._to_value(data.get('message'), json_format, Value))
        else:
            # 防御性处理：视图返回了非 dict 类型（不符合统一响应规范），
            # 仍然输出合法的 protobuf，避免触发 500 错误。
            envelope.result = 'success'
            envelope.success = True
            envelope.data.CopyFrom(self._to_value(data, json_format, Value))
            envelope.message.CopyFrom(self._to_value('', json_format, Value))

        return envelope.SerializeToString()

    @staticmethod
    def _build_typed_message(data, renderer_context):
        """尝试用强类型 builder 构建 proto 消息。

        从 renderer_context 中提取 view + action + method，
        通过 registry 查找注册的 builder 函数，
        调用 builder(data) 得到 proto 消息对象。

        参数：
            data             : 响应 dict
            renderer_context : DRF 上下文
        返回：
            protobuf.Message 实例（找到强类型 builder 时）
            None（无匹配 builder 时，调用方回退到通用 ApiEnvelope）
        """
        if not isinstance(data, dict):
            return None
        if not renderer_context:
            return None

        view    = renderer_context.get('view')
        request = renderer_context.get('request')
        action  = getattr(view, 'action', None)     # DRF router 设置的 action 名称
        method  = getattr(request, 'method', '')    # HTTP 方法字符串

        try:
            from google.protobuf.message import Message
            from app.protobuf.registry import get_builder
        except Exception:
            # protobuf 未安装或 registry 导入失败：静默降级到通用 fallback
            return None

        builder = get_builder(view, action, method)
        if not builder:
            return None

        msg = builder(data)
        # 确保 builder 返回的确实是 proto 消息对象，防止 adapter 误返回其他类型
        if isinstance(msg, Message):
            return msg
        return None

    @staticmethod
    def _to_value(py_obj, json_format, Value):
        """将任意 Python 对象转换为 protobuf Value（动态类型）。

        转换路径：Python 对象 -> JSON 字符串 -> protobuf Value
        通过 JSON 作为中间格式，是因为 google.protobuf.json_format.Parse
        已经实现了 JSON → Value 的完整映射，无需手动处理每种类型。

        支持的类型：
            None      -> NullValue
            bool      -> BoolValue
            int/float -> NumberValue
            str       -> StringValue
            dict      -> StructValue（嵌套 key-value 对）
            list      -> ListValue（任意元素列表）

        参数：
            py_obj     : 待转换的 Python 对象
            json_format: google.protobuf.json_format 模块（由调用方传入避免重复导入）
            Value      : google.protobuf.struct_pb2.Value 类（同上）
        返回：
            google.protobuf.Value 实例
        """
        value = Value()
        try:
            # ensure_ascii=False 保留中文字符，避免转义为 \uXXXX
            json_format.Parse(json.dumps(py_obj, ensure_ascii=False), value)
        except TypeError:
            # py_obj 包含不可 JSON 序列化的对象（如 datetime、Decimal）时，
            # 降级为字符串表示，确保响应不因序列化失败而中断。
            json_format.Parse(json.dumps(str(py_obj), ensure_ascii=False), value)
        return value

    @staticmethod
    def _get_proto_runtime():
        """懒加载 protobuf 运行时依赖。

        为什么懒加载：
            Django 在启动时会扫描并注册所有 INSTALLED_APPS 中的 renderer 类。
            若在模块顶层 import protobuf，当 protobuf 未安装时会导致整个服务
            无法启动——即使客户端从未发起过 protobuf 请求。
            懒加载将导入推迟到第一次实际 protobuf 请求时，
            保证 JSON 接口在任何情况下都能正常响应。

        返回：
            (ApiEnvelope 类, json_format 模块, Value 类) 三元组
        抛出：
            RuntimeError —— protobuf 未安装时，给出明确的错误提示
        """
        try:
            from google.protobuf import json_format
            from google.protobuf.struct_pb2 import Value
            from app.proto.common_pb2 import ApiEnvelope
            return ApiEnvelope, json_format, Value
        except Exception as exc:
            raise RuntimeError(
                "Protobuf 运行时不可用。请在当前 Python 解释器中安装依赖：\n"
                "    pip install protobuf\n"
                "或检查 app/proto/common_pb2.py 是否已通过 protoc 编译生成。"
            ) from exc
