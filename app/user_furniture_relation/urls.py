"""
用户家具关联路由定义。
"""

from django.urls import path

from .views import UserFurnitureRelationViewSet

urlpatterns = [
    path('bindFurnitureToUser/', UserFurnitureRelationViewSet.as_view({'post': 'bind_furniture_to_user'})),
    path('unbindFurnitureFromUser/', UserFurnitureRelationViewSet.as_view({'post': 'unbind_furniture_from_user'})),
    path('dirFurnitureListByUser/', UserFurnitureRelationViewSet.as_view({'get': 'dir_furniture_list_by_user'})),
]
