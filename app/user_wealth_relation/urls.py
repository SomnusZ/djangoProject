"""
用户货币资产关联路由定义。
"""

from django.urls import path

from .views import UserWealthRelationViewSet

urlpatterns = [
    path('bindWealthToUser/', UserWealthRelationViewSet.as_view({'post': 'bind_wealth_to_user'})),
    path('unbindWealthFromUser/', UserWealthRelationViewSet.as_view({'post': 'unbind_wealth_from_user'})),
    path('dirWealthListByUser/', UserWealthRelationViewSet.as_view({'get': 'dir_wealth_list_by_user'})),
]
