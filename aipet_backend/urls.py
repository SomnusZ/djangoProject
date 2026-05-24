"""
项目路由入口。
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from app.test_views import test_page

urlpatterns = [
    # 管理后台
    path('admin/', admin.site.urls),
    # 前端测试页面（通用路由）
    path('test/<str:name>/', test_page, name='test-page'),
    # JWT 刷新/校验
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    # 用户接口
    path('api/users/', include('app.user.urls')),
    # 模型接口
    path('api/models/', include('app.user_task.urls')),
    # 宠物模型接口
    path('api/pet-models/', include('app.pet_model.urls')),
    # 动作接口
    path('api/actions/', include('app.pet_action.urls')),
    # 任务动作关系接口
    path('api/task-actions/', include('app.user_task_action_relation.urls')),
    # 货币资产接口
    path('api/wealth/', include('app.wealth.urls')),
    # 用户货币资产关联接口
    path('api/user-wealth/', include('app.user_wealth_relation.urls')),
    # 玩法任务接口
    path('api/playtask/', include('app.playtask.urls')),
    # 用户玩法任务关联接口
    path('api/user-playtask/', include('app.user_playtask_relation.urls')),
    # 成就接口
    path('api/achievement/', include('app.achievement.urls')),
    # 用户成就关联接口
    path('api/user-achievement/', include('app.user_achievement_relation.urls')),
    # 家具接口
    path('api/furniture/', include('app.furniture.urls')),
    # 用户家具关联接口
    path('api/user-furniture/', include('app.user_furniture_relation.urls')),
    # 属性接口
    path('api/property/', include('app.property.urls')),
    # 用户属性关联接口
    path('api/user-property/', include('app.user_property_relation.urls')),
    # 宠物眼球UV贴图接口
    path('api/pet-eye-uvs/', include('app.pet_eye_uv_texture.urls')),
]

# 开发环境下提供媒体文件访问
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
