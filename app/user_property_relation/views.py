"""
用户属性关联视图文件。
包含属性与用户的绑定、解绑、按用户查询属性列表。
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action

from app.utils import success_response, error_response
from app.permissions import OwnedObjectMixin, OwnedQuerySetMixin

from .models import UserPropertyRelation
from .serializers import (
    UserPropertyRelationSerializer,
    BindPropertyToUserSerializer,
    UnbindPropertyFromUserSerializer,
)


class UserPropertyRelationViewSet(OwnedQuerySetMixin, OwnedObjectMixin, viewsets.GenericViewSet):
    """
    用户属性关联接口视图集。
    包含绑定、解绑、按用户查询属性列表。
    归属校验：关联记录通过 user 字段归属于当前登录用户。
    """

    queryset = UserPropertyRelation.objects.all()
    owner_field = 'user'

    @action(detail=False, methods=['post'], url_path='bindPropertyToUser')
    def bind_property_to_user(self, request):
        """
        绑定属性到当前登录用户。
        绑定后初始数值为 0，后续通过专用接口更新数值。
        同一用户对同一属性只允许存在一条绑定记录。
        请求体示例：
        {
            "property_id": 1
        }
        """
        serializer = BindPropertyToUserSerializer(
            data=request.data,
            context={'user': request.user},
        )
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        relation = serializer.save()
        return success_response(
            UserPropertyRelationSerializer(relation).data,
            message='绑定成功',
            status_code=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['post'], url_path='unbindPropertyFromUser')
    def unbind_property_from_user(self, request):
        """
        解绑当前登录用户与属性的关联。
        请求体示例：
        {
            "property_id": 1
        }
        """
        serializer = UnbindPropertyFromUserSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        property_id = serializer.validated_data['property_id']

        relation = UserPropertyRelation.objects.filter(
            user=request.user,
            property_id=property_id,
        ).first()
        if not relation:
            return error_response('关联不存在', status_code=status.HTTP_404_NOT_FOUND)

        relation.delete()
        return success_response(
            {'property_id': property_id},
            message='解绑成功',
        )

    @action(detail=False, methods=['get'], url_path='dirPropertyListByUser')
    def dir_property_list_by_user(self, request):
        """
        查询当前登录用户名下所有属性关联列表。
        返回每条关联的 relation_id、property_id、property_name、property_amount。
        查询参数示例：
        /api/user-property/dirPropertyListByUser/
        """
        relations_qs = self.get_queryset().select_related('property').order_by('-relation_id')
        data = UserPropertyRelationSerializer(relations_qs, many=True).data
        return success_response(data, message='查询成功')
