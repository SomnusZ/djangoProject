"""
成就实体定义文件。
包含 Achievement 表结构，记录系统中所有可解锁的成就种类（如"首次登录"、"连续签到7天"等）。
"""

from django.db import models


class Achievement(models.Model):
    # 成就ID：自增主键
    achievement_id = models.AutoField(primary_key=True, db_column='achievement_id', verbose_name='成就ID')

    # 成就名称：如"首次登录"、"连续签到7天"等，全局唯一
    achievement_name = models.CharField(
        max_length=100,
        unique=True,
        db_column='achievement_name',
        verbose_name='成就名称',
    )

    class Meta:
        # 数据库表名
        db_table = 'achievement'
        # 管理后台展示名称
        verbose_name = '成就'
        verbose_name_plural = '成就'

    def __str__(self):
        return self.achievement_name
