"""
用户模型定义文件。
本文件包含数据库表结构（User），用于存储用户基本信息。
"""

from django.db import models


class User(models.Model):
    # 用户ID：自增主键
    user_id = models.AutoField(primary_key=True, db_column='user_id', verbose_name='用户ID')
    # 用户名：允许为空，便于先注册后补充资料
    user_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='用户名')
    # 用户头像：上传至 media/profile_pics/ 目录
    user_profile_picture = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True,
        verbose_name='头像',
    )
    # 手机号：注册必填（模型层允许空，校验交由序列化器控制）
    user_phone_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        blank=True,
        null=True,
        verbose_name='手机号',
    )
    # 密码：存储哈希后的密码字符串
    user_password = models.CharField(max_length=128, verbose_name='密码')
    # 邮箱：弃用（允许为空，保留字段兼容历史数据）
    user_mail_address = models.EmailField(unique=True, db_index=True, blank=True, null=True, verbose_name='邮箱')

    class Meta:
        # 指定数据库表名
        db_table = 'user'
        # 管理后台展示名称
        verbose_name = '用户'
        verbose_name_plural = '用户'

    def __str__(self):
        # 优先展示用户名，没有则展示手机号或邮箱
        return self.user_name or self.user_phone_number or self.user_mail_address or str(self.user_id)

    @property
    def is_authenticated(self):
        """
        兼容 DRF 权限检查。
        自定义用户模型不继承 Django Auth 时，始终视为已认证用户。
        """
        return True
