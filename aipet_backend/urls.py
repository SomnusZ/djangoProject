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
]

# 开发环境下提供媒体文件访问
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
