"""
宠物眼球UV贴图序列化器定义文件。
负责模型 → JSON 的数据转换。
"""

from rest_framework import serializers

from .models import PetEyeUv


class PetEyeUvSerializer(serializers.ModelSerializer):
    """
    宠物眼球UV贴图记录输出序列化器。
    """

    class Meta:
        model = PetEyeUv
        fields = (
            'pet_eye_uv_id',
            'created_at',
            'updated_at',
            'original_image_path',
            'workflow_status',
            'eye_count',
            'eye_uv_url_0',
            'eye_uv_url_1',
            'base_bgr_0',
            'base_bgr_1',
            'workflow_error',
        )
