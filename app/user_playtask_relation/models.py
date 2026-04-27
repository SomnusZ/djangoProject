"""
用户玩法任务关联实体定义。

关系说明：
    - User     与 UserPlaytaskRelation 是一对多：一个用户可参与多种玩法任务。
    - Playtask 与 UserPlaytaskRelation 是一对多：同一种玩法任务可被多个用户参与。
    - 同一用户对同一玩法任务只允许存在一条记录（通过 UniqueConstraint 保证），
      任务进度的更新通过修改 playtask_progress 字段实现，而非插入新记录。
"""

from django.db import models

from app.user.models import User
from app.playtask.models import Playtask


class UserPlaytaskRelation(models.Model):
    # 关联关系ID：自增主键
    relation_id = models.AutoField(primary_key=True, db_column='relation_id', verbose_name='关联ID')

    # 关联用户（多对一）：一个用户可参与多种玩法任务
    user = models.ForeignKey(
        User,
        to_field='user_id',
        db_column='user_id',
        on_delete=models.CASCADE,
        related_name='playtask_relations',
        verbose_name='用户',
    )

    # 关联玩法任务种类（多对一）：多个用户可参与同一种玩法任务
    playtask = models.ForeignKey(
        Playtask,
        to_field='playtask_id',
        db_column='playtask_id',
        on_delete=models.CASCADE,
        related_name='user_relations',
        verbose_name='玩法任务',
    )

    # 任务进度：当前用户该玩法任务的完成进度，默认为 0，范围由业务层约定
    playtask_progress = models.IntegerField(
        default=0,
        db_column='playtask_progress',
        verbose_name='任务进度',
    )

    class Meta:
        db_table = 'user_playtask_relation'
        verbose_name = '用户玩法任务关联'
        verbose_name_plural = '用户玩法任务关联'
        # 同一用户对同一玩法任务只允许一条记录
        constraints = [
            models.UniqueConstraint(fields=['user', 'playtask'], name='uniq_user_playtask'),
        ]

    def __str__(self):
        return f"用户{self.user_id} - {self.playtask.playtask_name}: 进度{self.playtask_progress}"
