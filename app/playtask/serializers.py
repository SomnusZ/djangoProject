"""
玩法任务序列化器定义文件。
负责校验输入参数、转换模型与 JSON 之间的数据。
"""

from rest_framework import serializers

from .models import Playtask


class PlaytaskSerializer(serializers.ModelSerializer):
    """
    玩法任务信息输出序列化器。
    用于查询接口的响应数据。
    """

    class Meta:
        model = Playtask
        fields = (
            'playtask_id',
            'playtask_name',
        )


class CreatePlaytaskSerializer(serializers.ModelSerializer):
    """
    新增玩法任务序列化器。
    playtask_name 全局唯一，重复时抛出校验错误。
    """

    class Meta:
        model = Playtask
        fields = (
            'playtask_name',
        )

    def validate_playtask_name(self, value):
        if Playtask.objects.filter(playtask_name=value).exists():
            raise serializers.ValidationError('该玩法任务名称已存在')
        return value


class UpdatePlaytaskSerializer(serializers.ModelSerializer):
    """
    修改玩法任务序列化器。
    仅允许修改 playtask_name。
    """

    class Meta:
        model = Playtask
        fields = (
            'playtask_name',
        )

    def validate_playtask_name(self, value):
        # 排除自身后检查名称唯一性
        if Playtask.objects.filter(playtask_name=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError('该玩法任务名称已存在')
        return value


class DirPlaytaskQuerySerializer(serializers.Serializer):
    """
    查询玩法任务信息序列化器。
    支持通过 playtask_id 查询单条记录。
    """

    playtask_id = serializers.IntegerField(required=True)
