"""
proto_adapter.py  —  玩法任务模块 Protobuf 适配层

职责：
    1. 响应方向（Renderer 侧）：
       将视图返回的 Python dict 转换为 PlaytaskResponse 强类型 proto 消息。
       入口：get_playtask_builder(action, method) -> builder 函数

    2. 请求方向（Parser 侧）：
       根据 action + method 返回对应的 proto 请求消息类。
       入口：get_playtask_request_message_class(action, method) -> 消息类

接口覆盖：
    POST   /api/playtask/createPlaytask/   create_playtask
    PUT    /api/playtask/updatePlaytask/   update_playtask
    GET    /api/playtask/dirPlaytask/      dir_playtask
"""

from app.proto.playtask_pb2 import PlaytaskResponse, PlaytaskInfo, CreatePlaytaskRequest, UpdatePlaytaskRequest


# =============================================================================
# 内部工具函数
# =============================================================================

def _fill_playtask_info(dst: PlaytaskInfo, src: dict) -> None:
    """将 dict 中的玩法任务字段写入 proto PlaytaskInfo 消息对象。"""
    if not isinstance(src, dict):
        return
    dst.playtask_id   = int(src.get("playtask_id") or 0)
    dst.playtask_name = str(src.get("playtask_name") or "")


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

def build_playtask_response(payload: dict) -> PlaytaskResponse:
    """构建创建 / 修改 / 查询玩法任务接口的 proto 响应消息。"""
    msg = PlaytaskResponse()
    msg.result  = str(payload.get("result", "success"))
    msg.success = bool(payload.get("success", True))
    _set_message_content(msg, payload.get("message"))

    data = payload.get("data")
    if isinstance(data, dict):
        _fill_playtask_info(msg.data, data)
    return msg


# =============================================================================
# 响应方向：Builder 分发函数（供 registry 调用）
# =============================================================================

def get_playtask_builder(action: str, method: str):
    """根据 DRF action + HTTP method 返回对应的响应 builder 函数。

    映射规则：
        create_playtask + POST      -> build_playtask_response
        update_playtask + PUT|PATCH -> build_playtask_response
        dir_playtask    + GET       -> build_playtask_response
    """
    if action in ("create_playtask", "update_playtask", "dir_playtask"):
        return build_playtask_response
    return None


# =============================================================================
# 请求方向：消息类分发函数（供 registry 调用）
# =============================================================================

def get_playtask_request_message_class(action: str, method: str):
    """根据 DRF action + HTTP method 返回对应的 proto 请求消息类。

    映射规则：
        create_playtask + POST      -> CreatePlaytaskRequest
        update_playtask + PUT|PATCH -> UpdatePlaytaskRequest
        dir_playtask    + GET       -> None（URL Query String 传参，无请求体）
    """
    method = (method or "").upper()
    if action == "create_playtask" and method == "POST":
        return CreatePlaytaskRequest
    if action == "update_playtask" and method in ("PUT", "PATCH"):
        return UpdatePlaytaskRequest
    return None
