"""
玩法任务视图文件。
包含玩法任务相关接口：createPlaytask（新增）、updatePlaytask（修改）、dirPlaytask（查询）。
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from app.permissions import IsAdminUser
from app.utils import success_response, error_response

from .models import Playtask
from .serializers import (
    PlaytaskSerializer,
    CreatePlaytaskSerializer,
    UpdatePlaytaskSerializer,
    DirPlaytaskQuerySerializer,
)


class PlaytaskViewSet(viewsets.GenericViewSet):
    """
    玩法任务接口视图集。
    包含玩法任务新增、修改、查询。
    所有接口均需登录（IsAuthenticated）。
    """

    queryset = Playtask.objects.all()
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='createPlaytask',
            permission_classes=[IsAdminUser])
    def create_playtask(self, request):
        """
        新增玩法任务接口。
        playtask_name 全局唯一，重复时返回 400。
        请求体示例：
        {
            "playtask_name": "每日签到"
        }
        """
        serializer = CreatePlaytaskSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        playtask_obj = serializer.save()
        return success_response(
            PlaytaskSerializer(playtask_obj).data,
            message='创建成功',
            status_code=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['put', 'patch'], url_path='updatePlaytask',
            permission_classes=[IsAdminUser])
    def update_playtask(self, request):
        """
        修改玩法任务接口。
        通过 playtask_id 定位记录，仅允许修改 playtask_name。
        请求体示例：
        {
            "playtask_id": 1,
            "playtask_name": "每周打卡"
        }
        """
        playtask_id = request.data.get('playtask_id')
        if not playtask_id:
            return error_response('请提供 playtask_id', status_code=status.HTTP_400_BAD_REQUEST)

        playtask_obj = Playtask.objects.filter(playtask_id=playtask_id).first()
        if not playtask_obj:
            return error_response('玩法任务不存在', status_code=status.HTTP_404_NOT_FOUND)

        # 排除定位字段，避免序列化器报错
        update_data = request.data.copy()
        update_data.pop('playtask_id', None)

        serializer = UpdatePlaytaskSerializer(playtask_obj, data=update_data, partial=True)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return success_response(PlaytaskSerializer(playtask_obj).data, message='修改成功')

    @action(detail=False, methods=['get'], url_path='dirPlaytask')
    def dir_playtask(self, request):
        """
        查询玩法任务信息接口。
        通过 playtask_id 查询单条记录。
        查询参数示例：
        /api/playtask/dirPlaytask/?playtask_id=1
        """
        serializer = DirPlaytaskQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        playtask_id = serializer.validated_data['playtask_id']
        playtask_obj = Playtask.objects.filter(playtask_id=playtask_id).first()
        if not playtask_obj:
            return error_response('玩法任务不存在', status_code=status.HTTP_404_NOT_FOUND)

        return success_response(PlaytaskSerializer(playtask_obj).data, message='查询成功')

    @action(detail=False, methods=['get'], url_path='dirPlaytaskList')
    def dir_playtask_list(self, request):
        """
        查询所有玩法任务列表。
        GET /api/playtask/dirPlaytaskList/
        """
        playtasks = Playtask.objects.all().order_by('playtask_id')
        return success_response(PlaytaskSerializer(playtasks, many=True).data, message='查询成功')
