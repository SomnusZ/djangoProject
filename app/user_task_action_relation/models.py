"""
任务动作关系实体定义。
任务与动作通过中间表关联。
"""

from django.db import models

from app.user_task.models import UserTask
from app.pet_action.models import PetAction


class UserTaskActionRelation(models.Model):
    # 关系ID：自增主键
    relation_id = models.AutoField(primary_key=True, db_column='relation_id', verbose_name='关系ID')

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
        db_table = 'user_task_action_relation'
        verbose_name = '任务动作关系'
        verbose_name_plural = '任务动作关系'
        constraints = [
            models.UniqueConstraint(fields=['user_task', 'pet_action'], name='uniq_task_action'),
        ]

    def __str__(self):
        return f"{self.user_task_id}-{self.pet_action_id}"
