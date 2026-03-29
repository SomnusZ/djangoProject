"""
通用测试页面视图。
通过 /test/<name>/ 渲染 templates/<name>.html
"""

import re

from django.http import Http404
from django.shortcuts import render
from django.template import TemplateDoesNotExist
from django.template.loader import get_template

# 只允许字母、数字、下划线、中划线，防止路径穿越
_NAME_RE = re.compile(r'^[a-zA-Z0-9_-]+$')


def test_page(request, name):
    """
    通用测试页面视图。
    访问示例：/test/register/ -> 渲染 templates/register.html
    """
    if not _NAME_RE.match(name):
        raise Http404('页面不存在')

    template_name = f"{name}.html"
    try:
        get_template(template_name)
    except TemplateDoesNotExist:
        raise Http404('页面不存在')

    return render(request, template_name)
