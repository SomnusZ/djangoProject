"""
用户家具关联序列化器。
"""

from rest_framework import serializers

from app.furniture.models import Furniture

from .models import UserFurnitureRelation


class UserFurnitureRelationSerializer(serializers.ModelSerializer):
    """
    用户家具关联信息输出序列化器。
    用于绑定成功和查询接口的响应数据。
    额外展示 furniture_name，方便客户端无需二次查询。
    """

    furniture_name = serializers.CharField(source='furniture.furniture_name', read_only=True)

    class Meta:
        model = UserFurnitureRelation
        fields = (
            'relation_id',
            'user_id',
            'furniture_id',
            'furniture_name',
            'furniture_amount',
        )


class BindFurnitureToUserSerializer(serializers.Serializer):
    """
    绑定家具到用户序列化器。
    创建用户与家具的关联记录，初始数量为 0。
    同一用户对同一家具只允许存在一条关联记录。
    """

    furniture_id = serializers.IntegerField(required=True)

    def validate_furniture_id(self, value):
        if not Furniture.objects.filter(furniture_id=value).exists():
            raise serializers.ValidationError('家具不存在')
        return value

    def validate(self, attrs):
        # user 由视图注入，校验重复绑定
        user = self.context.get('user')
        if user and UserFurnitureRelation.objects.filter(
            user=user,
            furniture_id=attrs['furniture_id']
        ).exists():
            raise serializers.ValidationError('该用户已绑定该家具')
        return attrs

    def create(self, validated_data):
        user = self.context['user']
        return UserFurnitureRelation.objects.create(user=user, **validated_data)


class UnbindFurnitureFromUserSerializer(serializers.Serializer):
    """
    解绑用户与家具的关联序列化器。
    """

    furniture_id = serializers.IntegerField(required=True)

    def validate_furniture_id(self, value):
        if not Furniture.objects.filter(furniture_id=value).exists():
            raise serializers.ValidationError('家具不存在')
        return value
