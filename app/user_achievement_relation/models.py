"""
用户成就关联实体定义。

关系说明：
    - User        与 UserAchievementRelation 是一对多：一个用户可解锁多个成就。
    - Achievement 与 UserAchievementRelation 是一对多：同一个成就可被多个用户解锁。
    - 同一用户对同一成就只允许存在一条记录（通过 UniqueConstraint 保证），
      表示该用户已解锁该成就，重复解锁在业务层拦截。
"""

from django.db import models

from app.user.models import User
from app.achievement.models import Achievement


class UserAchievementRelation(models.Model):
    # 关联关系ID：自增主键
    relation_id = models.AutoField(primary_key=True, db_column='relation_id', verbose_name='关联ID')

    # 关联用户（多对一）：一个用户可解锁多个成就
    user = models.ForeignKey(
        User,
        to_field='user_id',
        db_column='user_id',
        on_delete=models.CASCADE,
        related_name='achievement_relations',
        verbose_name='用户',
    )

    # 关联成就（多对一）：同一成就可被多个用户解锁
    achievement = models.ForeignKey(
        Achievement,
        to_field='achievement_id',
        db_column='achievement_id',
        on_delete=models.CASCADE,
        related_name='user_relations',
        verbose_name='成就',
    )

    class Meta:
        db_table = 'user_achievement_relation'
        verbose_name = '用户成就关联'
        verbose_name_plural = '用户成就关联'
        # 同一用户对同一成就只允许一条记录，防止重复解锁
        constraints = [
            models.UniqueConstraint(fields=['user', 'achievement'], name='uniq_user_achievement'),
        ]

    def __str__(self):
        return f"用户{self.user_id} - {self.achievement.achievement_name}"
