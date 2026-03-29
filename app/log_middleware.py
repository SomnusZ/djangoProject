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
        user_id = getattr(request.user, "id", None) if getattr(request, "user", None) and request.user.is_authenticated else None

        logger.info(
            f"{request.method} {request.path} "
            f"status={response.status_code} "
            f"user_id={user_id} "
            f"time={duration:.2f}ms"
        )
        return response
