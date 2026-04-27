"""
proto_adapter.py  —  属性模块 Protobuf 适配层

职责：
    1. 响应方向（Renderer 侧）：
       将视图返回的 Python dict 转换为 PropertyResponse 强类型 proto 消息。
       入口：get_property_builder(action, method) -> builder 函数

    2. 请求方向（Parser 侧）：
       根据 action + method 返回对应的 proto 请求消息类。
       入口：get_property_request_message_class(action, method) -> 消息类

接口覆盖：
    POST /api/property/createProperty/   create_property
    PUT  /api/property/updateProperty/   update_property
    GET  /api/property/dirProperty/      dir_property
"""

from app.proto.property_pb2 import (
    PropertyResponse, PropertyInfo,
    CreatePropertyRequest, UpdatePropertyRequest,
)


# =============================================================================
# 内部工具函数
# =============================================================================

def _fill_property_info(dst: PropertyInfo, src: dict) -> None:
    """将 dict 中的属性字段写入 proto PropertyInfo 消息对象。"""
    if not isinstance(src, dict):
        return
    dst.property_id   = int(src.get("property_id") or 0)
    dst.property_name = str(src.get("property_name") or "")


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

def build_property_response(payload: dict) -> PropertyResponse:
    """构建创建 / 修改 / 查询属性接口的 proto 响应消息。"""
    msg = PropertyResponse()
    msg.result  = str(payload.get("result", "success"))
    msg.success = bool(payload.get("success", True))
    _set_message_content(msg, payload.get("message"))

    data = payload.get("data")
    if isinstance(data, dict):
        _fill_property_info(msg.data, data)
    return msg


# =============================================================================
# 响应方向：Builder 分发函数（供 registry 调用）
# =============================================================================

def get_property_builder(action: str, method: str):
    """根据 DRF action + HTTP method 返回对应的响应 builder 函数。

    映射规则：
        create_property + POST      -> build_property_response
        update_property + PUT|PATCH -> build_property_response
        dir_property    + GET       -> build_property_response
    """
    if action in ("create_property", "update_property", "dir_property"):
        return build_property_response
    return None


# =============================================================================
# 请求方向：消息类分发函数（供 registry 调用）
# =============================================================================

def get_property_request_message_class(action: str, method: str):
    """根据 DRF action + HTTP method 返回对应的 proto 请求消息类。

    映射规则：
        create_property + POST      -> CreatePropertyRequest
        update_property + PUT|PATCH -> UpdatePropertyRequest
        dir_property    + GET       -> None（URL Query String 传参，无请求体）
    """
    method = (method or "").upper()
    if action == "create_property" and method == "POST":
        return CreatePropertyRequest
    if action == "update_property" and method in ("PUT", "PATCH"):
        return UpdatePropertyRequest
    return None
