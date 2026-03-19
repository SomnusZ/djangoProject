"""
动作应用配置。
"""

from django.apps import AppConfig


class PetActionConfig(AppConfig):
    # 默认主键类型
    default_auto_field = 'django.db.models.BigAutoField'
    # 应用路径
    name = 'app.pet_action'
    # 管理后台显示名称
    verbose_name = '动作管理'
