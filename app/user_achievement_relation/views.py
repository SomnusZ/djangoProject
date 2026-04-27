"""
用户成就关联视图文件。
包含成就与用户的绑定（解锁）、解绑（撤销）、按用户查询成就列表。
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action

from app.utils import success_response, error_response
from app.permissions import OwnedObjectMixin, OwnedQuerySetMixin

from .models import UserAchievementRelation
from .serializers import (
    UserAchievementRelationSerializer,
    BindAchievementToUserSerializer,
    UnbindAchievementFromUserSerializer,
)


class UserAchievementRelationViewSet(OwnedQuerySetMixin, OwnedObjectMixin, viewsets.GenericViewSet):
    """
    用户成就关联接口视图集。
    包含解锁成就、撤销成就、按用户查询成就列表。
    归属校验：关联记录通过 user 字段归属于当前登录用户。
    """

    queryset = UserAchievementRelation.objects.all()
    owner_field = 'user'

    @action(detail=False, methods=['post'], url_path='bindAchievementToUser')
    def bind_achievement_to_user(self, request):
        """
        解锁成就（绑定成就到当前登录用户）。
        同一用户对同一成就只允许存在一条绑定记录，重复解锁返回 400。
        请求体示例：
        {
            "achievement_id": 1
        }
        """
        serializer = BindAchievementToUserSerializer(
            data=request.data,
            context={'user': request.user},
        )
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        relation = serializer.save()
        return success_response(
            UserAchievementRelationSerializer(relation).data,
            message='成就解锁成功',
            status_code=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['post'], url_path='unbindAchievementFromUser')
    def unbind_achievement_from_user(self, request):
        """
        撤销成就（解绑当前登录用户与成就的关联）。
        请求体示例：
        {
            "achievement_id": 1
        }
        """
        serializer = UnbindAchievementFromUserSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        achievement_id = serializer.validated_data['achievement_id']

        relation = UserAchievementRelation.objects.filter(
            user=request.user,
            achievement_id=achievement_id,
        ).first()
        if not relation:
            return error_response('关联不存在', status_code=status.HTTP_404_NOT_FOUND)

        relation.delete()
        return success_response(
            {'achievement_id': achievement_id},
            message='成就撤销成功',
        )

    @action(detail=False, methods=['get'], url_path='dirAchievementListByUser')
    def dir_achievement_list_by_user(self, request):
        """
        查询当前登录用户已解锁的所有成就列表。
        返回每条关联的 relation_id、achievement_id、achievement_name。
        查询参数示例：
        /api/user-achievement/dirAchievementListByUser/
        """
        relations_qs = self.get_queryset().select_related('achievement').order_by('-relation_id')
        data = UserAchievementRelationSerializer(relations_qs, many=True).data
        return success_response(data, message='查询成功')
