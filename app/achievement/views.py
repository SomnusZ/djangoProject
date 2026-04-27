"""
成就视图文件。
包含成就相关接口：createAchievement（新增）、updateAchievement（修改）、dirAchievement（查询）、dirAchievementList（列表）。
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from app.permissions import IsAdminUser
from app.utils import success_response, error_response

from .models import Achievement
from .serializers import (
    AchievementSerializer,
    CreateAchievementSerializer,
    UpdateAchievementSerializer,
    DirAchievementQuerySerializer,
)


class AchievementViewSet(viewsets.GenericViewSet):
    """
    成就接口视图集。
    包含成就新增、修改、查询。
    所有接口均需登录（IsAuthenticated）。
    """

    queryset = Achievement.objects.all()
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='createAchievement',
            permission_classes=[IsAdminUser])
    def create_achievement(self, request):
        """
        新增成就接口。
        achievement_name 全局唯一，重复时返回 400。
        请求体示例：
        {
            "achievement_name": "首次登录"
        }
        """
        serializer = CreateAchievementSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        achievement_obj = serializer.save()
        return success_response(
            AchievementSerializer(achievement_obj).data,
            message='创建成功',
            status_code=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['put', 'patch'], url_path='updateAchievement',
            permission_classes=[IsAdminUser])
    def update_achievement(self, request):
        """
        修改成就接口。
        通过 achievement_id 定位记录，仅允许修改 achievement_name。
        请求体示例：
        {
            "achievement_id": 1,
            "achievement_name": "连续签到7天"
        }
        """
        achievement_id = request.data.get('achievement_id')
        if not achievement_id:
            return error_response('请提供 achievement_id', status_code=status.HTTP_400_BAD_REQUEST)

        achievement_obj = Achievement.objects.filter(achievement_id=achievement_id).first()
        if not achievement_obj:
            return error_response('成就不存在', status_code=status.HTTP_404_NOT_FOUND)

        # 排除定位字段，避免序列化器报错
        update_data = request.data.copy()
        update_data.pop('achievement_id', None)

        serializer = UpdateAchievementSerializer(achievement_obj, data=update_data, partial=True)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return success_response(AchievementSerializer(achievement_obj).data, message='修改成功')

    @action(detail=False, methods=['get'], url_path='dirAchievement')
    def dir_achievement(self, request):
        """
        查询成就信息接口。
        通过 achievement_id 查询单条记录。
        查询参数示例：
        /api/achievement/dirAchievement/?achievement_id=1
        """
        serializer = DirAchievementQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        achievement_id = serializer.validated_data['achievement_id']
        achievement_obj = Achievement.objects.filter(achievement_id=achievement_id).first()
        if not achievement_obj:
            return error_response('成就不存在', status_code=status.HTTP_404_NOT_FOUND)

        return success_response(AchievementSerializer(achievement_obj).data, message='查询成功')

    @action(detail=False, methods=['get'], url_path='dirAchievementList')
    def dir_achievement_list(self, request):
        """
        查询所有成就列表。
        GET /api/achievement/dirAchievementList/
        """
        achievements = Achievement.objects.all().order_by('achievement_id')
        return success_response(AchievementSerializer(achievements, many=True).data, message='查询成功')
