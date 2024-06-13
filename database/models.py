from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from utils.utils import get_current_datetime


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=get_current_datetime())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=get_current_datetime(), onupdate=get_current_datetime())


class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(unique=True, nullable=False)
    last_name: Mapped[str] = mapped_column(String(200), nullable=False)
    first_name: Mapped[str] = mapped_column(String(200), nullable=False)
    patronymic: Mapped[str] = mapped_column(String(200), nullable=True)
    school_name: Mapped[str] = mapped_column(String(250), nullable=False)
    class_number: Mapped[int] = mapped_column(nullable=False)
    class_symbol: Mapped[str] = mapped_column(String(1), nullable=False)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)
    verification_waiting: Mapped[bool] = mapped_column(default=True, nullable=False)
    registration_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    is_curator: Mapped[bool] = mapped_column(default=False, nullable=False)
    user_teams = relationship('Team', back_populates='user')
    user_answers = relationship('UserAnswer', order_by='UserAnswer.id', back_populates='user')


class Team(Base):
    __tablename__ = 'team'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    school_name: Mapped[str] = mapped_column(String(200), nullable=False)
    class_number: Mapped[int] = mapped_column(nullable=False)
    class_symbol: Mapped[str] = mapped_column(String(1), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey('user.id'), nullable=False)
    user = relationship('User', back_populates='user_teams')
    group_task_answers = relationship('GroupTaskAnswer', back_populates='team')


class Task(Base):
    __tablename__ = 'task'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(String(), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    deadline: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    sending_task_time: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    getting_answers_time: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    is_finished: Mapped[bool] = mapped_column(default=False, nullable=False)
    user_answers = relationship('UserAnswer', order_by='UserAnswer.id', back_populates='task')
    group_task_answers = relationship('GroupTaskAnswer', back_populates='task')


class UserAnswer(Base):
    __tablename__ = 'user_answer'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), nullable=False)
    task_id: Mapped[int] = mapped_column(ForeignKey('task.id'), nullable=False)
    answer_text: Mapped[str] = mapped_column(String(), nullable=False)
    curator_feedback: Mapped[int] = mapped_column(Integer(), nullable=True)
    user = relationship('User', back_populates='user_answers')
    task = relationship('Task', back_populates='user_answers')


class GroupTaskAnswer(Base):
    __tablename__ = 'group_task_answer'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(ForeignKey('team.id'), nullable=False)
    task_id: Mapped[int] = mapped_column(ForeignKey('task.id'), nullable=False)
    answer_text: Mapped[str] = mapped_column(String(), nullable=False)
    curator_feedback: Mapped[int] = mapped_column(Integer(), nullable=True)
    team = relationship('Team', back_populates='group_task_answers')
    task = relationship('Task', back_populates='group_task_answers')
