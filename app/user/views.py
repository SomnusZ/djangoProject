"""
视图文件。
包含用户相关接口：dirUser、updateUser、creatUser。
"""

from django.contrib.auth.hashers import check_password
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action

from .models import User
from .serializers import (
    UserSerializer,
    CreateUserSerializer,
    UpdateUserSerializer,
    LoginSerializer,
    DirUserQuerySerializer,
)
from app.utils import success_response, error_response


class UserViewSet(viewsets.GenericViewSet):
    """
    用户接口视图集。
    使用自定义 action 实现登录、查询、注册、更新等操作。
    """

    queryset = User.objects.all()

    @action(detail=False, methods=['post'], url_path='creatUser')
    def creat_user(self, request):
        """
        用户注册/新增接口。
        请求体示例：
        {
            "user_mail_address": "test@example.com",
            "user_password": "123456",
            "user_name": "Tom",
            "user_phone_number": "13800000000"
        }
        """
        serializer = CreateUserSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        return success_response(UserSerializer(user).data, message='注册成功', status_code=status.HTTP_201_CREATED)

    @action(detail=False, methods=['put', 'patch'], url_path='updateUser')
    def update_user(self, request):
        """
        用户信息修改接口。
        需要 user_id 或 user_mail_address 作为定位条件。
        请求体示例：
        {
            "user_id": 1,
            "user_name": "Jerry",
            "user_password": "newpass"
        }
        """
        user_id = request.data.get('user_id')
        user_mail_address = request.data.get('user_mail_address')
        if not user_id and not user_mail_address:
            return error_response('请提供 user_id 或 user_mail_address', status_code=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(Q(user_id=user_id) | Q(user_mail_address=user_mail_address)).first()
        if not user:
            return error_response('用户不存在', status_code=status.HTTP_404_NOT_FOUND)

        # 移除仅用于定位的字段，避免序列化器报错
        update_data = request.data.copy()
        update_data.pop('user_id', None)
        update_data.pop('user_mail_address', None)

        serializer = UpdateUserSerializer(user, data=update_data, partial=True)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return success_response(UserSerializer(user).data, message='修改成功')

    @action(detail=False, methods=['post'], url_path='dirUser')
    def dir_user_login(self, request):
        """
        用户登录接口。
        请求体示例：
        {
            "user_mail_address": "test@example.com",
            "user_password": "123456"
        }
        """
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        user_mail_address = serializer.validated_data['user_mail_address']
        user_password = serializer.validated_data['user_password']

        user = User.objects.filter(user_mail_address=user_mail_address).first()
        if not user:
            return error_response('用户不存在', status_code=status.HTTP_404_NOT_FOUND)

        if not check_password(user_password, user.user_password):
            return error_response('密码错误', status_code=status.HTTP_400_BAD_REQUEST)

        return success_response(UserSerializer(user).data, message='登录成功')

    @action(detail=False, methods=['get'], url_path='dirUser')
    def dir_user_info(self, request):
        """
        用户信息查询接口。
        查询参数示例：
        /api/users/dirUser/?user_id=1
        或
        /api/users/dirUser/?user_mail_address=test@example.com
        """
        serializer = DirUserQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        user_id = serializer.validated_data.get('user_id')
        user_mail_address = serializer.validated_data.get('user_mail_address')

        user = User.objects.filter(Q(user_id=user_id) | Q(user_mail_address=user_mail_address)).first()
        if not user:
            return error_response('用户不存在', status_code=status.HTTP_404_NOT_FOUND)

        return success_response(UserSerializer(user).data, message='查询成功')


def register_page(request):
    """
    简单注册页视图。
    仅用于前端联调测试。
    """
    from django.shortcuts import render

    return render(request, 'register.html')
