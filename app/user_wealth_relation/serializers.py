"""
用户货币资产关联序列化器。
"""

from rest_framework import serializers

from app.user.models import User
from app.wealth.models import Wealth

from .models import UserWealthRelation


class UserWealthRelationSerializer(serializers.ModelSerializer):
    """
    用户货币资产关联信息输出序列化器。
    用于绑定成功和查询接口的响应数据。
    """

    wealth_name = serializers.CharField(source='wealth.wealth_name', read_only=True)

    class Meta:
        model = UserWealthRelation
        fields = (
            'relation_id',
            'user_id',
            'wealth_id',
            'wealth_name',
            'wealth_amount',
        )


class BindWealthToUserSerializer(serializers.Serializer):
    """
    绑定货币资产到用户序列化器。
    创建用户与货币资产的关联记录，初始数量为 0。
    同一用户对同一货币资产只允许存在一条关联记录。
    """

    wealth_id = serializers.IntegerField(required=True)

    def validate_wealth_id(self, value):
        if not Wealth.objects.filter(wealth_id=value).exists():
            raise serializers.ValidationError('货币资产不存在')
        return value

    def validate(self, attrs):
        # user 由视图注入，校验重复绑定
        user = self.context.get('user')
        if user and UserWealthRelation.objects.filter(
            user=user,
            wealth_id=attrs['wealth_id']
        ).exists():
            raise serializers.ValidationError('该用户已绑定该货币资产')
        return attrs

    def create(self, validated_data):
        user = self.context['user']
        return UserWealthRelation.objects.create(user=user, **validated_data)


class UnbindWealthFromUserSerializer(serializers.Serializer):
    """
    解绑用户与货币资产的关联序列化器。
    """

    wealth_id = serializers.IntegerField(required=True)

    def validate_wealth_id(self, value):
        if not Wealth.objects.filter(wealth_id=value).exists():
            raise serializers.ValidationError('货币资产不存在')
        return value


class DirWealthListByUserSerializer(serializers.Serializer):
    """
    查询用户名下货币资产列表序列化器。
    GET 请求无额外参数，用户 ID 从 JWT 中自动获取。
    """
    pass
