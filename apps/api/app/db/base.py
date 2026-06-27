from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import models here so Alembic discovers them
from app.db.models import User  # noqa: E402,F401