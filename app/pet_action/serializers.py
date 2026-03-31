"""
动作序列化器定义文件。
负责校验输入参数、转换模型与JSON之间的数据。
"""

from rest_framework import serializers

from .models import PetAction


class PetActionSerializer(serializers.ModelSerializer):
    """
    动作信息输出序列化器。
    """

    class Meta:
        model = PetAction
        fields = (
            'pet_action_id',
            'pet_action_name',
        )


class CreatePetActionSerializer(serializers.ModelSerializer):
    """
    新增动作序列化器。
    """

    class Meta:
        model = PetAction
        fields = (
            'pet_action_name',
        )


class DirActionQuerySerializer(serializers.Serializer):
    """
    查询动作信息序列化器。
    支持 pet_action_id 查询。
    """

    pet_action_id = serializers.IntegerField(required=True)


