"""
动作序列化器定义文件。
负责校验输入参数、转换模型与JSON之间的数据。
"""

from rest_framework import serializers

from app.user_task.models import PetModel
from .models import PetAction


class PetActionSerializer(serializers.ModelSerializer):
    """
    动作信息输出序列化器。
    """

    user_task_id = serializers.IntegerField(source='pet_model.user_task_id', read_only=True)

    class Meta:
        model = PetAction
        fields = (
            'pet_action_id',
            'user_task_id',
            'pet_action_name',
        )


class CreatePetActionSerializer(serializers.ModelSerializer):
    """
    新增动作序列化器。
    """

    user_task_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = PetAction
        fields = (
            'user_task_id',
            'pet_action_name',
        )

    def validate_user_task_id(self, value):
        if not PetModel.objects.filter(user_task_id=value).exists():
            raise serializers.ValidationError('模型不存在')
        return value

    def create(self, validated_data):
        user_task_id = validated_data.pop('user_task_id')
        pet_model = PetModel.objects.get(user_task_id=user_task_id)
        return PetAction.objects.create(pet_model=pet_model, **validated_data)


class DirActionQuerySerializer(serializers.Serializer):
    """
    查询动作信息序列化器。
    支持 pet_action_id 查询。
    """

    pet_action_id = serializers.IntegerField(required=True)


class DirActionListByPetModelSerializer(serializers.Serializer):
    """
    根据模型查询动作列表序列化器。
    支持 user_task_id 查询。
    """

    user_task_id = serializers.IntegerField(required=True)
