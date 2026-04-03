"""
用户任务视图文件。
包含任务相关接口：createUserTask、updateUserTask、dirUserTask、dirUserTaskListByUser。
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action

from app.utils import success_response, error_response
from app.permissions import IsOwnerPermission, OwnedObjectMixin, OwnedQuerySetMixin

from .models import UserTask
from .serializers import (
    UserTaskSerializer,
    CreateUserTaskSerializer,
    UpdateUserTaskSerializer,
    DirUserTaskQuerySerializer,
)


class UserTaskViewSet(OwnedQuerySetMixin, OwnedObjectMixin, viewsets.GenericViewSet):
    """
    用户任务接口视图集。
    包含任务新增、查询、修改，以及按用户查询任务列表。
    """

    queryset = UserTask.objects.all()
    # 统一归属权限控制
    permission_classes = [IsOwnerPermission]
    # 归属字段（当前用户）
    owner_field = 'user'

    @action(detail=False, methods=['post'], url_path='createUserTask')
    def create_user_task(self, request):
        """
        用户任务新增接口。
        请求体示例：
        {
            "task_name": "我的任务"
        }
        """
        # 只允许使用当前登录用户创建
        data = request.data.copy()
        data['user_id'] = getattr(request.user, 'user_id', None)

        serializer = CreateUserTaskSerializer(data=data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        task_obj = serializer.save()
        return success_response(UserTaskSerializer(task_obj).data, message='创建成功', status_code=status.HTTP_201_CREATED)

    @action(detail=False, methods=['put', 'patch'], url_path='updateUserTask')
    def update_user_task(self, request):
        """
        用户任务修改接口。
        仅允许修改 task_name。
        请求体示例：
        {
            "user_task_id": 1,
            "task_name": "新的任务名"
        }
        """
        user_task_id = request.data.get('user_task_id')
        if not user_task_id:
            return error_response('请提供 user_task_id', status_code=status.HTTP_400_BAD_REQUEST)

        task_obj, denied = self.get_owned_or_403(
            request,
            self.get_queryset(),
            not_found_msg='任务不存在',
            user_task_id=user_task_id,
        )
        if denied:
            return denied

        # 移除仅用于定位的字段，避免序列化器报错
        update_data = request.data.copy()
        update_data.pop('user_task_id', None)

        serializer = UpdateUserTaskSerializer(task_obj, data=update_data, partial=True)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return success_response(UserTaskSerializer(task_obj).data, message='修改成功')

    @action(detail=False, methods=['get'], url_path='dirUserTask')
    def dir_user_task(self, request):
        """
        用户任务信息查询接口。
        查询参数示例：
        /api/models/dirUserTask/?user_task_id=1
        """
        serializer = DirUserTaskQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        user_task_id = serializer.validated_data['user_task_id']
        task_obj, denied = self.get_owned_or_403(
            request,
            self.get_queryset(),
            not_found_msg='任务不存在',
            user_task_id=user_task_id,
        )
        if denied:
            return denied

        return success_response(UserTaskSerializer(task_obj).data, message='查询成功')

    @action(detail=False, methods=['get'], url_path='dirUserTaskListByUser')
    def dir_user_task_list_by_user(self, request):
        """
        查询当前登录用户的任务列表接口。
        查询参数示例：
        /api/models/dirUserTaskListByUser/
        """
        tasks_qs = self.get_queryset().order_by('-user_task_id')
        data = UserTaskSerializer(tasks_qs, many=True).data
        return success_response(data, message='查询成功')
