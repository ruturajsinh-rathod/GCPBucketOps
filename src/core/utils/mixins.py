from datetime import datetime, timezone

from fastapi.params import Query
from fastapi_pagination import Params
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column


class TimeStampMixin:
    """
    A mixin class to add timestamp fields in a model.
    """

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )


class Default100Page(Params):
    page: int = Query(1, ge=1, description="Page number")
    size: int = Query(100, ge=1, le=100, description="Page size")
