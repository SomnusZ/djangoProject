"""
任务动作关系序列化器。
"""

from rest_framework import serializers

from app.user_task.models import UserTask
from app.pet_action.models import PetAction

from .models import UserTaskActionRelation


class BindActionToTaskSerializer(serializers.Serializer):
    """
    绑定动作到任务。
    """

    user_task_id = serializers.IntegerField(required=True)
    pet_action_id = serializers.IntegerField(required=True)

    def validate(self, attrs):
        user_task_id = attrs.get('user_task_id')
        pet_action_id = attrs.get('pet_action_id')

        if not UserTask.objects.filter(user_task_id=user_task_id).exists():
            raise serializers.ValidationError('任务不存在')
        if not PetAction.objects.filter(pet_action_id=pet_action_id).exists():
            raise serializers.ValidationError('动作不存在')

        if UserTaskActionRelation.objects.filter(
            user_task_id=user_task_id,
            pet_action_id=pet_action_id
        ).exists():
            raise serializers.ValidationError('该任务已绑定该动作')

        return attrs

    def create(self, validated_data):
        return UserTaskActionRelation.objects.create(**validated_data)


class UnbindActionFromTaskSerializer(serializers.Serializer):
    """
    解绑动作与任务。
    """

    user_task_id = serializers.IntegerField(required=True)
    pet_action_id = serializers.IntegerField(required=True)

    def validate(self, attrs):
        user_task_id = attrs.get('user_task_id')
        pet_action_id = attrs.get('pet_action_id')

        if not UserTask.objects.filter(user_task_id=user_task_id).exists():
            raise serializers.ValidationError('任务不存在')
        if not PetAction.objects.filter(pet_action_id=pet_action_id).exists():
            raise serializers.ValidationError('动作不存在')

        return attrs


class DirActionListByTaskSerializer(serializers.Serializer):
    """
    通过任务查询动作列表。
    """

    user_task_id = serializers.IntegerField(required=True)
