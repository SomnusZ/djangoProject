"""
宠物眼球UV贴图应用配置。
"""

from django.apps import AppConfig


class PetEyeUvTextureConfig(AppConfig):
    # 默认主键类型
    default_auto_field = 'django.db.models.BigAutoField'
    # 应用路径
    name = 'app.pet_eye_uv_texture'
    # 管理后台显示名称
    verbose_name = '宠物眼球UV贴图'
