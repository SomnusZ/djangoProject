"""
属性视图文件。
包含属性相关接口：createProperty（新增）、updateProperty（修改）、dirProperty（查询）、dirPropertyList（列表）。
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from app.permissions import IsAdminUser
from app.utils import success_response, error_response

from .models import Property
from .serializers import (
    PropertySerializer,
    CreatePropertySerializer,
    UpdatePropertySerializer,
    DirPropertyQuerySerializer,
)


class PropertyViewSet(viewsets.GenericViewSet):
    """
    属性接口视图集。
    包含属性新增、修改、查询。
    所有接口均需登录（IsAuthenticated）。
    """

    queryset = Property.objects.all()
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='createProperty',
            permission_classes=[IsAdminUser])
    def create_property(self, request):
        """
        新增属性接口。
        property_name 全局唯一，重复时返回 400。
        请求体示例：
        {
            "property_name": "力量"
        }
        """
        serializer = CreatePropertySerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        property_obj = serializer.save()
        return success_response(
            PropertySerializer(property_obj).data,
            message='创建成功',
            status_code=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['put', 'patch'], url_path='updateProperty',
            permission_classes=[IsAdminUser])
    def update_property(self, request):
        """
        修改属性接口。
        通过 property_id 定位记录，仅允许修改 property_name。
        请求体示例：
        {
            "property_id": 1,
            "property_name": "最大力量"
        }
        """
        property_id = request.data.get('property_id')
        if not property_id:
            return error_response('请提供 property_id', status_code=status.HTTP_400_BAD_REQUEST)

        property_obj = Property.objects.filter(property_id=property_id).first()
        if not property_obj:
            return error_response('属性不存在', status_code=status.HTTP_404_NOT_FOUND)

        # 排除定位字段，避免序列化器报错
        update_data = request.data.copy()
        update_data.pop('property_id', None)

        serializer = UpdatePropertySerializer(property_obj, data=update_data, partial=True)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return success_response(PropertySerializer(property_obj).data, message='修改成功')

    @action(detail=False, methods=['get'], url_path='dirProperty')
    def dir_property(self, request):
        """
        查询属性信息接口。
        通过 property_id 查询单条记录。
        查询参数示例：
        /api/property/dirProperty/?property_id=1
        """
        serializer = DirPropertyQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        property_id = serializer.validated_data['property_id']
        property_obj = Property.objects.filter(property_id=property_id).first()
        if not property_obj:
            return error_response('属性不存在', status_code=status.HTTP_404_NOT_FOUND)

        return success_response(PropertySerializer(property_obj).data, message='查询成功')

    @action(detail=False, methods=['get'], url_path='dirPropertyList')
    def dir_property_list(self, request):
        """
        查询所有道具列表。
        GET /api/property/dirPropertyList/
        """
        properties = Property.objects.all().order_by('property_id')
        return success_response(PropertySerializer(properties, many=True).data, message='查询成功')
