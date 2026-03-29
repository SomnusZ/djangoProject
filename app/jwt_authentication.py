"""
自定义 JWT 认证：支持使用 app.user.models.User 作为认证用户模型。
"""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.settings import api_settings

from app.user.models import User as AppUser


class AppUserJWTAuthentication(JWTAuthentication):
    """
    使用自定义用户表（app.user.models.User）解析 JWT。
    """

    def get_user(self, validated_token):
        user_id = validated_token.get(api_settings.USER_ID_CLAIM)
        if user_id is None:
            raise AuthenticationFailed('Token 无效：未包含用户ID', code='token_no_user')

        try:
            return AppUser.objects.get(user_id=user_id)
        except AppUser.DoesNotExist:
            raise AuthenticationFailed('用户不存在', code='user_not_found')
