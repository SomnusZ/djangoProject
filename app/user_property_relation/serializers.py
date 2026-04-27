"""
用户属性关联序列化器。
"""

from rest_framework import serializers

from app.property.models import Property

from .models import UserPropertyRelation


class UserPropertyRelationSerializer(serializers.ModelSerializer):
    """
    用户属性关联信息输出序列化器。
    用于绑定成功和查询接口的响应数据。
    额外展示 property_name，方便客户端无需二次查询。
    """

    property_name = serializers.CharField(source='property.property_name', read_only=True)

    class Meta:
        model = UserPropertyRelation
        fields = (
            'relation_id',
            'user_id',
            'property_id',
            'property_name',
            'property_amount',
        )


class BindPropertyToUserSerializer(serializers.Serializer):
    """
    绑定属性到用户序列化器。
    创建用户与属性的关联记录，初始数值为 0。
    同一用户对同一属性只允许存在一条关联记录。
    """

    property_id = serializers.IntegerField(required=True)

    def validate_property_id(self, value):
        if not Property.objects.filter(property_id=value).exists():
            raise serializers.ValidationError('属性不存在')
        return value

    def validate(self, attrs):
        # user 由视图注入，校验重复绑定
        user = self.context.get('user')
        if user and UserPropertyRelation.objects.filter(
            user=user,
            property_id=attrs['property_id']
        ).exists():
            raise serializers.ValidationError('该用户已绑定该属性')
        return attrs

    def create(self, validated_data):
        user = self.context['user']
        return UserPropertyRelation.objects.create(user=user, **validated_data)


class UnbindPropertyFromUserSerializer(serializers.Serializer):
    """
    解绑用户与属性的关联序列化器。
    """

    property_id = serializers.IntegerField(required=True)

    def validate_property_id(self, value):
        if not Property.objects.filter(property_id=value).exists():
            raise serializers.ValidationError('属性不存在')
        return value
