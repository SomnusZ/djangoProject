"""
动作视图文件。
包含动作相关接口：dirAction、createAction。
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action

from app.utils import success_response, error_response

from .models import PetAction
from .serializers import (
    PetActionSerializer,
    CreatePetActionSerializer,
    DirActionQuerySerializer,
)


class PetActionViewSet(viewsets.GenericViewSet):
    """
    动作接口视图集。
    包含动作新增、查询。
    """

    queryset = PetAction.objects.all()

    @action(detail=False, methods=['post'], url_path='createAction')
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

    @action(detail=False, methods=['get'], url_path='dirAction')
    def dir_action(self, request):
        """
        动作信息查询接口。
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
