"""
属性实体定义文件。
包含 Property 表结构，记录系统中所有可拥有的属性种类（如"力量"、"敏捷"、"智力"等）。
"""

from django.db import models


class Property(models.Model):
    # 属性ID：自增主键
    property_id = models.AutoField(primary_key=True, db_column='property_id', verbose_name='属性ID')

    # 属性名称：如"力量"、"敏捷"、"智力"等，全局唯一
    property_name = models.CharField(
        max_length=100,
        unique=True,
        db_column='property_name',
        verbose_name='属性名称',
    )

    class Meta:
        # 数据库表名
        db_table = 'property'
        # 管理后台展示名称
        verbose_name = '属性'
        verbose_name_plural = '属性'

    def __str__(self):
        return self.property_name
