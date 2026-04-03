"""
用户任务序列化器定义文件。
负责校验输入参数、转换模型与 JSON 之间的数据。
"""

from rest_framework import serializers

from app.user.models import User
from .models import UserTask


class UserTaskSerializer(serializers.ModelSerializer):
    """
    用户任务信息输出序列化器。
    """

    user_id = serializers.IntegerField(source='user.user_id', read_only=True)

    class Meta:
        model = UserTask
        fields = (
            'user_task_id',
            'user_id',
            'task_name',
        )


class CreateUserTaskSerializer(serializers.ModelSerializer):
    """
    新增用户任务序列化器。
    """

    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = UserTask
        fields = (
            'user_id',
            'task_name',
        )

    def validate_user_id(self, value):
        if not User.objects.filter(user_id=value).exists():
            raise serializers.ValidationError('用户不存在')
        return value

    def create(self, validated_data):
        user_id = validated_data.pop('user_id')
        user = User.objects.get(user_id=user_id)
        return UserTask.objects.create(user=user, **validated_data)


class UpdateUserTaskSerializer(serializers.ModelSerializer):
    """
    修改用户任务序列化器。
    仅允许修改 task_name。
    """

    class Meta:
        model = UserTask
        fields = (
            'task_name',
        )


class DirUserTaskQuerySerializer(serializers.Serializer):
    """
    查询用户任务信息序列化器。
    支持 user_task_id 查询。
    """

    user_task_id = serializers.IntegerField(required=True)


class DirUserTaskListByUserSerializer(serializers.Serializer):
    """
    根据用户查询任务列表序列化器。
    支持 user_id 或 user_phone_number。
    """

    user_id = serializers.IntegerField(required=False)
    user_phone_number = serializers.CharField(required=False)

    def validate(self, attrs):
        if not attrs.get('user_id') and not attrs.get('user_phone_number'):
            raise serializers.ValidationError('请提供 user_id 或 user_phone_number')
        return attrs
