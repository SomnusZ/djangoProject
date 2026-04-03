"""
浠诲姟鍔ㄤ綔鍏崇郴瑙嗗浘鏂囦欢銆
鍖呭惈鍔ㄤ綔涓庝换鍔＄殑缁戝畾銆佽В缁戙佹寜浠诲姟鏌ヨ㈠姩浣滃垪琛ㄣ
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action

from app.utils import success_response, error_response
from app.permissions import OwnedObjectMixin, OwnedQuerySetMixin
from app.user_task.models import UserTask
from app.pet_action.models import PetAction

from .models import UserTaskActionRelation
from .serializers import (
    BindActionToTaskSerializer,
    UnbindActionFromTaskSerializer,
    DirActionListByTaskSerializer,
)
from app.pet_action.serializers import PetActionSerializer


class UserTaskActionRelationViewSet(OwnedQuerySetMixin, OwnedObjectMixin, viewsets.GenericViewSet):
    """
    浠诲姟鍔ㄤ綔鍏崇郴鎺ュ彛瑙嗗浘闆嗐
    鍖呭惈缁戝畾鍔ㄤ綔鍒颁换鍔°佽В缁戝姩浣溿佹寜浠诲姟鏌ヨ㈠姩浣滃垪琛ㄣ
    """

    queryset = UserTaskActionRelation.objects.all()
    # 褰掑睘瀛楁碉紙閫氳繃 user_task 鍏宠仈鐢ㄦ埛锛
    owner_field = 'user_task__user'

    @action(detail=False, methods=['post'], url_path='bindActionToTask')
    def bind_action_to_task(self, request):
        """
        缁戝畾鍔ㄤ綔鍒颁换鍔℃帴鍙ｃ
        璇锋眰浣撶ず渚嬶細
        {
            "user_task_id": 1,
            "pet_action_id": 2
        }
        """
        serializer = BindActionToTaskSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        # 鍙鍏佽哥粦瀹氬埌鑷宸卞悕涓嬬殑浠诲姟
        user_task_id = serializer.validated_data['user_task_id']
        user_task, denied = self.get_owned_or_403(
            request,
            UserTask.objects.all(),
            not_found_msg='浠诲姟涓嶅瓨鍦',
            user_task_id=user_task_id,
        )
        if denied:
            return denied

        relation = serializer.save()
        if relation.user_task_id != getattr(user_task, 'user_task_id', None):
            return error_response('鏃犳潈闄', status_code=status.HTTP_403_FORBIDDEN)

        data = {
            'relation_id': relation.relation_id,
            'user_task_id': relation.user_task_id,
            'pet_action_id': relation.pet_action_id,
        }
        return success_response(data, message='缁戝畾鎴愬姛', status_code=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='unbindActionFromTask')
    def unbind_action_from_task(self, request):
        """
        瑙ｇ粦鍔ㄤ綔涓庝换鍔℃帴鍙ｃ
        璇锋眰浣撶ず渚嬶細
        {
            "user_task_id": 1,
            "pet_action_id": 2
        }
        """
        serializer = UnbindActionFromTaskSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        # 鍙鍏佽歌В缁戣嚜宸卞悕涓嬬殑浠诲姟
        user_task_id = serializer.validated_data['user_task_id']
        user_task, denied = self.get_owned_or_403(
            request,
            UserTask.objects.all(),
            not_found_msg='浠诲姟涓嶅瓨鍦',
            user_task_id=user_task_id,
        )
        if denied:
            return denied

        pet_action_id = serializer.validated_data['pet_action_id']
        relation = UserTaskActionRelation.objects.filter(user_task=user_task, pet_action_id=pet_action_id).first()
        if not relation:
            return error_response('鍏宠仈涓嶅瓨鍦', status_code=status.HTTP_404_NOT_FOUND)

        relation.delete()
        data = {
            'user_task_id': user_task_id,
            'pet_action_id': pet_action_id,
        }
        return success_response(data, message='瑙ｇ粦鎴愬姛')

    @action(detail=False, methods=['get'], url_path='dirActionListByTask')
    def dir_action_list_by_task(self, request):
        """
        鏍规嵁浠诲姟鏌ヨ㈠姩浣滃垪琛ㄦ帴鍙ｃ
        鏌ヨ㈠弬鏁扮ず渚嬶細
        /api/task-actions/dirActionListByTask/?user_task_id=1
        """
        serializer = DirActionListByTaskSerializer(data=request.query_params)
        if not serializer.is_valid():
            return error_response(serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

        user_task_id = serializer.validated_data['user_task_id']
        user_task, denied = self.get_owned_or_403(
            request,
            UserTask.objects.all(),
            not_found_msg='浠诲姟涓嶅瓨鍦',
            user_task_id=user_task_id,
        )
        if denied:
            return denied

        action_ids = UserTaskActionRelation.objects.filter(user_task=user_task).values_list('pet_action_id', flat=True)
        actions_qs = PetAction.objects.filter(pet_action_id__in=action_ids).order_by('-pet_action_id')
        data = PetActionSerializer(actions_qs, many=True).data
        return success_response(data, message='鏌ヨ㈡垚鍔')
