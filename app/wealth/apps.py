"""
货币资产 App 配置。
"""

from django.apps import AppConfig


class WealthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.wealth'
    verbose_name = '货币资产'
