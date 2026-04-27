"""
成就 App 配置。
"""

from django.apps import AppConfig


class AchievementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.achievement'
    verbose_name = '成就'
