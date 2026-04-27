"""
用户玩法任务关联路由定义。
"""

from django.urls import path

from .views import UserPlaytaskRelationViewSet

urlpatterns = [
    path('bindPlaytaskToUser/', UserPlaytaskRelationViewSet.as_view({'post': 'bind_playtask_to_user'})),
    path('unbindPlaytaskFromUser/', UserPlaytaskRelationViewSet.as_view({'post': 'unbind_playtask_from_user'})),
    path('dirPlaytaskListByUser/', UserPlaytaskRelationViewSet.as_view({'get': 'dir_playtask_list_by_user'})),
]
