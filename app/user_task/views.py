"""
用户任务视图文件。
包含任务相关接口：createUserTask、updateUserTask、dirUserTask、dirUserTaskListByUser。
AI 宠物工作流接口：createUserTask（含图片预处理+Meshy提交）、queryMeshyTask。
"""

import uuid
from pathlib import Path

from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser

from app.utils import success_response, error_response
from app.permissions import IsOwnerPermission, OwnedObjectMixin, OwnedQuerySetMixin, get_user_from_request
from rest_framework.permissions import AllowAny

from .models import UserTask
from .serializers import (
    UserTaskSerializer,
    UpdateUserTaskSerializer,
    DirUserTaskQuerySerializer,
)

from aipet.task_workflow import preprocess_image
from aipet.task_workflow import meshy as workflow_meshy
from aipet.task_workflow import meshy_status as workflow_meshy_status
from aipet.photo_to_uv_texture import generate_eye_uv_texture

# 工作流涉及的所有数据库字段，view 层统一用这个列表做 update_fields
_WORKFLOW_FIELDS = [
    'workflow_status', 'image_path', 'pet_breed', 'pet_type',
    'meshy_job_id', 'meshy_retry_count', 'texture_clean_path', 'workflow_error',
]


class UserTaskViewSet(OwnedQuerySetMixin, OwnedObjectMixin, viewsets.GenericViewSet):
    """
    用户任务接口视图集。
    """

    queryset = UserTask.objects.all()
    # permission_classes = [IsOwnerPermission]  # 原逻辑：JWT 权限校验
    # 临时兼容：前端未接入 token，放行后由视图层通过手机号解析用户
    permission_classes = [AllowAny]
    owner_field = 'user'

    def get_queryset(self):
        # 临时兼容：优先 token，取不到则从请求参数 user_phone_number 解析用户
        # 原逻辑由 OwnedQuerySetMixin.get_queryset() 通过 request.user 过滤
        user = get_user_from_request(self.request)
        if user is None:
            return UserTask.objects.none()
        return UserTask.objects.filter(user=user)

    @action(detail=False, methods=['post'], url_path='createUserTask',
            parser_classes=[MultiPartParser])
    def create_user_task(self, request):
        """
        上传图片并启动 AI 宠物生成流程。
        task 在注册时已预创建，此接口取已有 task 写入图片处理结果。
        流程：校验图片 → 图片预处理 → 更新已有 UserTask → 提交 Meshy

        表单字段：
          - image: 宠物图片（file，≤5MB）
        """
        # 临时兼容：优先 token，取不到则从请求体 user_phone_number 解析用户
        # request_user = request.user  # 原逻辑
        request_user = get_user_from_request(request)
        if request_user is None:
            return error_response('用户不存在或未提供身份信息', status_code=status.HTTP_200_OK, result='unexit')

        # task_name 不再要求前端传入，自动用手机号生成（已废弃，task 在注册时预创建）
        # task_name = request.data.get('task_name', '').strip()  # 原逻辑
        # if not task_name:
        #     return error_response('请提供 task_name', status_code=status.HTTP_400_BAD_REQUEST)  # 原逻辑
        # task_name = request.data.get('task_name', '').strip() or request_user.user_phone_number  # 手机号自动生成逻辑

        image_file = request.FILES.get('image')
        if not image_file:
            return error_response('请上传 image 文件', status_code=status.HTTP_200_OK, result='imgNone')
        if not image_file.content_type.startswith('image/'):
            return error_response('只支持图片文件', status_code=status.HTTP_200_OK, result='imgOnly')
        if image_file.size > 5 * 1024 * 1024:
            return error_response('图片不能超过 5MB', status_code=status.HTTP_200_OK, result='tooLarge')

        # 取注册时预创建的 task（一个用户下只有一个 task）
        # 原逻辑：task_name 唯一性校验 + UserTask.objects.create(...) 新建
        # if UserTask.objects.filter(user=request_user, task_name=task_name).exists():
        #     return error_response('任务名已存在', status_code=status.HTTP_409_CONFLICT, result='tasknameexist')
        # task_id = str(uuid.uuid4())
        task_obj = self.get_queryset().first()
        if task_obj is None:
            return error_response('当前用户暂无任务，请联系管理员', status_code=status.HTTP_200_OK, result='taskNone')

        task_id = task_obj.user_task_id
        file_bytes = image_file.read()

        # ① 图片预处理
        ok, clean_data = preprocess_image(task_id, file_bytes)
        if not ok:
            code = clean_data.get('code', '')
            if code == 'no_pet_detected':
                return error_response(clean_data['detail'], status_code=status.HTTP_200_OK, result="undetected")
            return error_response(clean_data['detail'], status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, result='fail')

        # ② 预处理成功，更新已有 UserTask，并将用户状态更新为 1
        # 原逻辑：UserTask.objects.create(user_task_id=task_id, user=request_user, task_name=task_name, ...)
        task_obj.workflow_status = 'cleaned'
        task_obj.image_path = clean_data['image_path']
        task_obj.pet_breed = clean_data['pet_breed']
        task_obj.pet_type = clean_data['pet_type']
        task_obj.save(update_fields=['workflow_status', 'image_path', 'pet_breed', 'pet_type'])

        # 用户状态改为1，即用户成功完成图片上传但未收到贴图的状态
        # request.user.user_status = 1  # 原逻辑
        # request.user.save(update_fields=['user_status'])  # 原逻辑
        request_user.user_status = 1
        request_user.save(update_fields=['user_status'])

        # ④ 提交 Meshy
        _CAT_SIZE_MAP = {10: 'Cat_M', 20: 'Cat_L', 30: 'Cat_XL'}
        _CAT_SIZE_MODEL_MAP = {10: 1, 20: 2, 30: 3}
        cat_size_id = int(request.data.get('CatSizeID', 20))
        cat_size = _CAT_SIZE_MAP.get(cat_size_id, 'Cat_L')
        ok, meshy_data = workflow_meshy(task_obj, cat_size=cat_size)
        task_obj.pet_model_id = _CAT_SIZE_MODEL_MAP.get(cat_size_id, 0)
        task_obj.save(update_fields=_WORKFLOW_FIELDS + ['pet_model_id'])

        if not ok:
            # Meshy 提交失败，任务已创建但状态为 ERROR，客户端可查询得知原因
            return error_response(meshy_data['detail'], status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, result='fail')

        return success_response({
            'task_id':         task_obj.user_task_id,
            'task_name':       task_obj.task_name,
            'workflow_status': task_obj.workflow_status,
            'meshy_job_id':    task_obj.meshy_job_id,
            'pet_breed':       task_obj.pet_breed,
            'pet_type':        task_obj.pet_type,
        }, message='任务创建成功', status_code=status.HTTP_201_CREATED)

    @action(detail=False, methods=['put', 'patch'], url_path='updateUserTask')
    def update_user_task(self, request):
        """
        用户任务修改接口。
        仅允许修改 task_name。
        请求体示例：
        {
            "user_task_id": "uuid-string",
            "task_name": "新的任务名"
        }
        """
        user_task_id = request.data.get('user_task_id')
        if not user_task_id:
            return error_response('请提供 user_task_id', status_code=status.HTTP_400_BAD_REQUEST)

        task_obj, denied = self.get_owned_or_403(
            request,
            self.get_queryset(),
            not_found_msg='任务不存在',
            user_task_id=user_task_id,
        )
        if denied:
            return denied

        update_data = request.data.copy()
        update_data.pop('user_task_id', None)

        serializer = UpdateUserTaskSerializer(task_obj, data=update_data, partial=True)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return success_response(UserTaskSerializer(task_obj).data, message='修改成功')

    @action(detail=False, methods=['get'], url_path='dirUserTask')
    def dir_user_task(self, request):
        """
        用户任务信息查询接口。
        查询参数示例：
        /api/models/dirUserTask/?user_task_id=uuid-string
        """
        serializer = DirUserTaskQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        user_task_id = serializer.validated_data['user_task_id']
        task_obj, denied = self.get_owned_or_403(
            request,
            self.get_queryset(),
            not_found_msg='任务不存在',
            user_task_id=user_task_id,
        )
        if denied:
            return denied

        return success_response(UserTaskSerializer(task_obj).data, message='查询成功')

    @action(detail=False, methods=['get'], url_path='dirUserTaskListByUser')
    def dir_user_task_list_by_user(self, request):
        """
        查询当前登录用户的任务列表接口（按创建时间倒序）。
        """
        tasks_qs = self.get_queryset().order_by('-created_at')
        data = UserTaskSerializer(tasks_qs, many=True).data
        return success_response(data, message='查询成功')

    @action(detail=False, methods=['get'], url_path='queryMeshyTask')
    def query_meshy_task(self, request):
        """
        轮询 Meshy 任务状态，推进工作流直到完成。
        user_task 由 token 中的 user_id 关联查询，无需传 user_task_id。
        """
        # 临时兼容：优先 token，取不到则从 query 参数 user_phone_number 解析用户
        # request_user = request.user  # 原逻辑
        request_user = get_user_from_request(request)
        if request_user is None:
            return error_response('用户不存在或未提供身份信息', status_code=status.HTTP_401_UNAUTHORIZED)

        task_obj = self.get_queryset().first()
        if task_obj is None:
            return error_response('当前用户暂无任务', status_code=status.HTTP_200_OK, result='taskNone')

        ok, data = workflow_meshy_status(task_obj)
        task_obj.save(update_fields=_WORKFLOW_FIELDS)

        if not ok:
            return error_response(data['detail'], status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, result='fail')

        # 用户状态改为2，即用户成功完成图片上传且收到贴图的状态
        # 目前是在轮询逻辑中更新，如果不轮询或轮询中断，状态无法变更，在生产环境中是个风险
        if data.get('workflow_status') == 'DONE':
            # request.user.user_status = 2  # 原逻辑
            # request.user.save(update_fields=['user_status'])  # 原逻辑
            request_user.user_status = 2
            request_user.save(update_fields=['user_status'])

        # 兜底：若 workflow 返回的 texture_download_url 为空或缺失，
        # 则从数据库中的 texture_clean_path 推导，与 dirTaskResult 逻辑完全一致
        if not data.get('texture_download_url') and task_obj.texture_clean_path:
            relative = task_obj.texture_clean_path.split('meshy/')[-1]
            data['texture_download_url'] = f"{settings.MESHY_SERVER_URL}/meshy_images/{relative}"

        data['user_status'] = request_user.user_status  # 原逻辑: request.user.user_status

        # 暂时均返回base模型贴图, l和xl型号猫返回覆盖眼睛后的贴图
        if task_obj.pet_model_id in [2, 3]:
            data['texture_download_url'] = f"{settings.MESHY_SERVER_URL}/meshy_images/{task_obj.user_task_id}/UV_with_round_eyes.png"
        else:
            data['texture_download_url'] = f"{settings.MESHY_SERVER_URL}/meshy_images/{task_obj.user_task_id}/texture_0_base_color.png"
        return success_response(data, message='查询成功')

    @action(detail=False, methods=['get'], url_path='dirPetModelId')
    def dir_pet_model_id(self, request):
        """
        查询用户任务的 pet_model_id。
        user_task 由 token 中的 user_id 关联查询，无需传 user_task_id。
        """
        task_obj = self.get_queryset().first()
        if task_obj is None:
            return error_response('当前用户暂无任务', status_code=status.HTTP_404_NOT_FOUND)

        return success_response(
            {'user_task_id': task_obj.user_task_id, 'pet_model_id': task_obj.pet_model_id},
            message='查询成功',
        )

    @action(detail=False, methods=['put', 'patch'], url_path='updatePetModelId')
    def update_pet_model_id(self, request):
        """
        更新当前用户任务的 pet_model_id。
        user_task 由 token 中的 user_id 关联查询，无需传 user_task_id。
        仅出版本适用于user下只有一个user_task
        请求体示例：
        {
            "pet_model_id": 1
        }
        """
        pet_model_id = request.data.get('pet_model_id')
        if pet_model_id is None:
            return error_response('请提供 pet_model_id', status_code=status.HTTP_400_BAD_REQUEST)
        if not isinstance(pet_model_id, int):
            return error_response('pet_model_id 必须为整数', status_code=status.HTTP_400_BAD_REQUEST)

        task_obj = self.get_queryset().first()
        if task_obj is None:
            return error_response('当前用户暂无任务', status_code=status.HTTP_404_NOT_FOUND)

        task_obj.pet_model_id = pet_model_id
        task_obj.save(update_fields=['pet_model_id'])

        return success_response(
            {'user_task_id': task_obj.user_task_id, 'pet_model_id': task_obj.pet_model_id},
            message='更新成功',
        )

    @action(detail=False, methods=['get'], url_path='dirTaskResult')
    def dir_task_result(self, request):
        """
        查询当前用户已完成任务的贴图下载地址。
        从数据库读取 texture_clean_path，拼接服务器地址返回 texture_download_url。
        仅返回 workflow_status=DONE 的任务结果。
        临时兼容：优先 token，取不到则从 query 参数 user_phone_number 解析用户。
        """
        request_user = get_user_from_request(request)
        if request_user is None:
            return error_response('用户不存在或未提供身份信息', status_code=status.HTTP_401_UNAUTHORIZED)

        task_obj = self.get_queryset().filter(workflow_status='DONE').first()
        if task_obj is None:
            return error_response('暂无已完成的任务', status_code=status.HTTP_404_NOT_FOUND, result='notdone')

        # 将本地路径转换为可访问的 URL
        # texture_clean_path 示例：/www/wwwroot/djangoProject/aipet/3Dmodels/meshy/<uuid>/texture_clean.png
        # nginx 映射：/meshy_images/ -> /www/wwwroot/djangoProject/aipet/3Dmodels/meshy/
        # 转换后 URL：http://42.193.98.94/meshy_images/<uuid>/texture_clean.png
        relative = task_obj.texture_clean_path.split('meshy/')[-1]
        texture_download_url = f"{settings.MESHY_SERVER_URL}/meshy_images/{relative}"

        return success_response(
            {
                'task_id': task_obj.user_task_id,
                'workflow_status': task_obj.workflow_status,
                'texture_download_url': texture_download_url,
            },
            message='查询成功',
        )

    @action(detail=False, methods=['post'], url_path='generateEyeUvTexture',
            parser_classes=[MultiPartParser])
    def generate_eye_uv_texture_view(self, request):
        """
        测试接口：前端上传猫咪图片，生成眼球 UV 贴图。
        图片保存至 aipet/photo_to_uv_texture/UserImage/，结果直接返回给前端。
        """
        image_file = request.FILES.get('image')
        if not image_file:
            return error_response('请上传 image 文件', status_code=status.HTTP_200_OK)
        if not image_file.content_type.startswith('image/'):
            return error_response('只支持图片文件', status_code=status.HTTP_200_OK)

        _USERIMAGE_DIR = Path(__file__).resolve().parent.parent.parent / 'aipet' / 'photo_to_uv_texture' / 'UserImage'
        _USERIMAGE_DIR.mkdir(parents=True, exist_ok=True)

        suffix = Path(image_file.name).suffix or '.jpg'
        filename = f"{uuid.uuid4()}{suffix}"
        save_path = _USERIMAGE_DIR / filename

        with open(save_path, 'wb') as f:
            for chunk in image_file.chunks():
                f.write(chunk)

        result = generate_eye_uv_texture(str(save_path))

        # 把 recolored_path 本地绝对路径转为可访问的 URL
        # nginx 映射：/eye_uv_images/ -> aipet/photo_to_uv_texture/output/
        for item in result.get("recolored_results", []):
            if item.get("ok") and item.get("recolored_path"):
                relative = item["recolored_path"].replace("\\", "/").split("output/")[-1]
                item["recolored_url"] = f"{settings.MESHY_SERVER_URL}/eye_uv_images/{relative}"

        return success_response(result, message='生成成功')
