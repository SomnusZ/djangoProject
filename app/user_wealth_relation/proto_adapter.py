"""
proto_adapter.py  —  用户货币资产关联模块 Protobuf 适配层

职责：
    1. 响应方向（Renderer 侧）：
       将视图返回的 Python dict 转换为对应的强类型 proto 消息。
       入口：get_wealth_relation_builder(action, method) -> builder 函数

    2. 请求方向（Parser 侧）：
       根据 action + method 返回对应的 proto 请求消息类。
       入口：get_wealth_relation_request_message_class(action, method) -> 消息类

接口覆盖：
    POST /api/user-wealth/bindWealthToUser/      bind_wealth_to_user
    POST /api/user-wealth/unbindWealthFromUser/  unbind_wealth_from_user
    GET  /api/user-wealth/dirWealthListByUser/   dir_wealth_list_by_user
"""

from app.proto.user_wealth_relation_pb2 import (
    BindWealthResponse, UnbindWealthResponse, WealthRelationListResponse,
    WealthRelationInfo, WealthUnbindInfo,
    BindWealthRequest, UnbindWealthRequest,
)


# =============================================================================
# 内部工具函数
# =============================================================================

def _fill_relation_info(dst: WealthRelationInfo, src: dict) -> None:
    """将 dict 中的关联字段写入 proto WealthRelationInfo 消息对象。"""
    if not isinstance(src, dict):
        return
    dst.relation_id   = int(src.get("relation_id") or 0)
    dst.user_id       = int(src.get("user_id") or 0)
    dst.wealth_id     = int(src.get("wealth_id") or 0)
    dst.wealth_name   = str(src.get("wealth_name") or "")
    dst.wealth_amount = int(src.get("wealth_amount") or 0)


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

def build_bind_wealth_response(payload: dict) -> BindWealthResponse:
    """构建绑定货币资产到用户接口的 proto 响应消息。"""
    msg = BindWealthResponse()
    msg.result  = str(payload.get("result", "success"))
    msg.success = bool(payload.get("success", True))
    _set_message_content(msg, payload.get("message"))

    data = payload.get("data")
    if isinstance(data, dict):
        _fill_relation_info(msg.data, data)
    return msg


def build_unbind_wealth_response(payload: dict) -> UnbindWealthResponse:
    """构建解绑货币资产与用户接口的 proto 响应消息。"""
    msg = UnbindWealthResponse()
    msg.result  = str(payload.get("result", "success"))
    msg.success = bool(payload.get("success", True))
    _set_message_content(msg, payload.get("message"))

    data = payload.get("data")
    if isinstance(data, dict):
        msg.data.wealth_id = int(data.get("wealth_id") or 0)
    return msg


def build_wealth_relation_list_response(payload: dict) -> WealthRelationListResponse:
    """构建查询用户货币资产列表接口的 proto 响应消息。

    data 为 list，对应 repeated WealthRelationInfo。
    """
    msg = WealthRelationListResponse()
    msg.result  = str(payload.get("result", "success"))
    msg.success = bool(payload.get("success", True))
    _set_message_content(msg, payload.get("message"))

    data = payload.get("data")
    if isinstance(data, list):
        for item in data:
            _fill_relation_info(msg.data.add(), item)
    return msg


# =============================================================================
# 响应方向：Builder 分发函数（供 registry 调用）
# =============================================================================

def get_wealth_relation_builder(action: str, method: str):
    """根据 DRF action + HTTP method 返回对应的响应 builder 函数。

    映射规则：
        bind_wealth_to_user      -> build_bind_wealth_response
        unbind_wealth_from_user  -> build_unbind_wealth_response
        dir_wealth_list_by_user  -> build_wealth_relation_list_response
    """
    if action == "bind_wealth_to_user":
        return build_bind_wealth_response
    if action == "unbind_wealth_from_user":
        return build_unbind_wealth_response
    if action == "dir_wealth_list_by_user":
        return build_wealth_relation_list_response
    return None


# =============================================================================
# 请求方向：消息类分发函数（供 registry 调用）
# =============================================================================

def get_wealth_relation_request_message_class(action: str, method: str):
    """根据 DRF action + HTTP method 返回对应的 proto 请求消息类。

    映射规则：
        bind_wealth_to_user     + POST -> BindWealthRequest
        unbind_wealth_from_user + POST -> UnbindWealthRequest
        dir_wealth_list_by_user + GET  -> None（无请求体）
    """
    method = (method or "").upper()
    if action == "bind_wealth_to_user" and method == "POST":
        return BindWealthRequest
    if action == "unbind_wealth_from_user" and method == "POST":
        return UnbindWealthRequest
    return None
