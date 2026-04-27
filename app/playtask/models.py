"""
玩法任务实体定义文件。
包含 Playtask 表结构，记录系统中所有可分配的玩法任务种类（如每日签到、打卡任务等）。
"""

from django.db import models


class Playtask(models.Model):
    # 玩法任务ID：自增主键
    playtask_id = models.AutoField(primary_key=True, db_column='playtask_id', verbose_name='玩法任务ID')

    # 玩法任务名称：如"每日签到"、"打卡任务"、"挑战关卡"等，全局唯一
    playtask_name = models.CharField(
        max_length=100,
        unique=True,
        db_column='playtask_name',
        verbose_name='玩法任务名称',
    )

    class Meta:
        # 数据库表名
        db_table = 'playtask'
        # 管理后台展示名称
        verbose_name = '玩法任务'
        verbose_name_plural = '玩法任务'

    def __str__(self):
        return self.playtask_name
