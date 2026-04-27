"""
序列化器定义文件。
负责校验输入参数、转换模型与 JSON 之间的数据。
"""

import re
import secrets
import string

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
            'user_status',
            'user_role',
        )


class CreateUserSerializer(serializers.ModelSerializer):
    """
    用户注册/新增序列化器。
    当前仅支持手机号注册（邮箱弃用）。
    """

    # 手机号必填（弃用邮箱）
    user_phone_number = serializers.CharField(required=True)
    # 密码确认
    user_password_confirm = serializers.CharField(write_only=True)
    # 手机验证码（占位，后续接入短信服务）
    user_phone_code = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'user_phone_number',
            'user_password',
            'user_password_confirm',
            'user_phone_code',
        )
        extra_kwargs = {
            'user_password': {'write_only': True},
        }

    def validate_user_password(self, value):
        # 简单密码长度校验
        if len(value) < 6:
            raise serializers.ValidationError('密码长度不能小于6位')
        return value

    def validate_user_phone_number(self, value):
        """
        手机号格式校验（中国大陆 11 位手机号）。
        允许为空（前端可不传）。
        """
        if value is None or value == '':
            return value
        value = value.strip()
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式不正确')
        if User.objects.filter(user_phone_number=value).exists():
            raise serializers.ValidationError('手机号已存在')
        return value

    def validate_user_phone_code(self, value):
        """
        手机验证码校验（占位）。
        目前仅校验必填与非空，后续接入短信服务再做真实校验。
        """
        value = value.strip()
        if not value:
            raise serializers.ValidationError('请输入手机验证码')
        return value

    def validate(self, attrs):
        # 密码确认校验
        if attrs.get('user_password') != attrs.get('user_password_confirm'):
            raise serializers.ValidationError('两次输入的密码不一致')
        return attrs

    def create(self, validated_data):
        # 对密码进行哈希处理
        raw_password = validated_data.get('user_password')
        validated_data['user_password'] = make_password(raw_password)
        # 移除确认字段与验证码字段（不入库）
        validated_data.pop('user_password_confirm', None)
        validated_data.pop('user_phone_code', None)
        # 自动生成用户名：user_ + 随机大小写字母和数字
        random_part = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
        validated_data['user_name'] = f'user_{random_part}'
        # 邮箱弃用，保持为空
        validated_data['user_mail_address'] = None
        return super().create(validated_data)


class UpdateUserSerializer(serializers.ModelSerializer):
    """
    用户信息更新序列化器。
    允许修改用户名、用户状态。
    """

    class Meta:
        model = User
        fields = (
            'user_name',
            'user_status',
        )
        extra_kwargs = {
            'user_name':   {'required': False},
            'user_status': {'required': False},
        }


class LoginSerializer(serializers.Serializer):
    """
    登录序列化器。
    支持：手机号 + 密码 / 手机号 + 验证码。
    """

    user_phone_number = serializers.CharField(required=True)
    login_type = serializers.ChoiceField(choices=['password', 'code'])
    user_password = serializers.CharField(required=False, allow_blank=True)
    user_phone_code = serializers.CharField(required=False, allow_blank=True)

    def validate_user_phone_number(self, value):
        value = value.strip()
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式不正确')
        return value

    def validate(self, attrs):
        login_type = attrs.get('login_type')
        if login_type == 'password':
            if not attrs.get('user_password'):
                raise serializers.ValidationError('请输入密码')
        if login_type == 'code':
            if not attrs.get('user_phone_code'):
                raise serializers.ValidationError('请输入手机验证码')
        return attrs


class DirUserQuerySerializer(serializers.Serializer):
    """
    查询用户信息序列化器。
    支持 user_id 或 user_phone_number 作为查询条件。
    """

    user_id = serializers.IntegerField(required=False)
    user_phone_number = serializers.CharField(required=False)

    def validate(self, attrs):
        # 至少提供一个查询条件
        if not attrs.get('user_id') and not attrs.get('user_phone_number'):
            raise serializers.ValidationError('请提供 user_id 或 user_phone_number')
        return attrs
