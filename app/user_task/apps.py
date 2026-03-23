"""
模型应用配置。
"""

from django.apps import AppConfig


class UserTaskConfig(AppConfig):
    # 默认主键类型
    default_auto_field = 'django.db.models.BigAutoField'
    # 应用路径
    name = 'app.user_task'
    # 管理后台显示名称
    verbose_name = '模型管理'
