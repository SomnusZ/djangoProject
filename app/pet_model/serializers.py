"""
宠物模型序列化器定义文件。
负责校验输入参数、转换模型与JSON之间的数据。
"""

from rest_framework import serializers

from .models import PetModel


class PetModelSerializer(serializers.ModelSerializer):
    """
    模型信息输出序列化器。
    """

    class Meta:
        model = PetModel
        fields = (
            'pet_model_id',
            'pet_model_name',
        )


class CreatePetModelSerializer(serializers.ModelSerializer):
    """
    新增模型序列化器。
    """

    class Meta:
        model = PetModel
        fields = (
            'pet_model_name',
        )


class UpdatePetModelSerializer(serializers.ModelSerializer):
    """
    修改宠物模型序列化器。
    仅允许修改 pet_model_name。
    """

    class Meta:
        model = PetModel
        fields = (
            'pet_model_name',
        )


class DirModelQuerySerializer(serializers.Serializer):
    """
    查询模型信息序列化器。
    支持 pet_model_id 查询。
    """

    pet_model_id = serializers.IntegerField(required=True)
