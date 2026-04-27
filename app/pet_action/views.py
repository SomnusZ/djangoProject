"""
动作视图文件。
包含动作相关接口：createAction、updateAction、dirAction、dirActionList。
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from app.permissions import IsAdminUser
from app.utils import success_response, error_response

from .models import PetAction
from .serializers import (
    PetActionSerializer,
    CreatePetActionSerializer,
    UpdatePetActionSerializer,
    DirActionQuerySerializer,
)


class PetActionViewSet(viewsets.GenericViewSet):
    """
    动作接口视图集。
    包含动作新增、查询。
    """

    queryset = PetAction.objects.all()
    permission_classes = [IsAuthenticated]  # 查询等普通接口默认需登录

    @action(detail=False, methods=['post'], url_path='createAction',
            permission_classes=[IsAdminUser])
    def create_action(self, request):
        """
        动作新增接口。
        请求体示例：
        {
            "pet_action_name": "sit"
        }
        """
        serializer = CreatePetActionSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        action_obj = serializer.save()
        return success_response(PetActionSerializer(action_obj).data, message='创建成功', status_code=status.HTTP_201_CREATED)

    @action(detail=False, methods=['put', 'patch'], url_path='updateAction',
            permission_classes=[IsAdminUser])
    def update_action(self, request):
        """
        修改动作接口。
        通过 pet_action_id 定位记录，仅允许修改 pet_action_name。
        请求体示例：
        {
            "pet_action_id": 1,
            "pet_action_name": "jump"
        }
        """
        pet_action_id = request.data.get('pet_action_id')
        if not pet_action_id:
            return error_response('请提供 pet_action_id', status_code=status.HTTP_400_BAD_REQUEST)

        action_obj = PetAction.objects.filter(pet_action_id=pet_action_id).first()
        if not action_obj:
            return error_response('动作不存在', status_code=status.HTTP_404_NOT_FOUND)

        update_data = request.data.copy()
        update_data.pop('pet_action_id', None)

        serializer = UpdatePetActionSerializer(action_obj, data=update_data, partial=True)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return success_response(PetActionSerializer(action_obj).data, message='修改成功')

    @action(detail=False, methods=['get'], url_path='dirAction')
    def dir_action(self, request):
        """
        动作信息查询接口（单个）。
        查询参数示例：
        /api/actions/dirAction/?pet_action_id=1
        """
        serializer = DirActionQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        pet_action_id = serializer.validated_data['pet_action_id']
        action_obj = PetAction.objects.filter(pet_action_id=pet_action_id).first()
        if not action_obj:
            return error_response('动作不存在', status_code=status.HTTP_404_NOT_FOUND)

        return success_response(PetActionSerializer(action_obj).data, message='查询成功')

    @action(detail=False, methods=['get'], url_path='dirActionList')
    def dir_action_list(self, request):
        """
        查询所有动作列表。
        GET /api/actions/dirActionList/
        """
        actions = PetAction.objects.all().order_by('pet_action_id')
        return success_response(PetActionSerializer(actions, many=True).data, message='查询成功')
