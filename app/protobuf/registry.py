"""
registry.py  —  Protobuf 消息注册表

职责：
    作为 ProtobufRenderer（响应序列化）和 ProtobufParser（请求反序列化）的统一调度中心，
    根据"视图类 + action + HTTP method"三元组，查找对应的 proto 消息 builder 或消息类。

设计原则：
    1. 使用视图类引用（type(view)）而非类名字符串进行匹配。
       原因：字符串匹配在视图类重命名时会静默失效（既无报错也无 fallback 提示），
             而类引用在重命名后会在导入时即刻抛出 ImportError，问题更易发现。

    2. 所有导入均为懒加载（函数内 import），不在模块顶层执行。
       原因：Django 启动时会导入 settings.py 中注册的 renderer/parser 类，
             若此时 registry 已导入 views.py，可能引发循环导入（views → serializers
             → models → apps → settings → renderer → registry → views）。
             懒加载将导入推迟到第一次实际请求时，绕过循环导入问题。

    3. 两张注册表分开维护（_response_registry / _request_registry），
       各自只关心自己方向的映射，职责清晰，扩展新模块时互不干扰。

扩展方式（以新模块 xxx 为例）：
    # 1. 在 app/proto/ 中新建 xxx.proto 并编译生成 xxx_pb2.py
    # 2. 在 app/xxx/ 中新建 proto_adapter.py，实现 builder 和消息类解析函数
    # 3. 在下方两个注册表函数中各添加对应条目
"""


def _response_registry() -> dict:
    """构建并返回"响应方向"的注册表。

    格式：{ ViewClass: builder_factory }
    builder_factory 签名：(action: str, method: str) -> Callable[[dict], Message] | None
    """
    from app.user.views import UserViewSet
    from app.user.proto_adapter import get_user_builder

    from app.pet_action.views import PetActionViewSet
    from app.pet_action.proto_adapter import get_action_builder

    from app.pet_model.views import PetModelViewSet
    from app.pet_model.proto_adapter import get_model_builder

    from app.user_task.views import UserTaskViewSet
    from app.user_task.proto_adapter import get_task_builder

    from app.user_task_action_relation.views import UserTaskActionRelationViewSet
    from app.user_task_action_relation.proto_adapter import get_relation_builder

    from app.wealth.views import WealthViewSet
    from app.wealth.proto_adapter import get_wealth_builder

    from app.user_wealth_relation.views import UserWealthRelationViewSet
    from app.user_wealth_relation.proto_adapter import get_wealth_relation_builder

    from app.playtask.views import PlaytaskViewSet
    from app.playtask.proto_adapter import get_playtask_builder

    from app.user_playtask_relation.views import UserPlaytaskRelationViewSet
    from app.user_playtask_relation.proto_adapter import get_playtask_relation_builder

    from app.achievement.views import AchievementViewSet
    from app.achievement.proto_adapter import get_achievement_builder

    from app.user_achievement_relation.views import UserAchievementRelationViewSet
    from app.user_achievement_relation.proto_adapter import get_achievement_relation_builder

    from app.furniture.views import FurnitureViewSet
    from app.furniture.proto_adapter import get_furniture_builder

    from app.user_furniture_relation.views import UserFurnitureRelationViewSet
    from app.user_furniture_relation.proto_adapter import get_furniture_relation_builder

    from app.property.views import PropertyViewSet
    from app.property.proto_adapter import get_property_builder

    from app.user_property_relation.views import UserPropertyRelationViewSet
    from app.user_property_relation.proto_adapter import get_property_relation_builder

    return {
        UserViewSet:                      get_user_builder,
        PetActionViewSet:                 get_action_builder,
        PetModelViewSet:                  get_model_builder,
        UserTaskViewSet:                  get_task_builder,
        UserTaskActionRelationViewSet:    get_relation_builder,
        WealthViewSet:                    get_wealth_builder,
        UserWealthRelationViewSet:        get_wealth_relation_builder,
        PlaytaskViewSet:                  get_playtask_builder,
        UserPlaytaskRelationViewSet:      get_playtask_relation_builder,
        AchievementViewSet:               get_achievement_builder,
        UserAchievementRelationViewSet:   get_achievement_relation_builder,
        FurnitureViewSet:                 get_furniture_builder,
        UserFurnitureRelationViewSet:     get_furniture_relation_builder,
        PropertyViewSet:                  get_property_builder,
        UserPropertyRelationViewSet:      get_property_relation_builder,
    }


def _request_registry() -> dict:
    """构建并返回"请求方向"的注册表。

    格式：{ ViewClass: message_class_factory }
    message_class_factory 签名：(action: str, method: str) -> type[Message] | None
    """
    from app.user.views import UserViewSet
    from app.user.proto_adapter import get_user_request_message_class

    from app.pet_action.views import PetActionViewSet
    from app.pet_action.proto_adapter import get_action_request_message_class

    from app.pet_model.views import PetModelViewSet
    from app.pet_model.proto_adapter import get_model_request_message_class

    from app.user_task.views import UserTaskViewSet
    from app.user_task.proto_adapter import get_task_request_message_class

    from app.user_task_action_relation.views import UserTaskActionRelationViewSet
    from app.user_task_action_relation.proto_adapter import get_relation_request_message_class

    from app.wealth.views import WealthViewSet
    from app.wealth.proto_adapter import get_wealth_request_message_class

    from app.user_wealth_relation.views import UserWealthRelationViewSet
    from app.user_wealth_relation.proto_adapter import get_wealth_relation_request_message_class

    from app.playtask.views import PlaytaskViewSet
    from app.playtask.proto_adapter import get_playtask_request_message_class

    from app.user_playtask_relation.views import UserPlaytaskRelationViewSet
    from app.user_playtask_relation.proto_adapter import get_playtask_relation_request_message_class

    from app.achievement.views import AchievementViewSet
    from app.achievement.proto_adapter import get_achievement_request_message_class

    from app.user_achievement_relation.views import UserAchievementRelationViewSet
    from app.user_achievement_relation.proto_adapter import get_achievement_relation_request_message_class

    from app.furniture.views import FurnitureViewSet
    from app.furniture.proto_adapter import get_furniture_request_message_class

    from app.user_furniture_relation.views import UserFurnitureRelationViewSet
    from app.user_furniture_relation.proto_adapter import get_furniture_relation_request_message_class

    from app.property.views import PropertyViewSet
    from app.property.proto_adapter import get_property_request_message_class

    from app.user_property_relation.views import UserPropertyRelationViewSet
    from app.user_property_relation.proto_adapter import get_property_relation_request_message_class

    return {
        UserViewSet:                      get_user_request_message_class,
        PetActionViewSet:                 get_action_request_message_class,
        PetModelViewSet:                  get_model_request_message_class,
        UserTaskViewSet:                  get_task_request_message_class,
        UserTaskActionRelationViewSet:    get_relation_request_message_class,
        WealthViewSet:                    get_wealth_request_message_class,
        UserWealthRelationViewSet:        get_wealth_relation_request_message_class,
        PlaytaskViewSet:                  get_playtask_request_message_class,
        UserPlaytaskRelationViewSet:      get_playtask_relation_request_message_class,
        AchievementViewSet:              get_achievement_request_message_class,
        UserAchievementRelationViewSet:  get_achievement_relation_request_message_class,
        FurnitureViewSet:                get_furniture_request_message_class,
        UserFurnitureRelationViewSet:    get_furniture_relation_request_message_class,
        PropertyViewSet:                 get_property_request_message_class,
        UserPropertyRelationViewSet:     get_property_relation_request_message_class,
    }


def get_builder(view, action: str, method: str):
    """查找响应方向的 proto builder 函数。

    由 ProtobufRenderer 调用，用于将 Django 视图返回的 dict 序列化为 protobuf 二进制。

    参数：
        view   : 当前视图实例（ViewSet），取其 class 作为注册表 key
        action : DRF router action 名称（如 "create_action"、"dir_user"）
        method : HTTP 方法字符串（如 "POST"、"GET"、"PUT"）
    返回：
        Callable[[dict], protobuf.Message]  —— 找到匹配时
        None                                —— 无匹配（回退到通用 ApiEnvelope）
    """
    if not view or not action:
        return None
    factory = _response_registry().get(type(view))
    if factory:
        return factory(action, method)
    return None


def get_request_message_class(view, action: str, method: str):
    """查找请求方向的 proto 消息类。

    由 ProtobufParser 调用，用于将客户端发来的 protobuf 二进制反序列化为 dict。

    参数：
        view   : 当前视图实例（ViewSet），取其 class 作为注册表 key
        action : DRF router action 名称
        method : HTTP 方法字符串
    返回：
        type[protobuf.Message]  —— 找到匹配时（如 CreateActionRequest 类本身）
        None                    —— 无匹配（parser 返回空 dict，交由 Serializer 校验）
    """
    if not view or not action:
        return None
    factory = _request_registry().get(type(view))
    if factory:
        return factory(action, method)
    return None
