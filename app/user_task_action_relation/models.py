"""
浠诲姟鍔ㄤ綔鍏崇郴瀹炰綋瀹氫箟鏂囦欢銆
鍖呭惈 UserTaskActionRelation 琛ㄧ粨鏋勩
"""

from django.db import models

from app.user_task.models import UserTask
from app.pet_action.models import PetAction


class UserTaskActionRelation(models.Model):
    """
    浠诲姟-鍔ㄤ綔鍏宠仈琛ㄣ
    琛ㄨ揪涓氬姟鍏崇郴锛氫竴涓浠诲姟鍙浠ュ叧鑱斿氫釜鍔ㄤ綔锛屼竴涓鍔ㄤ綔涔熷彲琚澶氫釜浠诲姟浣跨敤銆
    """

    # 鍏宠仈ID锛氳嚜澧炰富閿
    relation_id = models.AutoField(primary_key=True, db_column='relation_id', verbose_name='鍏宠仈ID')
    # 鍏宠仈浠诲姟锛堝氬逛竴锛
    user_task = models.ForeignKey(
        UserTask,
        to_field='user_task_id',
        db_column='user_task_id',
        on_delete=models.CASCADE,
        related_name='action_relations',
        verbose_name='浠诲姟',
    )
    # 鍏宠仈鍔ㄤ綔锛堝氬逛竴锛
    pet_action = models.ForeignKey(
        PetAction,
        to_field='pet_action_id',
        db_column='pet_action_id',
        on_delete=models.CASCADE,
        related_name='task_relations',
        verbose_name='鍔ㄤ綔',
    )

    class Meta:
        # 鎸囧畾鏁版嵁搴撹〃鍚
        db_table = 'user_task_action_relation'
        # 鍏宠仈鍘婚噸锛岄伩鍏嶉噸澶嶇粦瀹
        unique_together = ('user_task', 'pet_action')
        # 绠＄悊鍚庡彴灞曠ず鍚嶇О
        verbose_name = '浠诲姟鍔ㄤ綔鍏宠仈'
        verbose_name_plural = '浠诲姟鍔ㄤ綔鍏宠仈'

