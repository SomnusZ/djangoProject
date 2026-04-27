"""
货币资产序列化器定义文件。
负责校验输入参数、转换模型与 JSON 之间的数据。
"""

from rest_framework import serializers

from .models import Wealth


class WealthSerializer(serializers.ModelSerializer):
    """
    货币资产信息输出序列化器。
    用于查询接口的响应数据。
    """

    class Meta:
        model = Wealth
        fields = (
            'wealth_id',
            'wealth_name',
        )


class CreateWealthSerializer(serializers.ModelSerializer):
    """
    新增货币资产序列化器。
    wealth_name 全局唯一，重复时抛出校验错误。
    """

    class Meta:
        model = Wealth
        fields = (
            'wealth_name',
        )

    def validate_wealth_name(self, value):
        if Wealth.objects.filter(wealth_name=value).exists():
            raise serializers.ValidationError('该货币资产名称已存在')
        return value


class UpdateWealthSerializer(serializers.ModelSerializer):
    """
    修改货币资产序列化器。
    仅允许修改 wealth_name。
    """

    class Meta:
        model = Wealth
        fields = (
            'wealth_name',
        )

    def validate_wealth_name(self, value):
        # 排除自身后检查名称唯一性
        if Wealth.objects.filter(wealth_name=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError('该货币资产名称已存在')
        return value


class DirWealthQuerySerializer(serializers.Serializer):
    """
    查询货币资产信息序列化器。
    支持通过 wealth_id 查询单条记录。
    """

    wealth_id = serializers.IntegerField(required=True)
