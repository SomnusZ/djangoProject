"""
通用权限与归属校验工具。
包含：
- 自定义 JWT 认证（使用 app.user.User）
- 归属权限与封装方法
"""

from typing import Optional

from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.settings import api_settings

from app.user.models import User
from app.utils import error_response


class AppUserJWTAuthentication(JWTAuthentication):
    """
    使用自定义用户表（app.user.models.User）解析 JWT。
    """

    def get_user(self, validated_token):
        user_id = validated_token.get(api_settings.USER_ID_CLAIM)
        if user_id is None:
            raise AuthenticationFailed('Token 无效：未包含用户ID', code='token_no_user')

        try:
            return User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            raise AuthenticationFailed('用户不存在', code='user_not_found')


def get_owner_user(obj) -> Optional[User]:
    """
    获取对象所属用户。
    支持：
    - obj 是 User
    - obj.user
    - obj.pet_model.user
    - obj.user_task.user
    """
    if isinstance(obj, User):
        return obj
    if hasattr(obj, 'user'):
        return obj.user
    if hasattr(obj, 'pet_model') and hasattr(obj.pet_model, 'user'):
        return obj.pet_model.user
    if hasattr(obj, 'user_task') and hasattr(obj.user_task, 'user'):
        return obj.user_task.user
    return None


class IsAdminUser(BasePermission):
    """
    管理员权限：user_role >= 1 才允许访问。
    用于字典表管理类接口（创建 / 修改动作、成就、家具、道具等）。
    """

    message = '需要管理员权限'

    def has_permission(self, request, view):
        return bool(
            request.user
            and getattr(request.user, 'is_authenticated', False)
            and getattr(request.user, 'user_role', 0) >= 1
        )


class IsOwnerPermission(BasePermission):
    """
    统一归属权限：
    - 必须登录
    - 只能访问归属自己的数据
    """

    def has_permission(self, request, view):
        return bool(request.user and getattr(request.user, 'is_authenticated', True))

    def has_object_permission(self, request, view, obj):
        owner = get_owner_user(obj)
        if owner is None:
            return False
        return getattr(owner, 'user_id', None) == getattr(request.user, 'user_id', None)


def get_owned_object_or_403(request, queryset, not_found_msg='资源不存在', **filters):
    """
    统一获取 + 归属校验：
    - 不存在 -> 404
    - 非本人 -> 403
    - 成功 -> 返回对象
    """
    obj = queryset.filter(**filters).first()
    if not obj:
        return None, error_response(not_found_msg, status_code=404)

    owner = get_owner_user(obj)
    if owner is None or getattr(owner, 'user_id', None) != getattr(request.user, 'user_id', None):
        return None, error_response('无权限', status_code=403)

    return obj, None


class OwnedObjectMixin:
    """
    提供 get_owned_or_403 方法。
    """

    def get_owned_or_403(self, request, queryset, not_found_msg='资源不存在', **filters):
        return get_owned_object_or_403(request, queryset, not_found_msg=not_found_msg, **filters)


class OwnedQuerySetMixin:
    """
    统一归属过滤：
    - owner_field 指向“归属用户”的字段路径（支持 ORM 关系路径）
    - 默认过滤为当前登录用户的数据
    """

    owner_field = None  # 示例：'user' 或 'pet_model__user' 或 'self'

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user or not getattr(self.request.user, 'is_authenticated', True):
            return qs.none()
        if not self.owner_field:
            return qs
        if self.owner_field == 'self':
            return qs.filter(user_id=getattr(self.request.user, 'user_id', None))
        return qs.filter(**{self.owner_field: self.request.user})
