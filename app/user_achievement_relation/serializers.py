"""
用户成就关联序列化器。
"""

from rest_framework import serializers

from app.achievement.models import Achievement

from .models import UserAchievementRelation


class UserAchievementRelationSerializer(serializers.ModelSerializer):
    """
    用户成就关联信息输出序列化器。
    用于绑定成功和查询接口的响应数据。
    额外展示 achievement_name，方便客户端无需二次查询。
    """

    achievement_name = serializers.CharField(source='achievement.achievement_name', read_only=True)

    class Meta:
        model = UserAchievementRelation
        fields = (
            'relation_id',
            'user_id',
            'achievement_id',
            'achievement_name',
        )


class BindAchievementToUserSerializer(serializers.Serializer):
    """
    绑定成就到用户序列化器（即解锁成就）。
    同一用户对同一成就只允许存在一条关联记录，防止重复解锁。
    """

    achievement_id = serializers.IntegerField(required=True)

    def validate_achievement_id(self, value):
        if not Achievement.objects.filter(achievement_id=value).exists():
            raise serializers.ValidationError('成就不存在')
        return value

    def validate(self, attrs):
        # user 由视图注入，校验重复解锁
        user = self.context.get('user')
        if user and UserAchievementRelation.objects.filter(
            user=user,
            achievement_id=attrs['achievement_id']
        ).exists():
            raise serializers.ValidationError('该用户已解锁该成就')
        return attrs

    def create(self, validated_data):
        user = self.context['user']
        return UserAchievementRelation.objects.create(user=user, **validated_data)


class UnbindAchievementFromUserSerializer(serializers.Serializer):
    """
    解绑用户与成就的关联序列化器（即撤销成就）。
    """

    achievement_id = serializers.IntegerField(required=True)

    def validate_achievement_id(self, value):
        if not Achievement.objects.filter(achievement_id=value).exists():
            raise serializers.ValidationError('成就不存在')
        return value
