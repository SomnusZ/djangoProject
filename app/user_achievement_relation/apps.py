"""
用户成就关联 App 配置。
"""

from django.apps import AppConfig


class UserAchievementRelationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.user_achievement_relation'
    verbose_name = '用户成就关联'
