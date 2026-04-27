"""
家具序列化器定义文件。
负责校验输入参数、转换模型与 JSON 之间的数据。
"""

from rest_framework import serializers

from .models import Furniture


class FurnitureSerializer(serializers.ModelSerializer):
    """
    家具信息输出序列化器。
    用于查询接口的响应数据。
    """

    class Meta:
        model = Furniture
        fields = (
            'furniture_id',
            'furniture_name',
        )


class CreateFurnitureSerializer(serializers.ModelSerializer):
    """
    新增家具序列化器。
    furniture_name 全局唯一，重复时抛出校验错误。
    """

    class Meta:
        model = Furniture
        fields = (
            'furniture_name',
        )

    def validate_furniture_name(self, value):
        if Furniture.objects.filter(furniture_name=value).exists():
            raise serializers.ValidationError('该家具名称已存在')
        return value


class UpdateFurnitureSerializer(serializers.ModelSerializer):
    """
    修改家具序列化器。
    仅允许修改 furniture_name。
    """

    class Meta:
        model = Furniture
        fields = (
            'furniture_name',
        )

    def validate_furniture_name(self, value):
        # 排除自身后检查名称唯一性
        if Furniture.objects.filter(furniture_name=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError('该家具名称已存在')
        return value


class DirFurnitureQuerySerializer(serializers.Serializer):
    """
    查询家具信息序列化器。
    支持通过 furniture_id 查询单条记录。
    """

    furniture_id = serializers.IntegerField(required=True)
