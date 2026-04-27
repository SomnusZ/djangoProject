"""
parser.py  —  Protobuf 请求体解析器（DRF Parser）

职责：
    接受客户端发送的 Content-Type: application/x-protobuf 二进制请求体，
    将其反序列化为 Python dict，再交给 DRF 的 Serializer 进行字段校验。
    视图层（views.py）收到的 request.data 与 JSON 路径完全相同，无需任何修改。

工作流程：
    1. DRF 内容协商（content negotiation）检测到请求头 Content-Type: application/x-protobuf。
    2. 调用本解析器的 parse() 方法。
    3. 从 parser_context 中取出 view 实例、request 对象，
       得到 action（如 "create_user"）和 HTTP method（如 "POST"）。
    4. 通过 registry.get_request_message_class() 查找对应的 proto 消息类。
    5. 用该消息类反序列化请求体二进制数据（ParseFromString）。
    6. 用 MessageToDict 将 proto 消息转换为 Python dict（key 保持 snake_case）。
    7. 返回 dict，DRF 将其赋值给 request.data，后续流程与 JSON 请求完全一致。

注意事项：
    - GET 请求通过 URL Query String 传参，不使用请求体，get_request_message_class
      对 GET action 返回 None，parser 随之返回空 dict（query_params 另行处理）。
    - 若 registry 找不到对应消息类（例如其他模块尚未定义请求消息），
      同样返回空 dict，DRF Serializer 会因必填字段缺失而返回 400 错误，
      不会引发服务端 500，行为与 JSON 路径一致。
    - 若请求体字节损坏或格式错误，ParseFromString 抛异常时同样返回空 dict。
"""

from rest_framework.parsers import BaseParser


class ProtobufParser(BaseParser):
    """将 application/x-protobuf 二进制请求体解析为 Python dict。

    只负责格式转换，不做业务校验。
    业务校验由各接口对应的 DRF Serializer 承担，与 JSON 路径一致。
    """

    # DRF 通过此 MIME 类型判断是否调用本解析器。
    # 客户端需在请求头中携带：Content-Type: application/x-protobuf
    media_type = 'application/x-protobuf'

    def parse(self, stream, media_type=None, parser_context=None):
        """解析二进制请求体，返回 Python dict。

        参数：
            stream          : 原始请求体的字节流（由 DRF 传入）
            media_type      : 实际的 Content-Type 值（本解析器已通过 media_type 匹配）
            parser_context  : DRF 上下文，包含以下关键字段：
                                - 'view'    : 当前视图实例（ViewSet）
                                - 'request' : DRF Request 对象
                                - 'kwargs'  : URL 路由参数
        返回：
            dict —— 与 JSONParser 输出结构一致，交给 Serializer 继续处理。
            若无法解析（未注册消息类 / 字节损坏），返回空 dict {}。
        """
        ctx     = parser_context or {}
        view    = ctx.get('view')                                    # 视图实例，用于确定模块
        request = ctx.get('request')                                 # DRF Request，用于取 method
        action  = getattr(view, 'action', None)                      # DRF router action 名称
        method  = (getattr(request, 'method', '') or '').upper()     # HTTP 方法，如 "POST"

        # 根据视图类 + action + method 查找对应的 proto 请求消息类。
        # 若该 action 不需要请求体（如 GET）或尚未注册，返回 None。
        msg_class = self._resolve(view, action, method)
        if msg_class is None:
            return {}

        try:
            from google.protobuf.json_format import MessageToDict

            # 实例化消息对象，从二进制字节流反序列化。
            msg = msg_class()
            msg.ParseFromString(stream.read())

            # 转换为 Python dict：
            #   preserving_proto_field_name=True
            #     保留 proto 字段的 snake_case 命名（如 user_phone_number），
            #     与 DRF Serializer 的字段名保持一致；
            #     若为 False，protobuf 默认会转成 lowerCamelCase（如 userPhoneNumber）。
            #
            #   always_print_fields_with_no_presence=True
            #     将未赋值的字段也包含在 dict 中（值为类型默认值，如空字符串 ""）。
            #     这样 DRF Serializer 能看到所有字段并对必填字段触发"该字段不可为空"
            #     的校验错误，而不是"字段缺失"，行为与 JSON 请求体路径一致。
            #     注意：此参数在 protobuf 5.x 中由旧版 including_default_value_fields 更名而来。
            return MessageToDict(
                msg,
                preserving_proto_field_name=True,
                always_print_fields_with_no_presence=True,
            )
        except Exception:
            # 请求体字节损坏或与消息类定义不匹配时，
            # 静默返回空 dict，让 DRF Serializer 报 400，避免触发 500。
            return {}

    @staticmethod
    def _resolve(view, action, method):
        """通过 registry 查找当前请求对应的 proto 消息类。

        参数：
            view   : 视图实例（其类型用于在 registry 中定位模块）
            action : DRF action 名称（如 "create_user"、"dir_user"）
            method : HTTP 方法（如 "POST"、"PUT"）
        返回：
            proto 消息类（如 CreateUserRequest），或 None（无匹配时）。
        """
        if not view or not action:
            return None
        try:
            from app.protobuf.registry import get_request_message_class
            return get_request_message_class(view, action, method)
        except Exception:
            # protobuf 未安装或 registry 导入失败时，静默降级，
            # 不影响 JSON 路径的正常工作。
            return None
