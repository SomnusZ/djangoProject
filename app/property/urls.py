"""
属性路由定义。
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PropertyViewSet

router = DefaultRouter()
# 注册属性路由，最终路径为 /api/property/
router.register(r'', PropertyViewSet, basename='property')

urlpatterns = [
    path('', include(router.urls)),
]
