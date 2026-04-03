"""
用户任务路由定义（仅任务相关）。
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import UserTaskViewSet

router = DefaultRouter()
# 注册任务路由，最终路径为 /api/models/
router.register(r'', UserTaskViewSet, basename='user_task')

urlpatterns = [
    path('', include(router.urls)),
]
