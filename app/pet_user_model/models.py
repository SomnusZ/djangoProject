"""
模型实体定义文件。
包含 PetModel 表结构。
"""

from django.db import models

from app.user.models import User


class PetModel(models.Model):
    # 模型ID：自增主键
    pet_model_id = models.AutoField(primary_key=True, db_column='pet_model_id', verbose_name='模型ID')
    # 关联用户（多对一）
    user = models.ForeignKey(
        User,
        to_field='user_id',
        db_column='user_id',
        on_delete=models.CASCADE,
        related_name='pet_models',
        verbose_name='用户',
    )
    # 模型名称
    model_name = models.CharField(max_length=200, verbose_name='模型名称')
    # 模型地址（存储路径或URL）
    model_address = models.CharField(max_length=500, verbose_name='模型地址')

    class Meta:
        # 指定数据库表名
        db_table = 'pet_model'
        # 管理后台展示名称
        verbose_name = '宠物模型'
        verbose_name_plural = '宠物模型'

    def __str__(self):
        # 展示模型名称
        return self.model_name
