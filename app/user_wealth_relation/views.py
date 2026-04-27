"""
用户货币资产关联视图文件。
包含货币资产与用户的绑定、解绑、按用户查询货币资产列表。
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action

from app.utils import success_response, error_response
from app.permissions import OwnedObjectMixin, OwnedQuerySetMixin

from .models import UserWealthRelation
from .serializers import (
    UserWealthRelationSerializer,
    BindWealthToUserSerializer,
    UnbindWealthFromUserSerializer,
)


class UserWealthRelationViewSet(OwnedQuerySetMixin, OwnedObjectMixin, viewsets.GenericViewSet):
    """
    用户货币资产关联接口视图集。
    包含绑定、解绑、按用户查询货币资产列表。
    归属校验：关联记录通过 user 字段归属于当前登录用户。
    """

    queryset = UserWealthRelation.objects.all()
    owner_field = 'user'

    @action(detail=False, methods=['post'], url_path='bindWealthToUser')
    def bind_wealth_to_user(self, request):
        """
        绑定货币资产到当前登录用户。
        绑定后初始数量为 0，后续通过专用接口修改数量。
        同一用户对同一货币资产只允许存在一条绑定记录。
        请求体示例：
        {
            "wealth_id": 1
        }
        """
        serializer = BindWealthToUserSerializer(
            data=request.data,
            context={'user': request.user},
        )
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        relation = serializer.save()
        return success_response(
            UserWealthRelationSerializer(relation).data,
            message='绑定成功',
            status_code=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['post'], url_path='unbindWealthFromUser')
    def unbind_wealth_from_user(self, request):
        """
        解绑当前登录用户与货币资产的关联。
        请求体示例：
        {
            "wealth_id": 1
        }
        """
        serializer = UnbindWealthFromUserSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        wealth_id = serializer.validated_data['wealth_id']

        relation = UserWealthRelation.objects.filter(
            user=request.user,
            wealth_id=wealth_id,
        ).first()
        if not relation:
            return error_response('关联不存在', status_code=status.HTTP_404_NOT_FOUND)

        relation.delete()
        return success_response(
            {'wealth_id': wealth_id},
            message='解绑成功',
        )

    @action(detail=False, methods=['get'], url_path='dirWealthListByUser')
    def dir_wealth_list_by_user(self, request):
        """
        查询当前登录用户名下所有货币资产关联列表。
        返回每条关联的 relation_id、wealth_id、wealth_name、wealth_amount。
        查询参数示例：
        /api/user-wealth/dirWealthListByUser/
        """
        relations_qs = self.get_queryset().select_related('wealth').order_by('-relation_id')
        data = UserWealthRelationSerializer(relations_qs, many=True).data
        return success_response(data, message='查询成功')
