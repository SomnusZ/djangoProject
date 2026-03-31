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
    支持三种结构：
    - obj 是 User 实例
    - obj.user（直接关联用户）
    - obj.pet_model.user（通过 pet_model 间接关联用户）
    - obj.user_task.user（通过 user_task 间接关联用户）
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


class IsOwnerPermission(BasePermission):
    """
    统一归属权限：
    - 仅允许已登录用户访问
    - 仅允许访问自己所属的数据
    """

    def has_permission(self, request, view):
        # 必须登录
        return bool(request.user and getattr(request.user, 'is_authenticated', True))

    def has_object_permission(self, request, view, obj):
        owner = get_owner_user(obj)
        if owner is None:
            return False
        return getattr(owner, 'user_id', None) == getattr(request.user, 'user_id', None)


def get_owned_object_or_403(request, queryset, not_found_msg='资源不存在', **filters):
    """
    统一获取 + 归属校验：
    - 对象不存在 -> 404
    - 不属于当前用户 -> 403
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
    提供统一方法：get_owned_or_403
    """

    def get_owned_or_403(self, request, queryset, not_found_msg='资源不存在', **filters):
        return get_owned_object_or_403(request, queryset, not_found_msg=not_found_msg, **filters)


class OwnedQuerySetMixin:
    """
    统一归属查询集：
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
        # 当 owner_field = 'self' 时，表示对象本身就是用户对象
        if self.owner_field == 'self':
            return qs.filter(user_id=getattr(self.request.user, 'user_id', None))
        return qs.filter(**{self.owner_field: self.request.user})
