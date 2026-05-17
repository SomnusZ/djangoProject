"""
公共响应工具。
输出 success 或 fail 结构，便于前端统一处理。
"""

from rest_framework import status
from rest_framework.response import Response


def success_response(data=None, message="操作成功", status_code=status.HTTP_200_OK):
    """
    统一成功响应格式。
    """
    return Response(
        {
            "result": "success",
            "success": True,
            "data": data,
            "message": message,
        },
        status=status_code,
    )


def error_response(message="操作失败", status_code=status.HTTP_400_BAD_REQUEST, result="fail"):
    """
    统一失败响应格式。
    result 可传入自定义标识（如 "registered"），默认为 "fail"。
    """
    return Response(
        {
            "result": result,
            "success": False,
            "data": None,
            "message": message,
        },
        status=status_code,
    )
