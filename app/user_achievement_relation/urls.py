"""
用户成就关联路由定义。
"""

from django.urls import path

from .views import UserAchievementRelationViewSet

urlpatterns = [
    path('bindAchievementToUser/', UserAchievementRelationViewSet.as_view({'post': 'bind_achievement_to_user'})),
    path('unbindAchievementFromUser/', UserAchievementRelationViewSet.as_view({'post': 'unbind_achievement_from_user'})),
    path('dirAchievementListByUser/', UserAchievementRelationViewSet.as_view({'get': 'dir_achievement_list_by_user'})),
]
