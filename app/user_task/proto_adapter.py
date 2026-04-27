"""
proto_adapter.py  —  用户任务模块 Protobuf 适配层

职责：
    1. 响应方向（Renderer 侧）：
       将视图返回的 Python dict 转换为强类型 proto 消息
       （UserTaskResponse 或 UserTaskListResponse）。
       入口：get_task_builder(action, method) -> builder 函数

    2. 请求方向（Parser 侧）：
       根据 action + method 返回对应的 proto 请求消息类。
       入口：get_task_request_message_class(action, method) -> 消息类

接口覆盖：
    POST     /api/models/createUserTask/         create_user_task
    PUT/PATCH /api/models/updateUserTask/        update_user_task
    GET      /api/models/dirUserTask/            dir_user_task
    GET      /api/models/dirUserTaskListByUser/  dir_user_task_list_by_user
"""

from app.proto.user_task_pb2 import (
    UserTaskResponse,
    UserTaskListResponse,
    UserTaskInfo,
    CreateUserTaskRequest,
    UpdateUserTaskRequest,
)
from app.proto.common_pb2 import ValidationError


# =============================================================================
# 内部工具函数
# =============================================================================

def _fill_user_task_info(dst: UserTaskInfo, src: dict) -> None:
    """将 dict 中的任务字段写入 proto UserTaskInfo 消息对象。"""
    if not isinstance(src, dict):
        return
    dst.user_task_id = int(src.get("user_task_id") or 0)
    dst.user_id      = int(src.get("user_id") or 0)
    dst.task_name    = str(src.get("task_name") or "")


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

def build_task_response(payload: dict) -> UserTaskResponse:
    """构建创建任务 / 修改任务 / 查询单个任务的 proto 响应消息。

    对应接口：
        POST      /api/models/createUserTask/
        PUT/PATCH /api/models/updateUserTask/
        GET       /api/models/dirUserTask/
    """
    msg = UserTaskResponse()
    msg.result  = str(payload.get("result", "success"))
    msg.success = bool(payload.get("success", True))
    _set_message_content(msg, payload.get("message"))

    data = payload.get("data")
    if isinstance(data, dict):
        _fill_user_task_info(msg.data, data)
    return msg


def build_task_list_response(payload: dict) -> UserTaskListResponse:
    """构建查询当前用户任务列表的 proto 响应消息。

    对应接口：GET /api/models/dirUserTaskListByUser/
    data 为列表，每个元素映射为一个 UserTaskInfo。
    """
    msg = UserTaskListResponse()
    msg.result  = str(payload.get("result", "success"))
    msg.success = bool(payload.get("success", True))
    _set_message_content(msg, payload.get("message"))

    data = payload.get("data")
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                info = msg.data.add()
                _fill_user_task_info(info, item)
    return msg


# =============================================================================
# 响应方向：Builder 分发函数（供 registry 调用）
# =============================================================================

def get_task_builder(action: str, method: str):
    """根据 DRF action + HTTP method 返回对应的响应 builder 函数。

    映射规则：
        create_user_task            + POST      -> build_task_response
        update_user_task            + PUT/PATCH -> build_task_response
        dir_user_task               + GET       -> build_task_response
        dir_user_task_list_by_user  + GET       -> build_task_list_response
    """
    if action in ("create_user_task", "update_user_task", "dir_user_task"):
        return build_task_response
    if action == "dir_user_task_list_by_user":
        return build_task_list_response
    return None


# =============================================================================
# 请求方向：消息类分发函数（供 registry 调用）
# =============================================================================

def get_task_request_message_class(action: str, method: str):
    """根据 DRF action + HTTP method 返回对应的 proto 请求消息类。

    映射规则：
        create_user_task + POST      -> CreateUserTaskRequest
        update_user_task + PUT/PATCH -> UpdateUserTaskRequest
        dir_*            + GET       -> None（URL Query String 传参，无请求体）
    """
    method = (method or "").upper()
    if action == "create_user_task" and method == "POST":
        return CreateUserTaskRequest
    if action == "update_user_task" and method in ("PUT", "PATCH"):
        return UpdateUserTaskRequest
    return None
