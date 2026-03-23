"""
宠物模型视图文件。
包含模型相关接口：createModel、dirModel。
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action

from app.utils import success_response, error_response

from .models import PetModel
from .serializers import (
    PetModelSerializer,
    CreatePetModelSerializer,
    DirModelQuerySerializer,
)


class PetModelViewSet(viewsets.GenericViewSet):
    """
    宠物模型接口视图集。
    包含模型新增、查询。
    """

    queryset = PetModel.objects.all()

    @action(detail=False, methods=['post'], url_path='createModel')
    def create_model(self, request):
        """
        模型新增接口。
        请求体示例：
        {
            "pet_model_name": "cat"
        }
        """
        serializer = CreatePetModelSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        model_obj = serializer.save()
        return success_response(PetModelSerializer(model_obj).data, message='创建成功', status_code=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='dirModel')
    def dir_model(self, request):
        """
        模型信息查询接口。
        查询参数示例：
        /api/pet-models/dirModel/?pet_model_id=1
        """
        serializer = DirModelQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        pet_model_id = serializer.validated_data['pet_model_id']
        model_obj = PetModel.objects.filter(pet_model_id=pet_model_id).first()
        if not model_obj:
            return error_response('模型不存在', status_code=status.HTTP_404_NOT_FOUND)

        return success_response(PetModelSerializer(model_obj).data, message='查询成功')
