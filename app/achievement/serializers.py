"""
成就序列化器定义文件。
负责校验输入参数、转换模型与 JSON 之间的数据。
"""

from rest_framework import serializers

from .models import Achievement


class AchievementSerializer(serializers.ModelSerializer):
    """
    成就信息输出序列化器。
    用于查询接口的响应数据。
    """

    class Meta:
        model = Achievement
        fields = (
            'achievement_id',
            'achievement_name',
        )


class CreateAchievementSerializer(serializers.ModelSerializer):
    """
    新增成就序列化器。
    achievement_name 全局唯一，重复时抛出校验错误。
    """

    class Meta:
        model = Achievement
        fields = (
            'achievement_name',
        )

    def validate_achievement_name(self, value):
        if Achievement.objects.filter(achievement_name=value).exists():
            raise serializers.ValidationError('该成就名称已存在')
        return value


class UpdateAchievementSerializer(serializers.ModelSerializer):
    """
    修改成就序列化器。
    仅允许修改 achievement_name。
    """

    class Meta:
        model = Achievement
        fields = (
            'achievement_name',
        )

    def validate_achievement_name(self, value):
        # 排除自身后检查名称唯一性
        if Achievement.objects.filter(achievement_name=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError('该成就名称已存在')
        return value


class DirAchievementQuerySerializer(serializers.Serializer):
    """
    查询成就信息序列化器。
    支持通过 achievement_id 查询单条记录。
    """

    achievement_id = serializers.IntegerField(required=True)
