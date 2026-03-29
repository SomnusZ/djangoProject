import time
import logging

logger = logging.getLogger("api")


class RequestLogMiddleware:
    """
    DRF 请求日志中间件：
    记录请求方法、路径、耗时、状态码、用户ID
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()

        response = self.get_response(request)

        duration = (time.time() - start) * 1000
        is_auth = getattr(request, "user", None) and getattr(request.user, "is_authenticated", True)
        user_id = None
        if is_auth:
            # 兼容自定义用户 user_id
            user_id = getattr(request.user, "user_id", None) or getattr(request.user, "id", None)

        logger.info(
            f"{request.method} {request.path} "
            f"status={response.status_code} "
            f"user_id={user_id} "
            f"time={duration:.2f}ms"
        )
        return response
