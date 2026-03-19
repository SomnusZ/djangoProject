"""
序列化器定义文件。
负责校验输入参数、转换模型与JSON之间的数据。
"""

from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    用户信息输出序列化器。
    用于对外返回用户信息（不包含密码）。
    """

    class Meta:
        model = User
        # 明确字段，避免密码意外返回
        fields = (
            'user_id',
            'user_name',
            'user_profile_picture',
            'user_phone_number',
            'user_mail_address',
        )


class CreateUserSerializer(serializers.ModelSerializer):
    """
    用户注册/新增序列化器。
    支持邮箱 + 密码注册，可选用户名、手机号、头像。
    """

    class Meta:
        model = User
        fields = (
            'user_name',
            'user_profile_picture',
            'user_phone_number',
            'user_password',
            'user_mail_address',
        )
        extra_kwargs = {
            'user_password': {'write_only': True},
        }

    def validate_user_password(self, value):
        # 简单密码长度校验
        if len(value) < 6:
            raise serializers.ValidationError('密码长度不能小于6位')
        return value

    def create(self, validated_data):
        # 对密码进行哈希处理
        raw_password = validated_data.get('user_password')
        validated_data['user_password'] = make_password(raw_password)
        return super().create(validated_data)


class UpdateUserSerializer(serializers.ModelSerializer):
    """
    用户信息更新序列化器。
    允许更新用户名、手机号、头像、密码。
    """

    class Meta:
        model = User
        fields = (
            'user_name',
            'user_profile_picture',
            'user_phone_number',
            'user_password',
        )
        extra_kwargs = {
            'user_password': {'write_only': True, 'required': False},
        }

    def update(self, instance, validated_data):
        # 如果提供了密码则进行哈希
        if 'user_password' in validated_data:
            validated_data['user_password'] = make_password(validated_data['user_password'])
        return super().update(instance, validated_data)


class LoginSerializer(serializers.Serializer):
    """
    登录序列化器。
    仅校验邮箱和密码。
    """

    user_mail_address = serializers.EmailField()
    user_password = serializers.CharField()


class DirUserQuerySerializer(serializers.Serializer):
    """
    查询用户信息序列化器。
    支持 user_id 或 user_mail_address 作为查询条件。
    """

    user_id = serializers.IntegerField(required=False)
    user_mail_address = serializers.EmailField(required=False)

    def validate(self, attrs):
        # 至少提供一个查询条件
        if not attrs.get('user_id') and not attrs.get('user_mail_address'):
            raise serializers.ValidationError('请提供 user_id 或 user_mail_address')
        return attrs
