"""
proto_adapter.py  —  货币资产模块 Protobuf 适配层

职责：
    1. 响应方向（Renderer 侧）：
       将视图返回的 Python dict 转换为 WealthResponse 强类型 proto 消息。
       入口：get_wealth_builder(action, method) -> builder 函数

    2. 请求方向（Parser 侧）：
       根据 action + method 返回对应的 proto 请求消息类。
       入口：get_wealth_request_message_class(action, method) -> 消息类

接口覆盖：
    POST   /api/wealth/createWealth/   create_wealth
    PUT    /api/wealth/updateWealth/   update_wealth
    GET    /api/wealth/dirWealth/      dir_wealth
"""

from app.proto.wealth_pb2 import WealthResponse, WealthInfo, CreateWealthRequest, UpdateWealthRequest


# =============================================================================
# 内部工具函数
# =============================================================================

def _fill_wealth_info(dst: WealthInfo, src: dict) -> None:
    """将 dict 中的货币资产字段写入 proto WealthInfo 消息对象。"""
    if not isinstance(src, dict):
        return
    dst.wealth_id   = int(src.get("wealth_id") or 0)
    dst.wealth_name = str(src.get("wealth_name") or "")


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

def build_wealth_response(payload: dict) -> WealthResponse:
    """构建创建 / 修改 / 查询货币资产接口的 proto 响应消息。

    对应接口：
        POST /api/wealth/createWealth/
        PUT  /api/wealth/updateWealth/
        GET  /api/wealth/dirWealth/
    """
    msg = WealthResponse()
    msg.result  = str(payload.get("result", "success"))
    msg.success = bool(payload.get("success", True))
    _set_message_content(msg, payload.get("message"))

    data = payload.get("data")
    if isinstance(data, dict):
        _fill_wealth_info(msg.data, data)
    return msg


# =============================================================================
# 响应方向：Builder 分发函数（供 registry 调用）
# =============================================================================

def get_wealth_builder(action: str, method: str):
    """根据 DRF action + HTTP method 返回对应的响应 builder 函数。

    映射规则：
        create_wealth + POST      -> build_wealth_response
        update_wealth + PUT|PATCH -> build_wealth_response
        dir_wealth    + GET       -> build_wealth_response
    """
    if action in ("create_wealth", "update_wealth", "dir_wealth"):
        return build_wealth_response
    return None


# =============================================================================
# 请求方向：消息类分发函数（供 registry 调用）
# =============================================================================

def get_wealth_request_message_class(action: str, method: str):
    """根据 DRF action + HTTP method 返回对应的 proto 请求消息类。

    映射规则：
        create_wealth + POST      -> CreateWealthRequest
        update_wealth + PUT|PATCH -> UpdateWealthRequest
        dir_wealth    + GET       -> None（URL Query String 传参，无请求体）
    """
    method = (method or "").upper()
    if action == "create_wealth" and method == "POST":
        return CreateWealthRequest
    if action == "update_wealth" and method in ("PUT", "PATCH"):
        return UpdateWealthRequest
    return None
