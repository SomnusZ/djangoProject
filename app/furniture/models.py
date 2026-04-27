"""
家具实体定义文件。
包含 Furniture 表结构，记录系统中所有可拥有的家具种类（如"木桌"、"沙发"、"书架"等）。
"""

from django.db import models


class Furniture(models.Model):
    # 家具ID：自增主键
    furniture_id = models.AutoField(primary_key=True, db_column='furniture_id', verbose_name='家具ID')

    # 家具名称：如"木桌"、"沙发"、"书架"等，全局唯一
    furniture_name = models.CharField(
        max_length=100,
        unique=True,
        db_column='furniture_name',
        verbose_name='家具名称',
    )

    class Meta:
        # 数据库表名
        db_table = 'furniture'
        # 管理后台展示名称
        verbose_name = '家具'
        verbose_name_plural = '家具'

    def __str__(self):
        return self.furniture_name
