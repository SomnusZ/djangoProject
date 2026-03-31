"""
模型序列化器定义文件。
负责校验输入参数、转换模型与JSON之间的数据。
"""

from rest_framework import serializers

from app.user.models import User
from app.pet_model.models import PetModel as BasePetModel
from app.pet_action.models import PetAction
from app.user_task_action_relation.models import UserTaskActionRelation
from .models import PetModel


class PetModelSerializer(serializers.ModelSerializer):
    """
    模型信息输出序列化器。
    """

    user_id = serializers.IntegerField(source='user.user_id', read_only=True)
    pet_model_id = serializers.IntegerField(source='pet_model.pet_model_id', read_only=True)
    action_list = serializers.SerializerMethodField()

    class Meta:
        model = PetModel
        fields = (
            'user_task_id',
            'user_id',
            'pet_model_id',
            'model_name',
            'model_address',
            'action_list',
        )

    def get_action_list(self, obj):
        """
        返回当前任务已关联的动作列表。
        """
        action_ids = UserTaskActionRelation.objects.filter(user_task=obj).values_list('pet_action_id', flat=True)
        actions = PetAction.objects.filter(pet_action_id__in=action_ids).values('pet_action_id', 'pet_action_name')
        return list(actions)


class CreatePetModelSerializer(serializers.ModelSerializer):
    """
    新增模型序列化器。
    """

    user_id = serializers.IntegerField(write_only=True)
    pet_model_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = PetModel
        fields = (
            'user_id',
            'pet_model_id',
            'model_name',
            'model_address',
        )

    def validate_user_id(self, value):
        if not User.objects.filter(user_id=value).exists():
            raise serializers.ValidationError('用户不存在')
        return value

    def validate_pet_model_id(self, value):
        if not BasePetModel.objects.filter(pet_model_id=value).exists():
            raise serializers.ValidationError('宠物模型不存在')
        return value

    def create(self, validated_data):
        user_id = validated_data.pop('user_id')
        pet_model_id = validated_data.pop('pet_model_id')
        user = User.objects.get(user_id=user_id)
        pet_model = BasePetModel.objects.get(pet_model_id=pet_model_id)
        return PetModel.objects.create(user=user, pet_model=pet_model, **validated_data)


class UpdatePetModelSerializer(serializers.ModelSerializer):
    """
    修改模型序列化器。
    仅允许修改 model_name。
    """

    class Meta:
        model = PetModel
        fields = (
            'model_name',
        )


class DirModelQuerySerializer(serializers.Serializer):
    """
    查询模型信息序列化器。
    支持 user_task_id 查询。
    """

    user_task_id = serializers.IntegerField(required=True)


class DirModelListByUserSerializer(serializers.Serializer):
    """
    根据用户查询模型列表序列化器。
    支持 user_id 或 user_mail_address。
    """

    user_id = serializers.IntegerField(required=False)
    user_mail_address = serializers.EmailField(required=False)

    def validate(self, attrs):
        if not attrs.get('user_id') and not attrs.get('user_mail_address'):
            raise serializers.ValidationError('请提供 user_id 或 user_mail_address')
        return attrs
