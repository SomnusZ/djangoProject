"""
项目路由入口。
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from app.user.views import register_page

urlpatterns = [
    # 管理后台
    path('admin/', admin.site.urls),
    # 前端页面
    path('register/', register_page, name='register-page'),
    # 用户接口
    path('api/users/', include('app.user.urls')),
    # 模型接口
    path('api/models/', include('app.pet_user_model.urls')),
    # 动作接口
    path('api/actions/', include('app.pet_action.urls')),
]

# 开发环境下提供媒体文件访问
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
