"""
宠物眼球UV贴图实体定义文件。
包含 PetEyeUv 表结构，记录每次眼球UV贴图生成的输入、输出与执行状态。
"""

from django.db import models


class PetEyeUv(models.Model):
    """
    宠物眼球UV贴图生成记录表。
    每次调用 generateEyeUv 接口写入一条，记录原图、生成结果及执行状态。
    当前与 user / user_task 解耦，仅作为独立的生成历史表存在。
    """

    # 记录ID：UUID 字符串主键（由业务层在写库前预生成）
    pet_eye_uv_id = models.CharField(max_length=36, primary_key=True, db_column='pet_eye_uv_id', verbose_name='眼球UV记录ID')
    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    # 更新时间
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    # 原图本地路径（保存到 aipet/photo_to_uv_texture/UserImage/ 下）
    original_image_path = models.CharField(max_length=512, default='', verbose_name='原图本地路径')

    # 工作流状态：upload_success / processing / generate_success / generate_fail
    workflow_status = models.CharField(max_length=32, default='upload_success', verbose_name='工作流状态')

    # 检测到的眼睛数量（0 / 1 / 2）
    eye_count = models.IntegerField(default=0, verbose_name='检测到的眼睛数量')

    # 第一只眼 UV 贴图可访问 URL
    eye_uv_url_0 = models.CharField(max_length=512, default='', verbose_name='眼球0 UV贴图URL')
    # 第二只眼 UV 贴图可访问 URL
    eye_uv_url_1 = models.CharField(max_length=512, default='', verbose_name='眼球1 UV贴图URL')

    # 第一只眼虹膜颜色 BGR，格式 "b,g,r"
    base_bgr_0 = models.CharField(max_length=50, default='', verbose_name='眼球0虹膜BGR')
    # 第二只眼虹膜颜色 BGR，格式 "b,g,r"
    base_bgr_1 = models.CharField(max_length=50, default='', verbose_name='眼球1虹膜BGR')

    # 工作流错误信息（空字符串表示无错误）
    workflow_error = models.TextField(default='', blank=True, verbose_name='工作流错误信息')

    class Meta:
        # 指定数据库表名
        db_table = 'pet_eye_uv'
        # 管理后台展示名称
        verbose_name = '宠物眼球UV贴图记录'
        verbose_name_plural = '宠物眼球UV贴图记录'
        # 默认按创建时间倒序
        ordering = ['-created_at']

    def __str__(self):
        # 展示主键 + 状态
        return f'{self.pet_eye_uv_id} ({self.workflow_status})'
