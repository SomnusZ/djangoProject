"""
任务动作关系序列化器定义文件。
"""

from rest_framework import serializers

from app.user_task.models import PetModel as UserTask
from app.pet_action.models import PetAction
from .models import UserTaskActionRelation


class BindActionToTaskSerializer(serializers.ModelSerializer):
    """
    绑定动作到任务的序列化器。
    """

    user_task_id = serializers.IntegerField(write_only=True)
    pet_action_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = UserTaskActionRelation
        fields = (
            'user_task_id',
            'pet_action_id',
        )

    def validate_user_task_id(self, value):
        if not UserTask.objects.filter(user_task_id=value).exists():
            raise serializers.ValidationError('任务不存在')
        return value

    def validate_pet_action_id(self, value):
        if not PetAction.objects.filter(pet_action_id=value).exists():
            raise serializers.ValidationError('动作不存在')
        return value

    def create(self, validated_data):
        user_task_id = validated_data.pop('user_task_id')
        pet_action_id = validated_data.pop('pet_action_id')
        user_task = UserTask.objects.get(user_task_id=user_task_id)
        pet_action = PetAction.objects.get(pet_action_id=pet_action_id)
        obj, _ = UserTaskActionRelation.objects.get_or_create(user_task=user_task, pet_action=pet_action)
        return obj


class UnbindActionFromTaskSerializer(serializers.ModelSerializer):
    """
    解绑动作与任务的序列化器。
    """

    user_task_id = serializers.IntegerField(write_only=True)
    pet_action_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = UserTaskActionRelation
        fields = (
            'user_task_id',
            'pet_action_id',
        )

    def validate_user_task_id(self, value):
        if not UserTask.objects.filter(user_task_id=value).exists():
            raise serializers.ValidationError('任务不存在')
        return value

    def validate_pet_action_id(self, value):
        if not PetAction.objects.filter(pet_action_id=value).exists():
            raise serializers.ValidationError('动作不存在')
        return value


class DirActionListByTaskSerializer(serializers.Serializer):
    """
    根据任务查询动作列表序列化器。
    支持 user_task_id 查询。
    """

    user_task_id = serializers.IntegerField(required=True)
