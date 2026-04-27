"""
proto_adapter.py  —  成就模块 Protobuf 适配层

职责：
    1. 响应方向（Renderer 侧）：
       将视图返回的 Python dict 转换为 AchievementResponse 强类型 proto 消息。
       入口：get_achievement_builder(action, method) -> builder 函数

    2. 请求方向（Parser 侧）：
       根据 action + method 返回对应的 proto 请求消息类。
       入口：get_achievement_request_message_class(action, method) -> 消息类

接口覆盖：
    POST /api/achievement/createAchievement/   create_achievement
    PUT  /api/achievement/updateAchievement/   update_achievement
    GET  /api/achievement/dirAchievement/      dir_achievement
"""

from app.proto.achievement_pb2 import (
    AchievementResponse, AchievementInfo,
    CreateAchievementRequest, UpdateAchievementRequest,
)


# =============================================================================
# 内部工具函数
# =============================================================================

def _fill_achievement_info(dst: AchievementInfo, src: dict) -> None:
    """将 dict 中的成就字段写入 proto AchievementInfo 消息对象。"""
    if not isinstance(src, dict):
        return
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

def build_achievement_response(payload: dict) -> AchievementResponse:
    """构建创建 / 修改 / 查询成就接口的 proto 响应消息。"""
    msg = AchievementResponse()
    msg.result  = str(payload.get("result", "success"))
    msg.success = bool(payload.get("success", True))
    _set_message_content(msg, payload.get("message"))

    data = payload.get("data")
    if isinstance(data, dict):
        _fill_achievement_info(msg.data, data)
    return msg


# =============================================================================
# 响应方向：Builder 分发函数（供 registry 调用）
# =============================================================================

def get_achievement_builder(action: str, method: str):
    """根据 DRF action + HTTP method 返回对应的响应 builder 函数。

    映射规则：
        create_achievement + POST      -> build_achievement_response
        update_achievement + PUT|PATCH -> build_achievement_response
        dir_achievement    + GET       -> build_achievement_response
    """
    if action in ("create_achievement", "update_achievement", "dir_achievement"):
        return build_achievement_response
    return None


# =============================================================================
# 请求方向：消息类分发函数（供 registry 调用）
# =============================================================================

def get_achievement_request_message_class(action: str, method: str):
    """根据 DRF action + HTTP method 返回对应的 proto 请求消息类。

    映射规则：
        create_achievement + POST      -> CreateAchievementRequest
        update_achievement + PUT|PATCH -> UpdateAchievementRequest
        dir_achievement    + GET       -> None（URL Query String 传参，无请求体）
    """
    method = (method or "").upper()
    if action == "create_achievement" and method == "POST":
        return CreateAchievementRequest
    if action == "update_achievement" and method in ("PUT", "PATCH"):
        return UpdateAchievementRequest
    return None
