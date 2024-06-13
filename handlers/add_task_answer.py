from sqlalchemy import select
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from database.models import GroupTaskAnswer, Task, Team, User, UserAnswer
from utils.constants import (ANSWER_ACCEPTED, ANSWER_ALREADY_SUBMITTED,
                             ANSWER_NOT_ALLOWED_YET, DEADLINE_PASSED,
                             ENTER_GROUP_TASK_ANSWER_TEXT,
                             ENTER_TASK_ANSWER_TEXT, GROUP_ANSWER_ACCEPTED,
                             GROUP_ANSWER_ALREADY_SUBMITTED, GROUP_TYPE,
                             INDIVIDUAL_TYPE, NO_ACTIVE_GROUP_TASKS,
                             NO_ACTIVE_INDIVIDUAL_TASKS, NOT_REGISTERED,
                             REGISTRATION_NOT_CONFIRMED, TASK_ANSWER_TEXT,
                             TEAM_NOT_REGISTERED, TEAM_TASK_ANSWER_TEXT)
from utils.decorators import with_db_session
from utils.utils import get_current_datetime


class AddTaskUserAnswer:

    @with_db_session
    @staticmethod
    async def prompt_task_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
        db_session = context.chat_data['db_session']
        user_id = update.message.from_user.id
        stmt = select(User).filter_by(telegram_id=user_id)
        result = await db_session.execute(stmt)
        user = result.scalars().first()

        if not user:
            await update.message.reply_text(NOT_REGISTERED)
            return ConversationHandler.END

        if not user.is_verified:
            await update.message.reply_text(REGISTRATION_NOT_CONFIRMED)
            return ConversationHandler.END

        stmt = select(Task).filter_by(type=INDIVIDUAL_TYPE, is_finished=False)
        result = await db_session.execute(stmt)
        task = result.scalars().first()

        if not task:
            await update.message.reply_text(NO_ACTIVE_INDIVIDUAL_TASKS)
            return ConversationHandler.END

        context.user_data['user'] = user
        await update.message.reply_text(ENTER_TASK_ANSWER_TEXT)
        return TASK_ANSWER_TEXT

    @with_db_session
    @staticmethod
    async def receive_task_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
        answer_text = update.message.text
        user = context.user_data['user']
        db_session = context.chat_data['db_session']

        stmt = select(Task).filter_by(type=INDIVIDUAL_TYPE, is_finished=False)
        result = await db_session.execute(stmt)
        task = result.scalars().first()

        if not task:
            await update.message.reply_text(NO_ACTIVE_INDIVIDUAL_TASKS)
            return ConversationHandler.END

        current_time = get_current_datetime()
        if task.getting_answers_time and current_time < task.getting_answers_time:
            await update.message.reply_text(
                ANSWER_NOT_ALLOWED_YET.format(
                    task_time=task.getting_answers_time.strftime("%d.%m.%Y %H:%M"),
                    current_time=current_time.strftime("%d.%m.%Y %H:%M")
                )
            )
            return ConversationHandler.END

        if task.deadline and current_time > task.deadline:
            await update.message.reply_text(
                DEADLINE_PASSED.format(
                    deadline=task.deadline.strftime("%d.%m.%Y %H:%M")
                )
            )
            return ConversationHandler.END

        existing_answer_stmt = select(UserAnswer).filter_by(user_id=user.id, task_id=task.id)
        existing_answer_result = await db_session.execute(existing_answer_stmt)
        existing_answer = existing_answer_result.scalars().first()

        if existing_answer:
            await update.message.reply_text(ANSWER_ALREADY_SUBMITTED)
            return ConversationHandler.END

        new_answer = UserAnswer(
            user_id=user.id,
            task_id=task.id,
            answer_text=answer_text
        )
        db_session.add(new_answer)
        await db_session.commit()

        await update.message.reply_text(ANSWER_ACCEPTED)
        return ConversationHandler.END


class AddGroupTaskAnswer:

    @staticmethod
    @with_db_session
    async def prompt_task_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
        db_session = context.chat_data['db_session']
        stmt = select(Task).filter_by(type=GROUP_TYPE, is_finished=False)
        result = await db_session.execute(stmt)
        task = result.scalars().first()

        if not task:
            await update.message.reply_text(NO_ACTIVE_GROUP_TASKS)
            return ConversationHandler.END

        current_time = get_current_datetime()
        if current_time < task.getting_answers_time:
            await update.message.reply_text(
                ANSWER_NOT_ALLOWED_YET.format(
                    task_time=task.getting_answers_time.strftime("%d.%m.%Y %H:%M"),
                    current_time=current_time.strftime("%d.%m.%Y %H:%M")
                )
            )
            return ConversationHandler.END

        if task.deadline and current_time > task.deadline:
            await update.message.reply_text(
                DEADLINE_PASSED.format(
                    deadline=task.deadline.strftime("%d.%m.%Y %H:%M")
                )
            )
            return ConversationHandler.END

        team_id = update.message.chat.id

        stmt = select(Team).filter_by(telegram_id=team_id)
        result = await db_session.execute(stmt)
        team = result.scalars().first()

        if not team:
            await update.message.reply_text(TEAM_NOT_REGISTERED)
            return ConversationHandler.END

        context.user_data['team'] = team
        await update.message.reply_text(ENTER_GROUP_TASK_ANSWER_TEXT)
        return TEAM_TASK_ANSWER_TEXT

    @staticmethod
    @with_db_session
    async def receive_task_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
        answer_text = update.message.text
        team = context.user_data['team']
        db_session = context.chat_data['db_session']

        stmt = select(Task).filter_by(type=GROUP_TYPE, is_finished=False)
        result = await db_session.execute(stmt)
        task = result.scalars().first()

        if not task:
            await update.message.reply_text(NO_ACTIVE_GROUP_TASKS)
            return ConversationHandler.END

        existing_answer_stmt = select(GroupTaskAnswer).filter_by(team_id=team.id, task_id=task.id)
        existing_answer_result = await db_session.execute(existing_answer_stmt)
        existing_answer = existing_answer_result.scalars().first()

        if existing_answer:
            await update.message.reply_text(GROUP_ANSWER_ALREADY_SUBMITTED)
            return ConversationHandler.END

        new_answer = GroupTaskAnswer(
            team_id=team.id,
            task_id=task.id,
            answer_text=answer_text
        )
        db_session.add(new_answer)
        await db_session.commit()

        await update.message.reply_text(GROUP_ANSWER_ACCEPTED)
        return ConversationHandler.END
