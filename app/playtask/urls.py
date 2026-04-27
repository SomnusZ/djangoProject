"""
玩法任务路由定义。
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PlaytaskViewSet

router = DefaultRouter()
# 注册玩法任务路由，最终路径为 /api/playtask/
router.register(r'', PlaytaskViewSet, basename='playtask')

urlpatterns = [
    path('', include(router.urls)),
]
