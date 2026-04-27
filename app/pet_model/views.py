"""
宠物模型视图文件。
包含模型相关接口：createModel、updateModel、dirModel、dirModelList。
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from app.permissions import IsAdminUser
from app.utils import success_response, error_response

from .models import PetModel
from .serializers import (
    PetModelSerializer,
    CreatePetModelSerializer,
    UpdatePetModelSerializer,
    DirModelQuerySerializer,
)


class PetModelViewSet(viewsets.GenericViewSet):
    """
    宠物模型接口视图集。
    包含模型新增、查询。
    """

    queryset = PetModel.objects.all()
    permission_classes = [IsAuthenticated]  # 查询等普通接口默认需登录

    @action(detail=False, methods=['post'], url_path='createModel',
            permission_classes=[IsAdminUser])
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

    @action(detail=False, methods=['put', 'patch'], url_path='updateModel',
            permission_classes=[IsAdminUser])
    def update_model(self, request):
        """
        修改宠物模型接口。
        通过 pet_model_id 定位记录，仅允许修改 pet_model_name。
        请求体示例：
        {
            "pet_model_id": 1,
            "pet_model_name": "dog"
        }
        """
        pet_model_id = request.data.get('pet_model_id')
        if not pet_model_id:
            return error_response('请提供 pet_model_id', status_code=status.HTTP_400_BAD_REQUEST)

        model_obj = PetModel.objects.filter(pet_model_id=pet_model_id).first()
        if not model_obj:
            return error_response('模型不存在', status_code=status.HTTP_404_NOT_FOUND)

        update_data = request.data.copy()
        update_data.pop('pet_model_id', None)

        serializer = UpdatePetModelSerializer(model_obj, data=update_data, partial=True)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return success_response(PetModelSerializer(model_obj).data, message='修改成功')

    @action(detail=False, methods=['get'], url_path='dirModel')
    def dir_model(self, request):
        """
        模型信息查询接口（单个）。
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

    @action(detail=False, methods=['get'], url_path='dirModelList')
    def dir_model_list(self, request):
        """
        查询所有宠物模型列表。
        GET /api/pet-models/dirModelList/
        """
        models = PetModel.objects.all().order_by('pet_model_id')
        return success_response(PetModelSerializer(models, many=True).data, message='查询成功')
