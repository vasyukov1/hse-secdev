import logging
import re
import traceback
from typing import Any, Dict
from uuid import uuid4

from fastapi import Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def problem(
    status_code: int,
    title: str,
    detail: str,
    type_: str = "about:blank",
    extras: Dict[str, Any] | None = None,
    mask_sensitive: bool = True,
) -> JSONResponse:
    correlation_id = str(uuid4())

    if mask_sensitive and detail:
        detail = re.sub(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL]", detail
        )
        detail = re.sub(
            r"\b(?:secret_|token_|key_)[A-Za-z0-9_]{10,}\b", "[TOKEN]", detail
        )

    payload = {
        "type": type_,
        "title": title,
        "status": status_code,
        "detail": detail,
        "correlation_id": correlation_id,
    }

    if extras:
        payload.update(extras)

    safe_extras = {
        k: v for k, v in (extras or {}).items() if not _is_sensitive_field(k)
    }

    logger.error(
        "API Error",
        extra={
            "correlation_id": correlation_id,
            "status_code": status_code,
            "title": title,
            "detail": detail,
            "type": type_,
            "extras": safe_extras,
        },
    )

    return JSONResponse(status_code=status_code, content=payload)


def _is_sensitive_field(field_name: str) -> bool:
    sensitive_fields = {"password", "token", "secret", "key", "authorization"}
    return any(sensitive in field_name.lower() for sensitive in sensitive_fields)


class ProblemDetailException(Exception):
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        title: str = "Internal Server Error",
        detail: str = "An unexpected error occurred",
        type_: str = "about:blank",
        extras: Dict[str, Any] | None = None,
        mask_sensitive: bool = True,
    ):
        self.status_code = status_code
        self.title = title
        self.detail = detail
        self.type_ = type_
        self.extras = extras or {}
        self.mask_sensitive = mask_sensitive


async def problem_detail_exception_handler(
    request: Request, exc: ProblemDetailException
):
    return problem(
        status_code=exc.status_code,
        title=exc.title,
        detail=exc.detail,
        type_=exc.type_,
        extras=exc.extras,
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception",
        extra={
            "correlation_id": str(uuid4()),
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc(),
        },
        exc_info=True,
    )

    return problem(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        title="Internal Server Error",
        detail="An unexpected error occurred",
        type_="https://tools.ietf.org/html/rfc9110#section-15.6.1",
        mask_sensitive=True,
    )
