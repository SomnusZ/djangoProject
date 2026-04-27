"""
用户货币资产关联 App 配置。
"""

from django.apps import AppConfig


class UserWealthRelationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.user_wealth_relation'
    verbose_name = '用户货币资产关联'
