"""
成就路由定义。
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AchievementViewSet

router = DefaultRouter()
# 注册成就路由，最终路径为 /api/achievement/
router.register(r'', AchievementViewSet, basename='achievement')

urlpatterns = [
    path('', include(router.urls)),
]
