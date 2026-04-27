"""
家具视图文件。
包含家具相关接口：createFurniture（新增）、updateFurniture（修改）、dirFurniture（查询）、dirFurnitureList（列表）。
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from app.permissions import IsAdminUser
from app.utils import success_response, error_response

from .models import Furniture
from .serializers import (
    FurnitureSerializer,
    CreateFurnitureSerializer,
    UpdateFurnitureSerializer,
    DirFurnitureQuerySerializer,
)


class FurnitureViewSet(viewsets.GenericViewSet):
    """
    家具接口视图集。
    包含家具新增、修改、查询。
    所有接口均需登录（IsAuthenticated）。
    """

    queryset = Furniture.objects.all()
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='createFurniture',
            permission_classes=[IsAdminUser])
    def create_furniture(self, request):
        """
        新增家具接口。
        furniture_name 全局唯一，重复时返回 400。
        请求体示例：
        {
            "furniture_name": "木桌"
        }
        """
        serializer = CreateFurnitureSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        furniture_obj = serializer.save()
        return success_response(
            FurnitureSerializer(furniture_obj).data,
            message='创建成功',
            status_code=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['put', 'patch'], url_path='updateFurniture',
            permission_classes=[IsAdminUser])
    def update_furniture(self, request):
        """
        修改家具接口。
        通过 furniture_id 定位记录，仅允许修改 furniture_name。
        请求体示例：
        {
            "furniture_id": 1,
            "furniture_name": "实木书桌"
        }
        """
        furniture_id = request.data.get('furniture_id')
        if not furniture_id:
            return error_response('请提供 furniture_id', status_code=status.HTTP_400_BAD_REQUEST)

        furniture_obj = Furniture.objects.filter(furniture_id=furniture_id).first()
        if not furniture_obj:
            return error_response('家具不存在', status_code=status.HTTP_404_NOT_FOUND)

        # 排除定位字段，避免序列化器报错
        update_data = request.data.copy()
        update_data.pop('furniture_id', None)

        serializer = UpdateFurnitureSerializer(furniture_obj, data=update_data, partial=True)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return success_response(FurnitureSerializer(furniture_obj).data, message='修改成功')

    @action(detail=False, methods=['get'], url_path='dirFurniture')
    def dir_furniture(self, request):
        """
        查询家具信息接口。
        通过 furniture_id 查询单条记录。
        查询参数示例：
        /api/furniture/dirFurniture/?furniture_id=1
        """
        serializer = DirFurnitureQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        furniture_id = serializer.validated_data['furniture_id']
        furniture_obj = Furniture.objects.filter(furniture_id=furniture_id).first()
        if not furniture_obj:
            return error_response('家具不存在', status_code=status.HTTP_404_NOT_FOUND)

        return success_response(FurnitureSerializer(furniture_obj).data, message='查询成功')

    @action(detail=False, methods=['get'], url_path='dirFurnitureList')
    def dir_furniture_list(self, request):
        """
        查询所有家具列表。
        GET /api/furniture/dirFurnitureList/
        """
        furnitures = Furniture.objects.all().order_by('furniture_id')
        return success_response(FurnitureSerializer(furnitures, many=True).data, message='查询成功')
