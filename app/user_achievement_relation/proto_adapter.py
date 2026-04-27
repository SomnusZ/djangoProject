"""
proto_adapter.py  —  用户成就关联模块 Protobuf 适配层

职责：
    1. 响应方向（Renderer 侧）：
       将视图返回的 Python dict 转换为对应的强类型 proto 消息。
       入口：get_achievement_relation_builder(action, method) -> builder 函数

    2. 请求方向（Parser 侧）：
       根据 action + method 返回对应的 proto 请求消息类。
       入口：get_achievement_relation_request_message_class(action, method) -> 消息类

接口覆盖：
    POST /api/user-achievement/bindAchievementToUser/      bind_achievement_to_user
    POST /api/user-achievement/unbindAchievementFromUser/  unbind_achievement_from_user
    GET  /api/user-achievement/dirAchievementListByUser/   dir_achievement_list_by_user
"""

from app.proto.user_achievement_relation_pb2 import (
    BindAchievementResponse, UnbindAchievementResponse, AchievementRelationListResponse,
    AchievementRelationInfo, AchievementUnbindInfo,
    BindAchievementRequest, UnbindAchievementRequest,
)


# =============================================================================
# 内部工具函数
# =============================================================================

def _fill_achievement_relation_info(dst: AchievementRelationInfo, src: dict) -> None:
    """将 dict 中的关联字段写入 proto AchievementRelationInfo 消息对象。
    注意：成就无数量字段。
    """
    if not isinstance(src, dict):
        return
    dst.relation_id      = int(src.get("relation_id") or 0)
    dst.user_id          = int(src.get("user_id") or 0)
    dst.achievement_id   = int(src.get("achievement_id") or 0)
    dst.achievement_name = str(src.get("achievement_name") or "")


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

def build_bind_achievement_response(payload: dict) -> BindAchievementResponse:
    """构建解锁成就（绑定）接口的 proto 响应消息。"""
    msg = BindAchievementResponse()
    msg.result  = str(payload.get("result", "success"))
    msg.success = bool(payload.get("success", True))
    _set_message_content(msg, payload.get("message"))

    data = payload.get("data")
    if isinstance(data, dict):
        _fill_achievement_relation_info(msg.data, data)
    return msg


def build_unbind_achievement_response(payload: dict) -> UnbindAchievementResponse:
    """构建撤销成就（解绑）接口的 proto 响应消息。"""
    msg = UnbindAchievementResponse()
    msg.result  = str(payload.get("result", "success"))
    msg.success = bool(payload.get("success", True))
    _set_message_content(msg, payload.get("message"))

    data = payload.get("data")
    if isinstance(data, dict):
        msg.data.achievement_id = int(data.get("achievement_id") or 0)
    return msg


def build_achievement_relation_list_response(payload: dict) -> AchievementRelationListResponse:
    """构建查询用户已解锁成就列表接口的 proto 响应消息。

    data 为 list，对应 repeated AchievementRelationInfo。
    """
    msg = AchievementRelationListResponse()
    msg.result  = str(payload.get("result", "success"))
    msg.success = bool(payload.get("success", True))
    _set_message_content(msg, payload.get("message"))

    data = payload.get("data")
    if isinstance(data, list):
        for item in data:
            _fill_achievement_relation_info(msg.data.add(), item)
    return msg


# =============================================================================
# 响应方向：Builder 分发函数（供 registry 调用）
# =============================================================================

def get_achievement_relation_builder(action: str, method: str):
    """根据 DRF action + HTTP method 返回对应的响应 builder 函数。"""
    if action == "bind_achievement_to_user":
        return build_bind_achievement_response
    if action == "unbind_achievement_from_user":
        return build_unbind_achievement_response
    if action == "dir_achievement_list_by_user":
        return build_achievement_relation_list_response
    return None


# =============================================================================
# 请求方向：消息类分发函数（供 registry 调用）
# =============================================================================

def get_achievement_relation_request_message_class(action: str, method: str):
    """根据 DRF action + HTTP method 返回对应的 proto 请求消息类。"""
    method = (method or "").upper()
    if action == "bind_achievement_to_user" and method == "POST":
        return BindAchievementRequest
    if action == "unbind_achievement_from_user" and method == "POST":
        return UnbindAchievementRequest
    return None
