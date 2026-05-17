"""
视图文件。
包含用户相关接口：dirUser、updateUser、createUser。
"""

import uuid

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
from app.permissions import get_owned_object_or_403, get_user_from_request
from app.user_task.models import UserTask


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
        - 若 @action 上声明了 permission_classes，优先使用（支持未来管理员接口扩展）
        """
        # 匿名接口显式豁免（优先级最高）
        if self.action == 'create_user':
            return [AllowAny()]
        if self.action == 'dir_user' and self.request.method == 'POST':
            return [AllowAny()]
        # 临时兼容：前端未接入 token 时，通过手机号传参，放行所有请求由视图层做用户解析
        if self.action in ('dir_user', 'update_user', 'dir_user_status'):
            return [AllowAny()]
        # 读取 @action 上声明的 permission_classes（如 IsAdminUser）
        action_method = getattr(self, self.action, None)
        if action_method:
            action_perms = getattr(action_method, 'kwargs', {}).get('permission_classes')
            if action_perms is not None:
                return [perm() for perm in action_perms]
        # 默认：登录即可
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
        # 手机号已注册单独判断，返回特定 result 标识
        phone = request.data.get('user_phone_number', '').strip()
        if phone and User.objects.filter(user_phone_number=phone).exists():
            return error_response('手机号已注册', status_code=status.HTTP_200_OK, result='registered')

        serializer = CreateUserSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()

        # 注册成功后同步创建一条空的 UserTask，task_id 预生成，task_name 固定为 "mao"
        UserTask.objects.create(
            user_task_id=str(uuid.uuid4()),
            user=user,
            task_name='mao',
        )

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
        # user = request.user  # 原逻辑：从 token 取用户
        # 临时兼容：优先 token，取不到则从请求体 user_phone_number 查询
        user = get_user_from_request(request)
        if user is None:
            return error_response('用户不存在或未提供身份信息', status_code=status.HTTP_200_OK, result='unexit')

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
                return error_response('用户不存在', status_code=status.HTTP_200_OK, result='unexist')

            if login_type == 'password':
                if not check_password(user_password, user.user_password):
                    return error_response('密码错误', status_code=status.HTTP_200_OK, result='wrongPassword')
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

            # 返回用户信息 + Token，附带 pet_model_id 供前端判断 3D 模型是否生成完成
            task = UserTask.objects.filter(user=user).first()
            user_data = UserSerializer(user).data
            user_data['pet_model_id'] = task.pet_model_id if task else 0
            data = {
                'user': user_data,
                'token': token_data,
            }

            return success_response(data, message='登录成功')

        # GET：查询用户信息
        # 临时兼容：优先 token，取不到则从 query 参数 user_phone_number 查询
        # request_user = request.user  # 原逻辑：从 token 取当前用户，再做归属校验
        request_user = get_user_from_request(request)
        if request_user is None:
            return error_response('用户不存在或未提供身份信息', status_code=status.HTTP_200_OK, result='unexit')

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

        # user, denied = get_owned_object_or_403(  # 原逻辑：归属校验基于 request.user
        #     request,
        #     User.objects.all(),
        #     not_found_msg='用户不存在',
        #     **filters,
        # )
        # if denied:
        #     return denied
        # 临时兼容：用解析出的 request_user 做归属校验
        user = User.objects.filter(**filters).first()
        if user is None:
            return error_response('用户不存在', status_code=status.HTTP_200_OK, result='unexit')
        if user.user_id != request_user.user_id:
            return error_response('无权限', status_code=status.HTTP_403_FORBIDDEN)

        # 取该用户预创建的任务记录，附带 pet_model_id 供前端判断 3D 模型是否生成完成
        task = UserTask.objects.filter(user=user).first()
        data = UserSerializer(user).data
        data['pet_model_id'] = task.pet_model_id if task else 0
        return success_response(data, message='查询成功')

    @action(detail=False, methods=['get'], url_path='dirUserStatus')
    def dir_user_status(self, request):
        """
        查询当前用户状态接口，仅返回 user_status。
        GET /api/users/dirUserStatus/
        临时兼容：优先 token，取不到则从 query 参数 user_phone_number 查询。
        """
        user = get_user_from_request(request)
        if user is None:
            return error_response('用户不存在或未提供身份信息', status_code=status.HTTP_200_OK, result='unexit')

        return success_response({'user_status': user.user_status}, message='查询成功')


# 测试页面已改为TemplateView
