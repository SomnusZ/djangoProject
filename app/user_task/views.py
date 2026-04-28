"""
用户任务视图文件。
包含任务相关接口：createUserTask、updateUserTask、dirUserTask、dirUserTaskListByUser。
AI 宠物工作流接口：createUserTask（含图片预处理+Meshy提交）、queryMeshyTask。
"""

import uuid

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser

from app.utils import success_response, error_response
from app.permissions import IsOwnerPermission, OwnedObjectMixin, OwnedQuerySetMixin

from .models import UserTask
from .serializers import (
    UserTaskSerializer,
    UpdateUserTaskSerializer,
    DirUserTaskQuerySerializer,
)

from aipet.task_workflow import preprocess_image
from aipet.task_workflow import meshy as workflow_meshy
from aipet.task_workflow import meshy_status as workflow_meshy_status

# 工作流涉及的所有数据库字段，view 层统一用这个列表做 update_fields
_WORKFLOW_FIELDS = [
    'workflow_status', 'image_path', 'pet_breed', 'pet_type',
    'meshy_job_id', 'meshy_retry_count', 'texture_clean_path', 'workflow_error',
]


class UserTaskViewSet(OwnedQuerySetMixin, OwnedObjectMixin, viewsets.GenericViewSet):
    """
    用户任务接口视图集。
    """

    queryset = UserTask.objects.all()
    permission_classes = [IsOwnerPermission]
    owner_field = 'user'

    @action(detail=False, methods=['post'], url_path='createUserTask',
            parser_classes=[MultiPartParser])
    def create_user_task(self, request):
        """
        创建用户任务并启动 AI 宠物生成流程。
        流程：图片预处理成功 → 写库 → 提交 Meshy
        预处理失败时不写库，用户可直接重新上传。

        表单字段：
          - task_name: 任务名称（string）
          - image:     宠物图片（file，≤5MB）
        """
        task_name = request.data.get('task_name', '').strip()
        if not task_name:
            return error_response('请提供 task_name', status_code=status.HTTP_400_BAD_REQUEST)

        image_file = request.FILES.get('image')
        if not image_file:
            return error_response('请上传 image 文件', status_code=status.HTTP_400_BAD_REQUEST)
        if not image_file.content_type.startswith('image/'):
            return error_response('只支持图片文件', status_code=status.HTTP_400_BAD_REQUEST)
        if image_file.size > 5 * 1024 * 1024:
            return error_response('图片不能超过 5MB', status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

        # 同一用户下 task_name 唯一性校验
        if UserTask.objects.filter(user=request.user, task_name=task_name).exists():
            return error_response('任务名已存在', status_code=status.HTTP_409_CONFLICT)

        # ① 预先生成 task_id，CleanPic 输出文件以此命名
        task_id = str(uuid.uuid4())
        file_bytes = image_file.read()

        # ② 图片预处理（在写库之前）
        ok, clean_data = preprocess_image(task_id, file_bytes)
        if not ok:
            code = clean_data.get('code', '')
            if code == 'no_pet_detected':
                return error_response(clean_data['detail'], status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
            return error_response(clean_data['detail'], status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # ③ 预处理成功，创建 UserTask 记录
        task_obj = UserTask.objects.create(
            user_task_id=task_id,
            user=request.user,
            task_name=task_name,
            workflow_status='cleaned',
            image_path=clean_data['image_path'],
            pet_breed=clean_data['pet_breed'],
            pet_type=clean_data['pet_type'],
        )

        # ④ 提交 Meshy
        ok, meshy_data = workflow_meshy(task_obj)
        task_obj.save(update_fields=_WORKFLOW_FIELDS)

        if not ok:
            # Meshy 提交失败，任务已创建但状态为 ERROR，客户端可查询得知原因
            return error_response(meshy_data['detail'], status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return success_response({
            'task_id':         task_obj.user_task_id,
            'task_name':       task_obj.task_name,
            'workflow_status': task_obj.workflow_status,
            'meshy_job_id':    task_obj.meshy_job_id,
            'pet_breed':       task_obj.pet_breed,
            'pet_type':        task_obj.pet_type,
        }, message='任务创建成功', status_code=status.HTTP_201_CREATED)

    @action(detail=False, methods=['put', 'patch'], url_path='updateUserTask')
    def update_user_task(self, request):
        """
        用户任务修改接口。
        仅允许修改 task_name。
        请求体示例：
        {
            "user_task_id": "uuid-string",
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
        /api/models/dirUserTask/?user_task_id=uuid-string
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
        查询当前登录用户的任务列表接口（按创建时间倒序）。
        """
        tasks_qs = self.get_queryset().order_by('-created_at')
        data = UserTaskSerializer(tasks_qs, many=True).data
        return success_response(data, message='查询成功')

    @action(detail=False, methods=['get'], url_path='queryMeshyTask')
    def query_meshy_task(self, request):
        """
        轮询 Meshy 任务状态，推进工作流直到完成。
        查询参数：
          /api/models/queryMeshyTask/?user_task_id=uuid-string
        """
        user_task_id = request.query_params.get('user_task_id')
        if not user_task_id:
            return error_response('请提供 user_task_id', status_code=status.HTTP_400_BAD_REQUEST)

        task_obj, denied = self.get_owned_or_403(
            request, self.get_queryset(),
            not_found_msg='任务不存在',
            user_task_id=user_task_id,
        )
        if denied:
            return denied

        ok, data = workflow_meshy_status(task_obj)
        task_obj.save(update_fields=_WORKFLOW_FIELDS)

        if not ok:
            return error_response(data['detail'], status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return success_response(data, message='查询成功')
