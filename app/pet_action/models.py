"""
动作实体定义文件。
包含 PetAction 表结构。
"""

from django.db import models

class PetAction(models.Model):
    # 动作ID：自增主键
    pet_action_id = models.AutoField(primary_key=True, db_column='pet_action_id', verbose_name='动作ID')
    # 动作名称
    pet_action_name = models.CharField(max_length=200, verbose_name='动作名称')

    class Meta:
        # 指定数据库表名
        db_table = 'pet_action'
        # 管理后台展示名称
        verbose_name = '动作'
        verbose_name_plural = '动作'

    def __str__(self):
        # 展示动作名称
        return self.pet_action_name
