"""
proto_adapter.py  —  用户属性关联模块 Protobuf 适配层

职责：
    1. 响应方向（Renderer 侧）：
       将视图返回的 Python dict 转换为对应的强类型 proto 消息。
       入口：get_property_relation_builder(action, method) -> builder 函数

    2. 请求方向（Parser 侧）：
       根据 action + method 返回对应的 proto 请求消息类。
       入口：get_property_relation_request_message_class(action, method) -> 消息类

接口覆盖：
    POST /api/user-property/bindPropertyToUser/      bind_property_to_user
    POST /api/user-property/unbindPropertyFromUser/  unbind_property_from_user
    GET  /api/user-property/dirPropertyListByUser/   dir_property_list_by_user
"""

from app.proto.user_property_relation_pb2 import (
    BindPropertyResponse, UnbindPropertyResponse, PropertyRelationListResponse,
    PropertyRelationInfo, PropertyUnbindInfo,
    BindPropertyRequest, UnbindPropertyRequest,
)


# =============================================================================
# 内部工具函数
# =============================================================================

def _fill_property_relation_info(dst: PropertyRelationInfo, src: dict) -> None:
    """将 dict 中的关联字段写入 proto PropertyRelationInfo 消息对象。"""
    if not isinstance(src, dict):
        return
    dst.relation_id     = int(src.get("relation_id") or 0)
    dst.user_id         = int(src.get("user_id") or 0)
    dst.property_id     = int(src.get("property_id") or 0)
    dst.property_name   = str(src.get("property_name") or "")
    dst.property_amount = int(src.get("property_amount") or 0)


def _set_message_content(msg, raw) -> None:
    """填充响应消息的 oneof message_content 字段。"""
    if isinstance(raw, str):
        msg.text = raw
    elif isinstance(raw, dict):
        for field_name, errors in raw.items():
            lv = msg.error.fields[field_name]
            if isinstance(errors, list):
                for err in errors:
                    lv.values.add().string_value = str(err)
            else:
                lv.values.add().string_value = str(errors)
    else:
        msg.text = str(raw) if raw is not None else ""


# =============================================================================
# 响应方向：Builder 函数
# =============================================================================

def build_bind_property_response(payload: dict) -> BindPropertyResponse:
    """构建绑定属性到用户接口的 proto 响应消息。"""
    msg = BindPropertyResponse()
    msg.result  = str(payload.get("result", "success"))
    msg.success = bool(payload.get("success", True))
    _set_message_content(msg, payload.get("message"))

    data = payload.get("data")
    if isinstance(data, dict):
        _fill_property_relation_info(msg.data, data)
    return msg


def build_unbind_property_response(payload: dict) -> UnbindPropertyResponse:
    """构建解绑属性与用户接口的 proto 响应消息。"""
    msg = UnbindPropertyResponse()
    msg.result  = str(payload.get("result", "success"))
    msg.success = bool(payload.get("success", True))
    _set_message_content(msg, payload.get("message"))

    data = payload.get("data")
    if isinstance(data, dict):
        msg.data.property_id = int(data.get("property_id") or 0)
    return msg


def build_property_relation_list_response(payload: dict) -> PropertyRelationListResponse:
    """构建查询用户属性列表接口的 proto 响应消息。

    data 为 list，对应 repeated PropertyRelationInfo。
    """
    msg = PropertyRelationListResponse()
    msg.result  = str(payload.get("result", "success"))
    msg.success = bool(payload.get("success", True))
    _set_message_content(msg, payload.get("message"))

    data = payload.get("data")
    if isinstance(data, list):
        for item in data:
            _fill_property_relation_info(msg.data.add(), item)
    return msg


# =============================================================================
# 响应方向：Builder 分发函数（供 registry 调用）
# =============================================================================

def get_property_relation_builder(action: str, method: str):
    """根据 DRF action + HTTP method 返回对应的响应 builder 函数。"""
    if action == "bind_property_to_user":
        return build_bind_property_response
    if action == "unbind_property_from_user":
        return build_unbind_property_response
    if action == "dir_property_list_by_user":
        return build_property_relation_list_response
    return None


# =============================================================================
# 请求方向：消息类分发函数（供 registry 调用）
# =============================================================================

def get_property_relation_request_message_class(action: str, method: str):
    """根据 DRF action + HTTP method 返回对应的 proto 请求消息类。"""
    method = (method or "").upper()
    if action == "bind_property_to_user" and method == "POST":
        return BindPropertyRequest
    if action == "unbind_property_from_user" and method == "POST":
        return UnbindPropertyRequest
    return None
