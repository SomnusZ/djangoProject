"""
用户任务实体定义文件。
包含 UserTask 表结构。
"""

from django.db import models

from app.user.models import User


class UserTask(models.Model):
    # 任务ID：自增主键
    user_task_id = models.AutoField(primary_key=True, db_column='user_task_id', verbose_name='任务ID')
    # 关联用户（多对一）
    user = models.ForeignKey(
        User,
        to_field='user_id',
        db_column='user_id',
        on_delete=models.CASCADE,
        related_name='user_tasks',
        verbose_name='用户',
    )
    # 任务名称
    task_name = models.CharField(max_length=200, verbose_name='任务名称')

    class Meta:
        # 指定数据库表名
        db_table = 'user_task'
        # 管理后台展示名称
        verbose_name = '用户任务'
        verbose_name_plural = '用户任务'

    def __str__(self):
        # 展示任务名称
        return self.task_name
