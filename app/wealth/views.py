"""
货币资产视图文件。
包含货币资产相关接口：createWealth（新增）、updateWealth（修改）、dirWealth（查询）、dirWealthList（列表）。
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from app.permissions import IsAdminUser
from app.utils import success_response, error_response

from .models import Wealth
from .serializers import (
    WealthSerializer,
    CreateWealthSerializer,
    UpdateWealthSerializer,
    DirWealthQuerySerializer,
)


class WealthViewSet(viewsets.GenericViewSet):
    """
    货币资产接口视图集。
    包含货币资产新增、修改、查询。
    所有接口均需登录（IsAuthenticated）。
    """

    queryset = Wealth.objects.all()
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='createWealth',
            permission_classes=[IsAdminUser])
    def create_wealth(self, request):
        """
        新增货币资产接口。
        wealth_name 全局唯一，重复时返回 400。
        请求体示例：
        {
            "wealth_name": "金币"
        }
        """
        serializer = CreateWealthSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)
        wealth_obj = serializer.save()
        return success_response(
            WealthSerializer(wealth_obj).data,
            message='创建成功',
            status_code=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['put', 'patch'], url_path='updateWealth',
            permission_classes=[IsAdminUser])
    def update_wealth(self, request):
        """
        修改货币资产接口。
        通过 wealth_id 定位记录，仅允许修改 wealth_name。
        请求体示例：
        {
            "wealth_id": 1,
            "wealth_name": "钻石"
        }
        """
        wealth_id = request.data.get('wealth_id')
        if not wealth_id:
            return error_response('请提供 wealth_id', status_code=status.HTTP_400_BAD_REQUEST)

        wealth_obj = Wealth.objects.filter(wealth_id=wealth_id).first()
        if not wealth_obj:
            return error_response('货币资产不存在', status_code=status.HTTP_404_NOT_FOUND)

        # 排除定位字段，避免序列化器报错
        update_data = request.data.copy()
        update_data.pop('wealth_id', None)

        serializer = UpdateWealthSerializer(wealth_obj, data=update_data, partial=True)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return success_response(WealthSerializer(wealth_obj).data, message='修改成功')

    @action(detail=False, methods=['get'], url_path='dirWealth')
    def dir_wealth(self, request):
        """
        查询货币资产信息接口。
        通过 wealth_id 查询单条记录。
        查询参数示例：
        /api/wealth/dirWealth/?wealth_id=1
        """
        serializer = DirWealthQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        wealth_id = serializer.validated_data['wealth_id']
        wealth_obj = Wealth.objects.filter(wealth_id=wealth_id).first()
        if not wealth_obj:
            return error_response('货币资产不存在', status_code=status.HTTP_404_NOT_FOUND)

        return success_response(WealthSerializer(wealth_obj).data, message='查询成功')

    @action(detail=False, methods=['get'], url_path='dirWealthList')
    def dir_wealth_list(self, request):
        """
        查询所有货币资产列表。
        GET /api/wealth/dirWealthList/
        """
        wealths = Wealth.objects.all().order_by('wealth_id')
        return success_response(WealthSerializer(wealths, many=True).data, message='查询成功')
