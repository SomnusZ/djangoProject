"""
模型视图文件。
包含模型相关接口：dirModel、dirModelListByUser、updateModel、createModel。
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action

from app.utils import success_response, error_response
from app.permissions import IsOwnerPermission, OwnedObjectMixin, OwnedQuerySetMixin

from .models import PetModel
from .serializers import (
    PetModelSerializer,
    CreatePetModelSerializer,
    UpdatePetModelSerializer,
    DirModelQuerySerializer,
)


class PetModelViewSet(OwnedQuerySetMixin, OwnedObjectMixin, viewsets.GenericViewSet):
    """
    模型接口视图集。
    包含模型新增、查询、修改，以及按用户查询模型列表。
    """

    queryset = PetModel.objects.all()
    # 统一归属权限控制
    permission_classes = [IsOwnerPermission]
    # 归属字段（当前用户）
    owner_field = 'user'

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
        # 只允许使用当前登录用户创建
        data = request.data.copy()
        data['user_id'] = getattr(request.user, 'user_id', None)

        serializer = CreatePetModelSerializer(data=data)
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

        model_obj, denied = self.get_owned_or_403(
            request,
            self.get_queryset(),
            not_found_msg='模型不存在',
            user_task_id=user_task_id,
        )
        if denied:
            return denied

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
        model_obj, denied = self.get_owned_or_403(
            request,
            self.get_queryset(),
            not_found_msg='模型不存在',
            user_task_id=user_task_id,
        )
        if denied:
            return denied

        return success_response(PetModelSerializer(model_obj).data, message='查询成功')

    @action(detail=False, methods=['get'], url_path='dirModelListByUser')
    def dir_model_list_by_user(self, request):
        """
        查询当前登录用户的模型列表接口。
        查询参数示例：
        /api/models/dirModelListByUser/
        """
        models_qs = self.get_queryset().order_by('-user_task_id')
        data = PetModelSerializer(models_qs, many=True).data
        return success_response(data, message='查询成功')
