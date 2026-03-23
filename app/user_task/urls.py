"""
模型路由定义（仅模型相关）。
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PetModelViewSet

router = DefaultRouter()
# 注册模型路由，最终路径为 /api/models/
router.register(r'', PetModelViewSet, basename='user_task')

urlpatterns = [
    path('', include(router.urls)),
]
