from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response
    detail = response.data
    if isinstance(exc, ValidationError):
        response.data = {"code": "validation_error", "message": "Please correct the highlighted fields.", "fields": detail}
    elif isinstance(detail, dict) and "detail" in detail:
        response.data = {"code": getattr(exc, "default_code", "error"), "message": str(detail["detail"])}
    return response
