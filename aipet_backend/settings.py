"""
Django settings for aipet_backend.
本配置文件包含：应用配置、数据库配置、静态与媒体文件配置等。
"""

from pathlib import Path
from datetime import timedelta

# 构建项目基础路径
BASE_DIR = Path(__file__).resolve().parent.parent

# 安全密钥（生产环境请替换并保密）
SECRET_KEY = 'django-insecure-rx7-02sh1tidvpq4k&@@2a#06+69o^15ze8b%me^ycnw%y+c9g'

# 调试模式（生产环境必须关闭）
DEBUG = True
# DEBUG = False

# 允许访问的主机
ALLOWED_HOSTS = []
# ALLOWED_HOSTS = ['42.193.98.94', 'localhost', '127.0.0.1']

# 应用配置
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Django REST framework
    'rest_framework',
    # 用户应用
    'app.user.apps.UsersConfig',
    # 模型应用
    'app.user_task.apps.UserTaskConfig',
    # 宠物模型应用
    'app.pet_model.apps.PetModelConfig',
    # 动作应用
    'app.pet_action.apps.PetActionConfig',
    # 任务动作关系应用
    'app.user_task_action_relation.apps.UserTaskActionRelationConfig',
    # 货币资产应用
    'app.wealth.apps.WealthConfig',
    # 用户货币资产关联应用
    'app.user_wealth_relation.apps.UserWealthRelationConfig',
    # 玩法任务应用
    'app.playtask.apps.PlaytaskConfig',
    # 用户玩法任务关联应用
    'app.user_playtask_relation.apps.UserPlaytaskRelationConfig',
    # 成就应用
    'app.achievement.apps.AchievementConfig',
    # 用户成就关联应用
    'app.user_achievement_relation.apps.UserAchievementRelationConfig',
    # 家具应用
    'app.furniture.apps.FurnitureConfig',
    # 用户家具关联应用
    'app.user_furniture_relation.apps.UserFurnitureRelationConfig',
    # 属性应用
    'app.property.apps.PropertyConfig',
    # 用户属性关联应用
    'app.user_property_relation.apps.UserPropertyRelationConfig',
]

# 中间件
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'app.log_middleware.RequestLogMiddleware',
]

# 路由入口
ROOT_URLCONF = 'aipet_backend.urls'

# 模板配置
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI 入口
WSGI_APPLICATION = 'aipet_backend.wsgi.application'

# 数据库配置（MySQL）
# 需要安装 mysqlclient 或 pymysql
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'aipetdb',
        'USER': 'root',
        'PASSWORD': '123123zhh',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'aipetdb',
#         'USER': 'root',
#         'PASSWORD': 'NewPassword123!',
#         'HOST': '127.0.0.1',
#         'PORT': '3306',
#     }
# }

# 密码验证
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 国际化
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# 静态文件
STATIC_URL = 'static/'

# 媒体文件（上传头像）
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
SITE_URL = 'http://127.0.0.1:8000'  # 本地开发
# SITE_URL = 'http://42.193.98.94'  # 生产服务器

# 默认主键类型
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Meshy 基础宠物模型路径（相对项目根目录）
# 首次调用 submitMeshyTask 时懒加载，base64 编码后缓存在内存中
MESHY_MODEL_PATH = str(BASE_DIR / 'aipet' / '3Dmodels' / 'Sample' / 'model0107.fbx')

# 服务器外网地址，用于拼接贴图下载 URL
# nginx 配置：location /meshy_images/ -> /www/wwwroot/djangoProject/aipet/3Dmodels/meshy/
MESHY_SERVER_URL = 'http://127.0.0.1:8000'  # 本地开发
# MESHY_SERVER_URL = 'http://42.193.98.94'  # 生产服务器

# DRF 配置
REST_FRAMEWORK = {
    # 启用 JWT 认证，启用自定义user实体
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'app.permissions.AppUserJWTAuthentication',
    ],
    # 强制登录：所有接口访问必须要求登录并携带有效 Token
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        # Keep JSON as default for backward compatibility.
        # Existing frontend/test pages require JSON and should not break.
        'rest_framework.renderers.JSONRenderer',
        # Add protobuf output when client sends Accept: application/x-protobuf.
        # This is additive, not a replacement:
        # - No business view changes required.
        # - Same response payload is encoded into protobuf envelope.
        # - If client does not request protobuf, JSON response remains unchanged.
        'app.protobuf.renderer.ProtobufRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        # Accept Content-Type: application/x-protobuf request bodies.
        # Deserializes binary proto to dict; views receive it via request.data
        # with no changes required.
        'app.protobuf.parser.ProtobufParser',
    ],
}

# JWT 配置
SIMPLE_JWT = {
    # 访问令牌有效期
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    # 刷新令牌有效期
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    # 自定义用户主键字段（项目使用 user_id）
    'USER_ID_FIELD': 'user_id',
    # Token 中的字段名（可按需调整）
    'USER_ID_CLAIM': 'user_id',
    # 是否轮换刷新令牌
    'ROTATE_REFRESH_TOKENS': False,
    # 刷新后是否将旧令牌加入黑名单（如需可开启并添加黑名单应用）
    'BLACKLIST_AFTER_ROTATION': False,
}

# 日志配置（输出到文件 logs/api.log）
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] %(levelname)s %(name)s %(message)s',
        },
    },
    'handlers': {
        'api_file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'api.log',
            'formatter': 'standard',
            'encoding': 'utf-8',
        },
        # 控制台日志输出（开发调试）
        'api_console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        'api': {
            # 同时输出到文件与控制台
            'handlers': ['api_file', 'api_console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
