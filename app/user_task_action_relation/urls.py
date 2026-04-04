"""
任务动作关系路由。
"""

from django.urls import path

from .views import UserTaskActionRelationViewSet


urlpatterns = [
    path('bindActionToTask/', UserTaskActionRelationViewSet.as_view({'post': 'bind_action_to_task'})),
    path('unbindActionFromTask/', UserTaskActionRelationViewSet.as_view({'post': 'unbind_action_from_task'})),
    path('dirActionListByTask/', UserTaskActionRelationViewSet.as_view({'get': 'dir_action_list_by_task'})),
]
