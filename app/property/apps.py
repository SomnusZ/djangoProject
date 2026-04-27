"""
属性 App 配置。
"""

from django.apps import AppConfig


class PropertyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.property'
    verbose_name = '属性'
