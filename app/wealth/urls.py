"""
货币资产路由定义。
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import WealthViewSet

router = DefaultRouter()
# 注册货币资产路由，最终路径为 /api/wealth/
router.register(r'', WealthViewSet, basename='wealth')

urlpatterns = [
    path('', include(router.urls)),
]
