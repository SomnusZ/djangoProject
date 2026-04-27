"""
用户货币资产关联实体定义。

关系说明：
    - User  与 UserWealthRelation 是一对多：一个用户可持有多种货币资产。
    - Wealth 与 UserWealthRelation 是一对多：同一种货币资产可被多个用户持有。
    - 同一用户对同一种货币资产只允许存在一条记录（通过 UniqueConstraint 保证），
      货币数量的增减通过更新 wealth_amount 字段实现，而非插入新记录。
"""

from django.db import models

from app.user.models import User
from app.wealth.models import Wealth


class UserWealthRelation(models.Model):
    # 关联关系ID：自增主键
    relation_id = models.AutoField(primary_key=True, db_column='relation_id', verbose_name='关联ID')

    # 关联用户（多对一）：一个用户可拥有多条货币资产记录
    user = models.ForeignKey(
        User,
        to_field='user_id',
        db_column='user_id',
        on_delete=models.CASCADE,
        related_name='wealth_relations',
        verbose_name='用户',
    )

    # 关联货币资产种类（多对一）：多个用户可持有同一种货币资产
    wealth = models.ForeignKey(
        Wealth,
        to_field='wealth_id',
        db_column='wealth_id',
        on_delete=models.CASCADE,
        related_name='user_relations',
        verbose_name='货币资产',
    )

    # 货币数量：当前用户持有该货币资产的数量，默认为 0，不允许为负
    wealth_amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
        db_column='wealth_amount',
        verbose_name='货币数量',
    )

    class Meta:
        db_table = 'user_wealth_relation'
        verbose_name = '用户货币资产关联'
        verbose_name_plural = '用户货币资产关联'
        # 同一用户对同一货币资产只允许一条记录
        constraints = [
            models.UniqueConstraint(fields=['user', 'wealth'], name='uniq_user_wealth'),
        ]

    def __str__(self):
        return f"用户{self.user_id} - {self.wealth.wealth_name}: {self.wealth_amount}"
