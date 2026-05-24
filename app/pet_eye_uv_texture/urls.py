"""
宠物眼球UV贴图路由定义。
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PetEyeUvViewSet

router = DefaultRouter()
# 注册眼球UV贴图路由，最终路径为 /api/pet-eye-uvs/
router.register(r'', PetEyeUvViewSet, basename='pet_eye_uv')

urlpatterns = [
    path('', include(router.urls)),
]
