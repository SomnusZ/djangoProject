"""
任务动作关系视图文件。
包含动作与任务的绑定、解绑、按任务查询动作列表。
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action

from app.utils import success_response, error_response
from app.permissions import OwnedObjectMixin, OwnedQuerySetMixin
from app.user_task.models import PetModel as UserTask
from app.pet_action.models import PetAction

from .models import UserTaskActionRelation
from .serializers import (
    BindActionToTaskSerializer,
    UnbindActionFromTaskSerializer,
    DirActionListByTaskSerializer,
)
from app.pet_action.serializers import PetActionSerializer


class UserTaskActionRelationViewSet(OwnedQuerySetMixin, OwnedObjectMixin, viewsets.GenericViewSet):
    """
    任务动作关系接口视图集。
    包含绑定动作到任务、解绑动作、按任务查询动作列表。
    """

    queryset = UserTaskActionRelation.objects.all()
    # 归属字段（通过 user_task 关联用户）
    owner_field = 'user_task__user'

    @action(detail=False, methods=['post'], url_path='bindActionToTask')
    def bind_action_to_task(self, request):
        """
        绑定动作到任务接口。
        请求体示例：
        {
            "user_task_id": 1,
            "pet_action_id": 2
        }
        """
        serializer = BindActionToTaskSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        # 只允许绑定到自己名下的任务
        user_task_id = serializer.validated_data['user_task_id']
        user_task, denied = self.get_owned_or_403(
            request,
            UserTask.objects.all(),
            not_found_msg='任务不存在',
            user_task_id=user_task_id,
        )
        if denied:
            return denied

        relation = serializer.save()
        if relation.user_task_id != getattr(user_task, 'user_task_id', None):
            return error_response('无权限', status_code=status.HTTP_403_FORBIDDEN)

        data = {
            'relation_id': relation.relation_id,
            'user_task_id': relation.user_task_id,
            'pet_action_id': relation.pet_action_id,
        }
        return success_response(data, message='绑定成功', status_code=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='unbindActionFromTask')
    def unbind_action_from_task(self, request):
        """
        解绑动作与任务接口。
        请求体示例：
        {
            "user_task_id": 1,
            "pet_action_id": 2
        }
        """
        serializer = UnbindActionFromTaskSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        # 只允许解绑自己名下的任务
        user_task_id = serializer.validated_data['user_task_id']
        user_task, denied = self.get_owned_or_403(
            request,
            UserTask.objects.all(),
            not_found_msg='任务不存在',
            user_task_id=user_task_id,
        )
        if denied:
            return denied

        pet_action_id = serializer.validated_data['pet_action_id']
        relation = UserTaskActionRelation.objects.filter(user_task=user_task, pet_action_id=pet_action_id).first()
        if not relation:
            return error_response('关联不存在', status_code=status.HTTP_404_NOT_FOUND)

        relation.delete()
        data = {
            'user_task_id': user_task_id,
            'pet_action_id': pet_action_id,
        }
        return success_response(data, message='解绑成功')

    @action(detail=False, methods=['get'], url_path='dirActionListByTask')
    def dir_action_list_by_task(self, request):
        """
        根据任务查询动作列表接口。
        查询参数示例：
        /api/task-actions/dirActionListByTask/?user_task_id=1
        """
        serializer = DirActionListByTaskSerializer(data=request.query_params)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        user_task_id = serializer.validated_data['user_task_id']
        user_task, denied = self.get_owned_or_403(
            request,
            UserTask.objects.all(),
            not_found_msg='任务不存在',
            user_task_id=user_task_id,
        )
        if denied:
            return denied

        action_ids = UserTaskActionRelation.objects.filter(user_task=user_task).values_list('pet_action_id', flat=True)
        actions_qs = PetAction.objects.filter(pet_action_id__in=action_ids).order_by('-pet_action_id')
        data = PetActionSerializer(actions_qs, many=True).data
        return success_response(data, message='查询成功')
