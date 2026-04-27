"""
用户属性关联 App 配置。
"""

from django.apps import AppConfig


class UserPropertyRelationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.user_property_relation'
    verbose_name = '用户属性关联'
