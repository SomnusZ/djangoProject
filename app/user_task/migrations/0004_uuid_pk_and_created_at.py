"""
手工迁移：
1. user_task_id: AutoField(int) → CharField(UUID 字符串)
2. 新增 created_at（auto_now_add），旧行填充当前时间
3. 更新 workflow_status 的 choices 和 default
"""

import uuid
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_task', '0003_add_workflow_fields'),
    ]

    operations = [
        # ── 1. 把整数主键改为 UUID 字符串主键 ────────────────────────────
        #   SQLite 会重建表，旧行的整数 id 会被原样转为字符串（"1"/"2"…）
        #   新行由业务层在 views.py 中预先生成 UUID 后传入
        migrations.AlterField(
            model_name='usertask',
            name='user_task_id',
            field=models.CharField(
                db_column='user_task_id',
                default=uuid.uuid4,
                editable=False,
                max_length=36,
                primary_key=True,
                serialize=False,
                verbose_name='任务ID',
            ),
        ),

        # ── 2. 新增 created_at ──────────────────────────────────────────
        #   preserve_default=False：迁移完成后移除 default，
        #   模型层 auto_now_add=True 接管新行的写入
        migrations.AddField(
            model_name='usertask',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
                verbose_name='创建时间',
            ),
            preserve_default=False,
        ),

        # ── 3. 更新 workflow_status choices / default ───────────────────
        migrations.AlterField(
            model_name='usertask',
            name='workflow_status',
            field=models.CharField(
                choices=[
                    ('pending',            '待开始'),
                    ('cleaned',            '图片已预处理'),
                    ('meshy_pending',      'Meshy任务已提交'),
                    ('IN_PROGRESS',        'Meshy生成中'),
                    ('resubmit_pending',   '重试提交中'),
                    ('meshy_done',         'Meshy完成'),
                    ('TEXTURE_PROCESSING', '贴图处理中'),
                    ('DONE',               '全部完成'),
                    ('FAILED',             'Meshy失败'),
                    ('ERROR',              '本地错误'),
                ],
                default='cleaned',
                max_length=32,
                verbose_name='工作流状态',
            ),
        ),
    ]
