"""
家具 App 配置。
"""

from django.apps import AppConfig


class FurnitureConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.furniture'
    verbose_name = '家具'
