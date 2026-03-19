"""
模型序列化器定义文件。
负责校验输入参数、转换模型与JSON之间的数据。
"""

from rest_framework import serializers

from app.user.models import User
from .models import PetModel


class PetModelSerializer(serializers.ModelSerializer):
    """
    模型信息输出序列化器。
    """

    user_id = serializers.IntegerField(source='user.user_id', read_only=True)

    class Meta:
        model = PetModel
        fields = (
            'pet_model_id',
            'user_id',
            'model_name',
            'model_address',
        )


class CreatePetModelSerializer(serializers.ModelSerializer):
    """
    新增模型序列化器。
    """

    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = PetModel
        fields = (
            'user_id',
            'model_name',
            'model_address',
        )

    def validate_user_id(self, value):
        if not User.objects.filter(user_id=value).exists():
            raise serializers.ValidationError('用户不存在')
        return value

    def create(self, validated_data):
        user_id = validated_data.pop('user_id')
        user = User.objects.get(user_id=user_id)
        return PetModel.objects.create(user=user, **validated_data)


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
    支持 pet_model_id 查询。
    """

    pet_model_id = serializers.IntegerField(required=True)


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
