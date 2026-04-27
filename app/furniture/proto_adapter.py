"""
proto_adapter.py  —  家具模块 Protobuf 适配层

职责：
    1. 响应方向（Renderer 侧）：
       将视图返回的 Python dict 转换为 FurnitureResponse 强类型 proto 消息。
       入口：get_furniture_builder(action, method) -> builder 函数

    2. 请求方向（Parser 侧）：
       根据 action + method 返回对应的 proto 请求消息类。
       入口：get_furniture_request_message_class(action, method) -> 消息类

接口覆盖：
    POST /api/furniture/createFurniture/   create_furniture
    PUT  /api/furniture/updateFurniture/   update_furniture
    GET  /api/furniture/dirFurniture/      dir_furniture
"""

from app.proto.furniture_pb2 import (
    FurnitureResponse, FurnitureInfo,
    CreateFurnitureRequest, UpdateFurnitureRequest,
)


# =============================================================================
# 内部工具函数
# =============================================================================

def _fill_furniture_info(dst: FurnitureInfo, src: dict) -> None:
    """将 dict 中的家具字段写入 proto FurnitureInfo 消息对象。"""
    if not isinstance(src, dict):
        return
    dst.furniture_id   = int(src.get("furniture_id") or 0)
    dst.furniture_name = str(src.get("furniture_name") or "")


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

def build_furniture_response(payload: dict) -> FurnitureResponse:
    """构建创建 / 修改 / 查询家具接口的 proto 响应消息。"""
    msg = FurnitureResponse()
    msg.result  = str(payload.get("result", "success"))
    msg.success = bool(payload.get("success", True))
    _set_message_content(msg, payload.get("message"))

    data = payload.get("data")
    if isinstance(data, dict):
        _fill_furniture_info(msg.data, data)
    return msg


# =============================================================================
# 响应方向：Builder 分发函数（供 registry 调用）
# =============================================================================

def get_furniture_builder(action: str, method: str):
    """根据 DRF action + HTTP method 返回对应的响应 builder 函数。

    映射规则：
        create_furniture + POST      -> build_furniture_response
        update_furniture + PUT|PATCH -> build_furniture_response
        dir_furniture    + GET       -> build_furniture_response
    """
    if action in ("create_furniture", "update_furniture", "dir_furniture"):
        return build_furniture_response
    return None


# =============================================================================
# 请求方向：消息类分发函数（供 registry 调用）
# =============================================================================

def get_furniture_request_message_class(action: str, method: str):
    """根据 DRF action + HTTP method 返回对应的 proto 请求消息类。

    映射规则：
        create_furniture + POST      -> CreateFurnitureRequest
        update_furniture + PUT|PATCH -> UpdateFurnitureRequest
        dir_furniture    + GET       -> None（URL Query String 传参，无请求体）
    """
    method = (method or "").upper()
    if action == "create_furniture" and method == "POST":
        return CreateFurnitureRequest
    if action == "update_furniture" and method in ("PUT", "PATCH"):
        return UpdateFurnitureRequest
    return None
