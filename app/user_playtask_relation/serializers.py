"""
用户玩法任务关联序列化器。
"""

from rest_framework import serializers

from app.playtask.models import Playtask

from .models import UserPlaytaskRelation


class UserPlaytaskRelationSerializer(serializers.ModelSerializer):
    """
    用户玩法任务关联信息输出序列化器。
    用于绑定成功和查询接口的响应数据。
    额外展示 playtask_name，方便客户端无需二次查询。
    """

    playtask_name = serializers.CharField(source='playtask.playtask_name', read_only=True)

    class Meta:
        model = UserPlaytaskRelation
        fields = (
            'relation_id',
            'user_id',
            'playtask_id',
            'playtask_name',
            'playtask_progress',
        )


class BindPlaytaskToUserSerializer(serializers.Serializer):
    """
    绑定玩法任务到用户序列化器。
    创建用户与玩法任务的关联记录，初始进度为 0。
    同一用户对同一玩法任务只允许存在一条关联记录。
    """

    playtask_id = serializers.IntegerField(required=True)

    def validate_playtask_id(self, value):
        if not Playtask.objects.filter(playtask_id=value).exists():
            raise serializers.ValidationError('玩法任务不存在')
        return value

    def validate(self, attrs):
        # user 由视图注入，校验重复绑定
        user = self.context.get('user')
        if user and UserPlaytaskRelation.objects.filter(
            user=user,
            playtask_id=attrs['playtask_id']
        ).exists():
            raise serializers.ValidationError('该用户已绑定该玩法任务')
        return attrs

    def create(self, validated_data):
        user = self.context['user']
        return UserPlaytaskRelation.objects.create(user=user, **validated_data)


class UnbindPlaytaskFromUserSerializer(serializers.Serializer):
    """
    解绑用户与玩法任务的关联序列化器。
    """

    playtask_id = serializers.IntegerField(required=True)

    def validate_playtask_id(self, value):
        if not Playtask.objects.filter(playtask_id=value).exists():
            raise serializers.ValidationError('玩法任务不存在')
        return value
