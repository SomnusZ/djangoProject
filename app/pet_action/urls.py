"""
动作路由定义（仅动作相关）。
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PetActionViewSet

router = DefaultRouter()
# 注册动作路由，最终路径为 /api/actions/
router.register(r'', PetActionViewSet, basename='pet_action')

urlpatterns = [
    path('', include(router.urls)),
]
