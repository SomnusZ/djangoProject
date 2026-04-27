"""
用户属性关联实体定义。

关系说明：
    - User     与 UserPropertyRelation 是一对多：一个用户可拥有多种属性。
    - Property 与 UserPropertyRelation 是一对多：同一种属性可被多个用户拥有。
    - 同一用户对同一属性只允许存在一条记录（通过 UniqueConstraint 保证），
      属性数值的增减通过更新 property_amount 字段实现，而非插入新记录。
"""

from django.db import models

from app.user.models import User
from app.property.models import Property


class UserPropertyRelation(models.Model):
    # 关联关系ID：自增主键
    relation_id = models.AutoField(primary_key=True, db_column='relation_id', verbose_name='关联ID')

    # 关联用户（多对一）：一个用户可拥有多种属性
    user = models.ForeignKey(
        User,
        to_field='user_id',
        db_column='user_id',
        on_delete=models.CASCADE,
        related_name='property_relations',
        verbose_name='用户',
    )

    # 关联属性种类（多对一）：多个用户可拥有同一种属性
    property = models.ForeignKey(
        Property,
        to_field='property_id',
        db_column='property_id',
        on_delete=models.CASCADE,
        related_name='user_relations',
        verbose_name='属性',
    )

    # 属性数值：当前用户该属性的数值，默认为 0
    property_amount = models.IntegerField(
        default=0,
        db_column='property_amount',
        verbose_name='属性数值',
    )

    class Meta:
        db_table = 'user_property_relation'
        verbose_name = '用户属性关联'
        verbose_name_plural = '用户属性关联'
        # 同一用户对同一属性只允许一条记录
        constraints = [
            models.UniqueConstraint(fields=['user', 'property'], name='uniq_user_property'),
        ]

    def __str__(self):
        return f"用户{self.user_id} - {self.property.property_name}: {self.property_amount}"
