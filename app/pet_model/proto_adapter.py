"""
proto_adapter.py  —  宠物模型模块 Protobuf 适配层

职责：
    1. 响应方向（Renderer 侧）：
       将视图返回的 Python dict 转换为 PetModelResponse 强类型 proto 消息。
       入口：get_model_builder(action, method) -> builder 函数

    2. 请求方向（Parser 侧）：
       根据 action + method 返回对应的 proto 请求消息类。
       入口：get_model_request_message_class(action, method) -> 消息类

接口覆盖：
    POST /api/pet-models/createModel/   create_model
    GET  /api/pet-models/dirModel/      dir_model
"""

from app.proto.pet_model_pb2 import PetModelResponse, PetModelInfo, CreateModelRequest
from app.proto.common_pb2 import ValidationError


# =============================================================================
# 内部工具函数
# =============================================================================

def _fill_pet_model_info(dst: PetModelInfo, src: dict) -> None:
    """将 dict 中的模型字段写入 proto PetModelInfo 消息对象。"""
    if not isinstance(src, dict):
        return
    dst.pet_model_id   = int(src.get("pet_model_id") or 0)
    dst.pet_model_name = str(src.get("pet_model_name") or "")


def _set_message_content(msg, raw) -> None:
    """填充响应消息的 oneof message_content 字段。

    规则：
        str  -> msg.text = raw
        dict -> msg.error（DRF 字段级校验错误）
        None/其他 -> msg.text = ""
    """
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

def build_model_response(payload: dict) -> PetModelResponse:
    """构建创建模型 / 查询模型接口的 proto 响应消息。

    对应接口：
        POST /api/pet-models/createModel/
        GET  /api/pet-models/dirModel/
    """
    msg = PetModelResponse()
    msg.result  = str(payload.get("result", "success"))
    msg.success = bool(payload.get("success", True))
    _set_message_content(msg, payload.get("message"))

    data = payload.get("data")
    if isinstance(data, dict):
        _fill_pet_model_info(msg.data, data)
    return msg


# =============================================================================
# 响应方向：Builder 分发函数（供 registry 调用）
# =============================================================================

def get_model_builder(action: str, method: str):
    """根据 DRF action + HTTP method 返回对应的响应 builder 函数。

    映射规则：
        create_model + POST -> build_model_response
        dir_model    + GET  -> build_model_response
    """
    if action in ("create_model", "dir_model"):
        return build_model_response
    return None


# =============================================================================
# 请求方向：消息类分发函数（供 registry 调用）
# =============================================================================

def get_model_request_message_class(action: str, method: str):
    """根据 DRF action + HTTP method 返回对应的 proto 请求消息类。

    映射规则：
        create_model + POST -> CreateModelRequest
        dir_model    + GET  -> None（URL Query String 传参，无请求体）
    """
    method = (method or "").upper()
    if action == "create_model" and method == "POST":
        return CreateModelRequest
    return None
