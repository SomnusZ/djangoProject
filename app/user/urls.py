"""
用户路由定义（仅用户相关 API）。
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import UserViewSet

router = DefaultRouter()
# 注册用户路由，最终路径为 /api/users/
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    # API 路由
    path('', include(router.urls)),
]
