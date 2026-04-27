"""
用户家具关联 App 配置。
"""

from django.apps import AppConfig


class UserFurnitureRelationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.user_furniture_relation'
    verbose_name = '用户家具关联'
