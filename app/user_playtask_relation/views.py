"""
用户玩法任务关联视图文件。
包含玩法任务与用户的绑定、解绑、按用户查询玩法任务列表。
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action

from app.utils import success_response, error_response
from app.permissions import OwnedObjectMixin, OwnedQuerySetMixin

from .models import UserPlaytaskRelation
from .serializers import (
    UserPlaytaskRelationSerializer,
    BindPlaytaskToUserSerializer,
    UnbindPlaytaskFromUserSerializer,
)


class UserPlaytaskRelationViewSet(OwnedQuerySetMixin, OwnedObjectMixin, viewsets.GenericViewSet):
    """
    用户玩法任务关联接口视图集。
    包含绑定、解绑、按用户查询玩法任务列表。
    归属校验：关联记录通过 user 字段归属于当前登录用户。
    """

    queryset = UserPlaytaskRelation.objects.all()
    owner_field = 'user'

    @action(detail=False, methods=['post'], url_path='bindPlaytaskToUser')
    def bind_playtask_to_user(self, request):
        """
        绑定玩法任务到当前登录用户。
        绑定后初始进度为 0，后续通过专用接口更新进度。
        同一用户对同一玩法任务只允许存在一条绑定记录。
        请求体示例：
        {
            "playtask_id": 1
        }
        """
        serializer = BindPlaytaskToUserSerializer(
            data=request.data,
            context={'user': request.user},
        )
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        relation = serializer.save()
        return success_response(
            UserPlaytaskRelationSerializer(relation).data,
            message='绑定成功',
            status_code=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['post'], url_path='unbindPlaytaskFromUser')
    def unbind_playtask_from_user(self, request):
        """
        解绑当前登录用户与玩法任务的关联。
        请求体示例：
        {
            "playtask_id": 1
        }
        """
        serializer = UnbindPlaytaskFromUserSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        playtask_id = serializer.validated_data['playtask_id']

        relation = UserPlaytaskRelation.objects.filter(
            user=request.user,
            playtask_id=playtask_id,
        ).first()
        if not relation:
            return error_response('关联不存在', status_code=status.HTTP_404_NOT_FOUND)

        relation.delete()
        return success_response(
            {'playtask_id': playtask_id},
            message='解绑成功',
        )

    @action(detail=False, methods=['get'], url_path='dirPlaytaskListByUser')
    def dir_playtask_list_by_user(self, request):
        """
        查询当前登录用户名下所有玩法任务关联列表。
        返回每条关联的 relation_id、playtask_id、playtask_name、playtask_progress。
        查询参数示例：
        /api/user-playtask/dirPlaytaskListByUser/
        """
        relations_qs = self.get_queryset().select_related('playtask').order_by('-relation_id')
        data = UserPlaytaskRelationSerializer(relations_qs, many=True).data
        return success_response(data, message='查询成功')
