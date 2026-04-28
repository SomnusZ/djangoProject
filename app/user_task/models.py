"""
用户任务实体定义文件。
包含 UserTask 表结构。
"""

import uuid

from django.db import models

from app.user.models import User


class WorkflowStatus(models.TextChoices):
    """AI 宠物生成工作流状态枚举"""
    PENDING          = 'pending',            '待开始'
    CLEANED          = 'cleaned',            '图片已预处理'
    MESHY_PENDING    = 'meshy_pending',      'Meshy任务已提交'
    IN_PROGRESS      = 'IN_PROGRESS',        'Meshy生成中'
    RESUBMIT_PENDING = 'resubmit_pending',   '重试提交中'
    MESHY_DONE       = 'meshy_done',         'Meshy完成'
    TEXTURE_PROC     = 'TEXTURE_PROCESSING', '贴图处理中'
    DONE             = 'DONE',               '全部完成'
    FAILED           = 'FAILED',             'Meshy失败'
    ERROR            = 'ERROR',              '本地错误'


class UserTask(models.Model):
    # 任务ID：UUID 字符串主键（创建时由业务层生成，与 CleanPic 输出文件名保持一致）
    user_task_id = models.CharField(
        primary_key=True,
        max_length=36,
        default=uuid.uuid4,
        editable=False,
        db_column='user_task_id',
        verbose_name='任务ID',
    )
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
    # 创建时间（用于列表排序，切换 UUID 主键后自增 ID 不再可用）
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    # ── AI 宠物生成工作流字段 ──────────────────────────────────
    workflow_status = models.CharField(
        max_length=32,
        choices=WorkflowStatus.choices,
        default=WorkflowStatus.CLEANED,
        verbose_name='工作流状态',
    )
    # 预处理后图片路径（相对项目根目录）
    image_path = models.CharField(max_length=512, blank=True, default='', verbose_name='图片路径')
    # YOLO 识别到的宠物品种
    pet_breed = models.CharField(max_length=100, blank=True, default='', verbose_name='宠物品种')
    # YOLO 识别到的宠物类型（cat/dog）
    pet_type = models.CharField(max_length=20, blank=True, default='', verbose_name='宠物类型')
    # Meshy 任务 ID
    meshy_job_id = models.CharField(max_length=200, blank=True, default='', verbose_name='Meshy任务ID')
    # Meshy 重试次数
    meshy_retry_count = models.IntegerField(default=0, verbose_name='Meshy重试次数')
    # 最终贴图清理后的本地路径
    texture_clean_path = models.CharField(max_length=512, blank=True, default='', verbose_name='贴图路径')
    # 工作流错误信息
    workflow_error = models.TextField(blank=True, default='', verbose_name='错误信息')

    class Meta:
        db_table = 'user_task'
        verbose_name = '用户任务'
        verbose_name_plural = '用户任务'
        constraints = [
            models.UniqueConstraint(fields=['user', 'task_name'], name='uniq_user_task_name'),
        ]

    def __str__(self):
        return self.task_name
