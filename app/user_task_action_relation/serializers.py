"""
浠诲姟鍔ㄤ綔鍏崇郴搴忓垪鍖栧櫒瀹氫箟鏂囦欢銆
"""

from rest_framework import serializers

from app.user_task.models import UserTask
from app.pet_action.models import PetAction
from .models import UserTaskActionRelation


class BindActionToTaskSerializer(serializers.ModelSerializer):
    """
    缁戝畾鍔ㄤ綔鍒颁换鍔＄殑搴忓垪鍖栧櫒銆
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
            raise serializers.ValidationError('浠诲姟涓嶅瓨鍦')
        return value

    def validate_pet_action_id(self, value):
        if not PetAction.objects.filter(pet_action_id=value).exists():
            raise serializers.ValidationError('鍔ㄤ綔涓嶅瓨鍦')
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
    瑙ｇ粦鍔ㄤ綔涓庝换鍔＄殑搴忓垪鍖栧櫒銆
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
            raise serializers.ValidationError('浠诲姟涓嶅瓨鍦')
        return value

    def validate_pet_action_id(self, value):
        if not PetAction.objects.filter(pet_action_id=value).exists():
            raise serializers.ValidationError('鍔ㄤ綔涓嶅瓨鍦')
        return value


class DirActionListByTaskSerializer(serializers.Serializer):
    """
    鏍规嵁浠诲姟鏌ヨ㈠姩浣滃垪琛ㄥ簭鍒楀寲鍣ㄣ
    鏀鎸 user_task_id 鏌ヨ銆
    """

    user_task_id = serializers.IntegerField(required=True)
