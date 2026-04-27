"""
用户家具关联实体定义。

关系说明：
    - User      与 UserFurnitureRelation 是一对多：一个用户可拥有多种家具。
    - Furniture 与 UserFurnitureRelation 是一对多：同一种家具可被多个用户拥有。
    - 同一用户对同一家具只允许存在一条记录（通过 UniqueConstraint 保证），
      家具数量的增减通过更新 furniture_amount 字段实现，而非插入新记录。
"""

from django.db import models

from app.user.models import User
from app.furniture.models import Furniture


class UserFurnitureRelation(models.Model):
    # 关联关系ID：自增主键
    relation_id = models.AutoField(primary_key=True, db_column='relation_id', verbose_name='关联ID')

    # 关联用户（多对一）：一个用户可拥有多种家具
    user = models.ForeignKey(
        User,
        to_field='user_id',
        db_column='user_id',
        on_delete=models.CASCADE,
        related_name='furniture_relations',
        verbose_name='用户',
    )

    # 关联家具种类（多对一）：多个用户可拥有同一种家具
    furniture = models.ForeignKey(
        Furniture,
        to_field='furniture_id',
        db_column='furniture_id',
        on_delete=models.CASCADE,
        related_name='user_relations',
        verbose_name='家具',
    )

    # 家具数量：当前用户拥有该家具的数量，默认为 0
    furniture_amount = models.IntegerField(
        default=0,
        db_column='furniture_amount',
        verbose_name='家具数量',
    )

    class Meta:
        db_table = 'user_furniture_relation'
        verbose_name = '用户家具关联'
        verbose_name_plural = '用户家具关联'
        # 同一用户对同一家具只允许一条记录
        constraints = [
            models.UniqueConstraint(fields=['user', 'furniture'], name='uniq_user_furniture'),
        ]

    def __str__(self):
        return f"用户{self.user_id} - {self.furniture.furniture_name}: {self.furniture_amount}"
