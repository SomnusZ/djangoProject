"""
模型视图文件。
包含模型相关接口：dirModel、dirModelListByUser、updateModel、createModel。
"""

from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action

from app.user.models import User
from app.utils import success_response, error_response

from .models import PetModel
from .serializers import (
    PetModelSerializer,
    CreatePetModelSerializer,
    UpdatePetModelSerializer,
    DirModelQuerySerializer,
    DirModelListByUserSerializer,
)


class PetModelViewSet(viewsets.GenericViewSet):
    """
    模型接口视图集。
    包含模型新增、查询、修改，以及按用户查询模型列表。
    """

    queryset = PetModel.objects.all()

    @action(detail=False, methods=['post'], url_path='createModel')
    def create_model(self, request):
        """
        模型新增接口。
        请求体示例：
        {
            "user_id": 1,
            "pet_model_id": 1,
            "model_name": "cat-v1",
            "model_address": "/models/cat-v1.bin"
        }
        """
        serializer = CreatePetModelSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        model_obj = serializer.save()
        return success_response(PetModelSerializer(model_obj).data, message='创建成功', status_code=status.HTTP_201_CREATED)

    @action(detail=False, methods=['put', 'patch'], url_path='updateModel')
    def update_model(self, request):
        """
        模型修改接口。
        仅允许修改 model_name。
        请求体示例：
        {
            "user_task_id": 1,
            "model_name": "cat-v2"
        }
        """
        user_task_id = request.data.get('user_task_id')
        if not user_task_id:
            return error_response('请提供 user_task_id', status_code=status.HTTP_400_BAD_REQUEST)

        model_obj = PetModel.objects.filter(user_task_id=user_task_id).first()
        if not model_obj:
            return error_response('模型不存在', status_code=status.HTTP_404_NOT_FOUND)

        # 移除仅用于定位的字段，避免序列化器报错
        update_data = request.data.copy()
        update_data.pop('user_task_id', None)
        update_data.pop('pet_model_id', None)

        serializer = UpdatePetModelSerializer(model_obj, data=update_data, partial=True)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return success_response(PetModelSerializer(model_obj).data, message='修改成功')

    @action(detail=False, methods=['get'], url_path='dirModel')
    def dir_model(self, request):
        """
        模型信息查询接口。
        查询参数示例：
        /api/models/dirModel/?user_task_id=1
        """
        serializer = DirModelQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        user_task_id = serializer.validated_data['user_task_id']
        model_obj = PetModel.objects.filter(user_task_id=user_task_id).first()
        if not model_obj:
            return error_response('模型不存在', status_code=status.HTTP_404_NOT_FOUND)

        return success_response(PetModelSerializer(model_obj).data, message='查询成功')

    @action(detail=False, methods=['get'], url_path='dirModelListByUser')
    def dir_model_list_by_user(self, request):
        """
        根据用户查询模型列表接口。
        查询参数示例：
        /api/models/dirModelListByUser/?user_id=1
        或
        /api/models/dirModelListByUser/?user_mail_address=test@example.com
        """
        serializer = DirModelListByUserSerializer(data=request.query_params)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        user_id = serializer.validated_data.get('user_id')
        user_mail_address = serializer.validated_data.get('user_mail_address')

        user = User.objects.filter(Q(user_id=user_id) | Q(user_mail_address=user_mail_address)).first()
        if not user:
            return error_response('用户不存在', status_code=status.HTTP_404_NOT_FOUND)

        models_qs = PetModel.objects.filter(user=user).order_by('-user_task_id')
        data = PetModelSerializer(models_qs, many=True).data
        return success_response(data, message='查询成功')
