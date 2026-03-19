"""
Django settings for aipet_backend.
本配置文件包含：应用配置、数据库配置、静态与媒体文件配置等。
"""

from pathlib import Path

# 构建项目基础路径
BASE_DIR = Path(__file__).resolve().parent.parent

# 安全密钥（生产环境请替换并保密）
SECRET_KEY = 'django-insecure-rx7-02sh1tidvpq4k&@@2a#06+69o^15ze8b%me^ycnw%y+c9g'

# 调试模式（生产环境必须关闭）
DEBUG = True

# 允许访问的主机
ALLOWED_HOSTS = []

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
    'app.pet_user_model.apps.PetUserModelConfig',
    # 动作应用
    'app.pet_action.apps.PetActionConfig',
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

# 默认主键类型
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# DRF 配置
REST_FRAMEWORK = {
    # 关闭默认 SessionAuthentication 的 CSRF 校验，方便前端联调
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    # 允许匿名访问
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
    ],
}
