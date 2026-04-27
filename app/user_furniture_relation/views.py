"""
用户家具关联视图文件。
包含家具与用户的绑定、解绑、按用户查询家具列表。
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action

from app.utils import success_response, error_response
from app.permissions import OwnedObjectMixin, OwnedQuerySetMixin

from .models import UserFurnitureRelation
from .serializers import (
    UserFurnitureRelationSerializer,
    BindFurnitureToUserSerializer,
    UnbindFurnitureFromUserSerializer,
)


class UserFurnitureRelationViewSet(OwnedQuerySetMixin, OwnedObjectMixin, viewsets.GenericViewSet):
    """
    用户家具关联接口视图集。
    包含绑定、解绑、按用户查询家具列表。
    归属校验：关联记录通过 user 字段归属于当前登录用户。
    """

    queryset = UserFurnitureRelation.objects.all()
    owner_field = 'user'

    @action(detail=False, methods=['post'], url_path='bindFurnitureToUser')
    def bind_furniture_to_user(self, request):
        """
        绑定家具到当前登录用户。
        绑定后初始数量为 0，后续通过专用接口更新数量。
        同一用户对同一家具只允许存在一条绑定记录。
        请求体示例：
        {
            "furniture_id": 1
        }
        """
        serializer = BindFurnitureToUserSerializer(
            data=request.data,
            context={'user': request.user},
        )
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        relation = serializer.save()
        return success_response(
            UserFurnitureRelationSerializer(relation).data,
            message='绑定成功',
            status_code=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['post'], url_path='unbindFurnitureFromUser')
    def unbind_furniture_from_user(self, request):
        """
        解绑当前登录用户与家具的关联。
        请求体示例：
        {
            "furniture_id": 1
        }
        """
        serializer = UnbindFurnitureFromUserSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        furniture_id = serializer.validated_data['furniture_id']

        relation = UserFurnitureRelation.objects.filter(
            user=request.user,
            furniture_id=furniture_id,
        ).first()
        if not relation:
            return error_response('关联不存在', status_code=status.HTTP_404_NOT_FOUND)

        relation.delete()
        return success_response(
            {'furniture_id': furniture_id},
            message='解绑成功',
        )

    @action(detail=False, methods=['get'], url_path='dirFurnitureListByUser')
    def dir_furniture_list_by_user(self, request):
        """
        查询当前登录用户名下所有家具关联列表。
        返回每条关联的 relation_id、furniture_id、furniture_name、furniture_amount。
        查询参数示例：
        /api/user-furniture/dirFurnitureListByUser/
        """
        relations_qs = self.get_queryset().select_related('furniture').order_by('-relation_id')
        data = UserFurnitureRelationSerializer(relations_qs, many=True).data
        return success_response(data, message='查询成功')
