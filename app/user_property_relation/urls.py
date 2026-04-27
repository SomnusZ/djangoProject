"""
用户属性关联路由定义。
"""

from django.urls import path

from .views import UserPropertyRelationViewSet

urlpatterns = [
    path('bindPropertyToUser/', UserPropertyRelationViewSet.as_view({'post': 'bind_property_to_user'})),
    path('unbindPropertyFromUser/', UserPropertyRelationViewSet.as_view({'post': 'unbind_property_from_user'})),
    path('dirPropertyListByUser/', UserPropertyRelationViewSet.as_view({'get': 'dir_property_list_by_user'})),
]
