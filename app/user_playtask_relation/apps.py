"""
用户玩法任务关联 App 配置。
"""

from django.apps import AppConfig


class UserPlaytaskRelationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.user_playtask_relation'
    verbose_name = '用户玩法任务关联'
