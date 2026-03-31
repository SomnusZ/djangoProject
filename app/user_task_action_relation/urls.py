"""
任务动作关系路由定义。
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import UserTaskActionRelationViewSet

router = DefaultRouter()
# 注册关系路由，最终路径为 /api/task-actions/
router.register(r'', UserTaskActionRelationViewSet, basename='user_task_action_relation')

urlpatterns = [
    path('', include(router.urls)),
]
