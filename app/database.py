import os

from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///cookhelper.db")
if DATABASE_URL.startswith("postgres://"):
    # some hosts (Render, Heroku-style) hand out the old "postgres://" scheme,
    # but SQLAlchemy 2.x requires "postgresql://"
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
