"""
玩法任务 App 配置。
"""

from django.apps import AppConfig


class PlaytaskConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.playtask'
    verbose_name = '玩法任务'
