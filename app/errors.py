import logging
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
) -> JSONResponse:
    correlation_id = str(uuid4())

    payload = {
        "type": type_,
        "title": title,
        "status": status_code,
        "detail": detail,
        "correlation_id": correlation_id,
    }

    if extras:
        payload.update(extras)

    logger.error(
        "API Error",
        extra={
            "correlation_id": correlation_id,
            "status_code": status_code,
            "title": title,
            "detail": detail,
            "type": type_,
        },
    )

    return JSONResponse(status_code=status_code, content=payload)


class ProblemDetailException(Exception):
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        title: str = "Internal Server Error",
        detail: str = "An unexpected error occurred",
        type_: str = "about:blank",
        extras: Dict[str, Any] | None = None,
    ):
        self.status_code = status_code
        self.title = title
        self.detail = detail
        self.type_ = type_
        self.extras = extras or {}


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
