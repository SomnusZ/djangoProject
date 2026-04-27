"""
proto_adapter.py  —  任务动作关联模块 Protobuf 适配层

职责：
    1. 响应方向（Renderer 侧）：
       将视图返回的 Python dict 转换为强类型 proto 消息
       （BindResponse / UnbindResponse / ActionListResponse）。
       入口：get_relation_builder(action, method) -> builder 函数

    2. 请求方向（Parser 侧）：
       根据 action + method 返回对应的 proto 请求消息类。
       入口：get_relation_request_message_class(action, method) -> 消息类

接口覆盖：
    POST /api/task-actions/bindActionToTask/      bind_action_to_task
    POST /api/task-actions/unbindActionFromTask/  unbind_action_from_task
    GET  /api/task-actions/dirActionListByTask/   dir_action_list_by_task
"""

from app.proto.user_task_action_relation_pb2 import (
    BindResponse,
    UnbindResponse,
    ActionListResponse,
    RelationInfo,
    UnbindInfo,
    ActionBriefInfo,
    BindActionRequest,
    UnbindActionRequest,
)
from app.proto.common_pb2 import ValidationError


# =============================================================================
# 内部工具函数
# =============================================================================

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

def build_bind_response(payload: dict) -> BindResponse:
    """构建绑定动作到任务接口的 proto 响应消息。

    对应接口：POST /api/task-actions/bindActionToTask/
    data 结构：{ "relation_id": 1, "user_task_id": 1, "pet_action_id": 2 }
    """
    msg = BindResponse()
    msg.result  = str(payload.get("result", "success"))
    msg.success = bool(payload.get("success", True))
    _set_message_content(msg, payload.get("message"))

    data = payload.get("data")
    if isinstance(data, dict):
        msg.data.relation_id   = int(data.get("relation_id") or 0)
        msg.data.user_task_id  = int(data.get("user_task_id") or 0)
        msg.data.pet_action_id = int(data.get("pet_action_id") or 0)
    return msg


def build_unbind_response(payload: dict) -> UnbindResponse:
    """构建解绑动作与任务接口的 proto 响应消息。

    对应接口：POST /api/task-actions/unbindActionFromTask/
    data 结构：{ "user_task_id": 1, "pet_action_id": 2 }（无 relation_id，记录已删除）
    """
    msg = UnbindResponse()
    msg.result  = str(payload.get("result", "success"))
    msg.success = bool(payload.get("success", True))
    _set_message_content(msg, payload.get("message"))

    data = payload.get("data")
    if isinstance(data, dict):
        msg.data.user_task_id  = int(data.get("user_task_id") or 0)
        msg.data.pet_action_id = int(data.get("pet_action_id") or 0)
    return msg


def build_action_list_response(payload: dict) -> ActionListResponse:
    """构建查询任务关联动作列表接口的 proto 响应消息。

    对应接口：GET /api/task-actions/dirActionListByTask/
    data 结构：[{ "pet_action_id": 1, "pet_action_name": "sit" }, ...]
    """
    msg = ActionListResponse()
    msg.result  = str(payload.get("result", "success"))
    msg.success = bool(payload.get("success", True))
    _set_message_content(msg, payload.get("message"))

    data = payload.get("data")
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                brief = msg.data.add()
                brief.pet_action_id   = int(item.get("pet_action_id") or 0)
                brief.pet_action_name = str(item.get("pet_action_name") or "")
    return msg


# =============================================================================
# 响应方向：Builder 分发函数（供 registry 调用）
# =============================================================================

def get_relation_builder(action: str, method: str):
    """根据 DRF action + HTTP method 返回对应的响应 builder 函数。

    映射规则：
        bind_action_to_task     + POST -> build_bind_response
        unbind_action_from_task + POST -> build_unbind_response
        dir_action_list_by_task + GET  -> build_action_list_response
    """
    if action == "bind_action_to_task":
        return build_bind_response
    if action == "unbind_action_from_task":
        return build_unbind_response
    if action == "dir_action_list_by_task":
        return build_action_list_response
    return None


# =============================================================================
# 请求方向：消息类分发函数（供 registry 调用）
# =============================================================================

def get_relation_request_message_class(action: str, method: str):
    """根据 DRF action + HTTP method 返回对应的 proto 请求消息类。

    映射规则：
        bind_action_to_task     + POST -> BindActionRequest
        unbind_action_from_task + POST -> UnbindActionRequest
        dir_action_list_by_task + GET  -> None（URL Query String 传参，无请求体）
    """
    method = (method or "").upper()
    if action == "bind_action_to_task" and method == "POST":
        return BindActionRequest
    if action == "unbind_action_from_task" and method == "POST":
        return UnbindActionRequest
    return None
