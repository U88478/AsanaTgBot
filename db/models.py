from traitlets import Bool
from utils.config import db_url
from sqlalchemy import Boolean, Column, String, BigInteger, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Users(Base):
    __tablename__ = 'Users'

    tg_id = Column(BigInteger, primary_key=True)
    tg_first_name = Column(String, nullable=False)
    tg_username = Column(String, nullable=True)
    asana_token = Column(String, nullable=True)
    asana_refresh_token = Column(String, nullable=True)
    asana_id = Column(String, nullable=False)


class DefaultSettings(Base):
    __tablename__ = 'DefaultSettings'

    chat_id = Column(BigInteger, primary_key=True)
    workspace_id = Column(String, nullable=False)
    workspace_name = Column(String, nullable=False)
    project_id = Column(String, nullable=True)
    project_name = Column(String, nullable=True)
    section_id = Column(String, nullable=True)
    section_name = Column(String, nullable=True)
    notification_user_id = Column(BigInteger, nullable=False)
    toggle_stickers = Column(Boolean, nullable=False)


# Підключення до бази даних
engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
session = Session()

# Створення таблиць
Base.metadata.create_all(engine)

# Закриття сесії
session.close()
