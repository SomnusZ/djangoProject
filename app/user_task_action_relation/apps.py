"""
任务动作关系 App 配置。
"""

from django.apps import AppConfig


class UserTaskActionRelationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.user_task_action_relation'
    verbose_name = '任务动作关系'
