"""
任务动作关系实体定义文件。
包含 UserTaskActionRelation 表结构。
"""

from django.db import models

from app.user_task.models import PetModel as UserTask
from app.pet_action.models import PetAction


class UserTaskActionRelation(models.Model):
    """
    任务-动作关联表。
    表达业务关系：一个任务可以关联多个动作，一个动作也可被多个任务使用。
    """

    # 关联ID：自增主键
    relation_id = models.AutoField(primary_key=True, db_column='relation_id', verbose_name='关联ID')
    # 关联任务（多对一）
    user_task = models.ForeignKey(
        UserTask,
        to_field='user_task_id',
        db_column='user_task_id',
        on_delete=models.CASCADE,
        related_name='action_relations',
        verbose_name='任务',
    )
    # 关联动作（多对一）
    pet_action = models.ForeignKey(
        PetAction,
        to_field='pet_action_id',
        db_column='pet_action_id',
        on_delete=models.CASCADE,
        related_name='task_relations',
        verbose_name='动作',
    )

    class Meta:
        # 指定数据库表名
        db_table = 'user_task_action_relation'
        # 关联去重，避免重复绑定
        unique_together = ('user_task', 'pet_action')
        # 管理后台展示名称
        verbose_name = '任务动作关联'
        verbose_name_plural = '任务动作关联'

