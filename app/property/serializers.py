"""
属性序列化器定义文件。
负责校验输入参数、转换模型与 JSON 之间的数据。
"""

from rest_framework import serializers

from .models import Property


class PropertySerializer(serializers.ModelSerializer):
    """
    属性信息输出序列化器。
    用于查询接口的响应数据。
    """

    class Meta:
        model = Property
        fields = (
            'property_id',
            'property_name',
        )


class CreatePropertySerializer(serializers.ModelSerializer):
    """
    新增属性序列化器。
    property_name 全局唯一，重复时抛出校验错误。
    """

    class Meta:
        model = Property
        fields = (
            'property_name',
        )

    def validate_property_name(self, value):
        if Property.objects.filter(property_name=value).exists():
            raise serializers.ValidationError('该属性名称已存在')
        return value


class UpdatePropertySerializer(serializers.ModelSerializer):
    """
    修改属性序列化器。
    仅允许修改 property_name。
    """

    class Meta:
        model = Property
        fields = (
            'property_name',
        )

    def validate_property_name(self, value):
        # 排除自身后检查名称唯一性
        if Property.objects.filter(property_name=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError('该属性名称已存在')
        return value


class DirPropertyQuerySerializer(serializers.Serializer):
    """
    查询属性信息序列化器。
    支持通过 property_id 查询单条记录。
    """

    property_id = serializers.IntegerField(required=True)
