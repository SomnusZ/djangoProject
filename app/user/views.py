"""
视图文件。
包含用户相关接口：dirUser、updateUser、createUser。
"""

from django.contrib.auth.hashers import check_password
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    UserSerializer,
    CreateUserSerializer,
    UpdateUserSerializer,
    LoginSerializer,
    DirUserQuerySerializer,
)
from app.utils import success_response, error_response
from app.permissions import get_owned_object_or_403


class UserViewSet(viewsets.GenericViewSet):
    """
    用户接口视图集。
    使用自定义 action 实现登录、查询、注册、更新等操作。
    """

    queryset = User.objects.all()

    def get_permissions(self):
        """
        权限控制：
        - 注册 / 登录允许匿名访问
        - 其他接口必须携带有效 Token
        """
        # 优先按 action 名称判断（DRF 会自动设置 self.action）
        if self.action == 'create_user':
            return [AllowAny()]
        if self.action == 'dir_user' and self.request.method == 'POST':
            return [AllowAny()]
        return [IsAuthenticated()]

    # 注册接口允许匿名访问
    @action(detail=False, methods=['post'], url_path='createUser')
    def create_user(self, request):
        """
        用户注册/新增接口。
        请求体示例：
        {
            "user_phone_number": "13800000000",
            "user_password": "123456",
            "user_password_confirm": "123456",
            "user_phone_code": "1234"
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
        仅允许修改当前登录用户自己的信息。
        请求体示例：
        {
            "user_name": "Jerry"
        }
        """
        user = request.user

        # 移除仅用于定位的字段，避免序列化器报错
        update_data = request.data.copy()
        update_data.pop('user_id', None)
        update_data.pop('user_mail_address', None)

        serializer = UpdateUserSerializer(user, data=update_data, partial=True)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return success_response(UserSerializer(user).data, message='修改成功')

    # 登录接口允许匿名访问（POST）；查询接口需要登录（GET）
    @action(detail=False, methods=['get', 'post'], url_path='dirUser')
    def dir_user(self, request):
        """
        用户登录/查询接口。
        POST：登录
        GET：查询用户信息
        """
        if request.method == 'POST':
            # 登录逻辑
            serializer = LoginSerializer(data=request.data)
            if not serializer.is_valid():
                return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

            user_phone_number = serializer.validated_data['user_phone_number']
            login_type = serializer.validated_data['login_type']
            user_password = serializer.validated_data.get('user_password')
            user_phone_code = serializer.validated_data.get('user_phone_code')

            user = User.objects.filter(user_phone_number=user_phone_number).first()
            if not user:
                return error_response('用户不存在', status_code=status.HTTP_404_NOT_FOUND)

            if login_type == 'password':
                if not check_password(user_password, user.user_password):
                    return error_response('密码错误', status_code=status.HTTP_400_BAD_REQUEST)
            elif login_type == 'code':
                # 手机验证码登录占位（暂不做真实校验）
                if not user_phone_code:
                    return error_response('请输入手机验证码', status_code=status.HTTP_400_BAD_REQUEST)

            # 生成 JWT（access / refresh）
            refresh = RefreshToken.for_user(user)
            token_data = {
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
            }

            # 返回用户信息 + Token
            data = {
                'user': UserSerializer(user).data,
                'token': token_data,
            }

            return success_response(data, message='登录成功')

        # GET：查询用户信息（需登录）
        serializer = DirUserQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        filters = {}
        user_id = serializer.validated_data.get('user_id')
        user_phone_number = serializer.validated_data.get('user_phone_number')
        if user_id:
            filters['user_id'] = user_id
        if user_phone_number:
            filters['user_phone_number'] = user_phone_number

        user, denied = get_owned_object_or_403(
            request,
            User.objects.all(),
            not_found_msg='用户不存在',
            **filters,
        )
        if denied:
            return denied

        return success_response(UserSerializer(user).data, message='查询成功')


# 测试页面已改为TemplateView
