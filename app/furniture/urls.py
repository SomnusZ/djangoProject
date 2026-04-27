"""
家具路由定义。
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FurnitureViewSet

router = DefaultRouter()
# 注册家具路由，最终路径为 /api/furniture/
router.register(r'', FurnitureViewSet, basename='furniture')

urlpatterns = [
    path('', include(router.urls)),
]
