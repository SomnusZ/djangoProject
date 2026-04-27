"""
货币资产实体定义文件。
包含 Wealth 表结构，记录系统中所有可分配的货币资产种类（如金币、钻石等）。
"""

from django.db import models


class Wealth(models.Model):
    # 货币资产ID：自增主键
    wealth_id = models.AutoField(primary_key=True, db_column='wealth_id', verbose_name='货币资产ID')

    # 货币资产名称：如"金币"、"钻石"、"积分"等，全局唯一
    wealth_name = models.CharField(
        max_length=100,
        unique=True,
        db_column='wealth_name',
        verbose_name='货币资产名称',
    )

    class Meta:
        # 数据库表名
        db_table = 'wealth'
        # 管理后台展示名称
        verbose_name = '货币资产'
        verbose_name_plural = '货币资产'

    def __str__(self):
        return self.wealth_name
