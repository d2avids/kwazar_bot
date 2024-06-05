from datetime import datetime
from sqlalchemy import select
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from utils.constants import TASK_ANSWER_TEXT, GROUP_TYPE, INDIVIDUAL_TYPE, TEAM_TASK_ANSWER_TEXT

from database.models import Task, User, UserAnswer, Team, GroupTaskAnswer
from utils.decorators import with_db_session


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
            await update.message.reply_text('Вы не зарегистрированы в системе')
            return ConversationHandler.END

        if not user.is_verified:
            await update.message.reply_text('Ваша регистрация не подтверждена')
            return ConversationHandler.END

        stmt = select(Task).filter_by(type=INDIVIDUAL_TYPE, is_finished=False)
        result = await db_session.execute(stmt)
        task = result.scalars().first()

        if not task:
            await update.message.reply_text('Нет активных индивидуальных заданий')
            return ConversationHandler.END

        context.user_data['user'] = user
        await update.message.reply_text('Введите текст ответа на задание')
        return TASK_ANSWER_TEXT

    @with_db_session
    @staticmethod
    async def receive_task_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
        answer_text = update.message.text
        user = context.user_data['user']
        db_session = context.chat_data['db_session']

        stmt = select(Task).filter_by(type='individual', is_finished=False)
        result = await db_session.execute(stmt)
        task = result.scalars().first()

        if not task:
            await update.message.reply_text('Нет активных индивидуальных заданий')
            return ConversationHandler.END

        current_time = datetime.now()
        if task.getting_answers_time and current_time < task.getting_answers_time:
            await update.message.reply_text(
                f'Ответ на задание можно отправить не ранее {task.getting_answers_time.strftime("%d.%m.%Y %H:%M")}'
            )
            return ConversationHandler.END

        if task.deadline and current_time > task.deadline:
            await update.message.reply_text(
                f'Срок сдачи задания истек {task.deadline.strftime("%d.%m.%Y %H:%M")}'
            )
            return ConversationHandler.END

        existing_answer_stmt = select(UserAnswer).filter_by(user_id=user.id, task_id=task.id)
        existing_answer_result = await db_session.execute(existing_answer_stmt)
        existing_answer = existing_answer_result.scalars().first()

        if existing_answer:
            await update.message.reply_text(
                'Вами уже был дан ответ на текущее задание. '
                'Повторная сдача ответа на задание не допускается'
            )
            return ConversationHandler.END

        new_answer = UserAnswer(
            user_id=user.id,
            task_id=task.id,
            answer_text=answer_text
        )
        db_session.add(new_answer)
        await db_session.commit()

        await update.message.reply_text('Ваш ответ принят')
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
            await update.message.reply_text('Нет активных групповых заданий')
            return ConversationHandler.END

        current_time = datetime.now()
        if current_time < task.getting_answers_time:
            await update.message.reply_text(
                f'Ответ на задание можно отправить не ранее {task.getting_answers_time.strftime("%d.%m.%Y %H:%M")}. '
                f'Текущее время: {current_time}'
            )
            return ConversationHandler.END

        if task.deadline and current_time > task.deadline:
            await update.message.reply_text(
                f'Срок сдачи задания истек {task.deadline.strftime("%d.%m.%Y %H:%M")}'
            )
            return ConversationHandler.END

        team_id = update.message.chat.id

        stmt = select(Team).filter_by(telegram_id=team_id)
        result = await db_session.execute(stmt)
        team = result.scalars().first()

        if not team:
            await update.message.reply_text('Команда не зарегистрирована в системе')
            return ConversationHandler.END

        context.user_data['team'] = team
        await update.message.reply_text('Введите текст ответа на групповое задание')
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
            await update.message.reply_text('Нет активных групповых заданий')
            return ConversationHandler.END

        existing_answer_stmt = select(GroupTaskAnswer).filter_by(team_id=team.id, task_id=task.id)
        existing_answer_result = await db_session.execute(existing_answer_stmt)
        existing_answer = existing_answer_result.scalars().first()

        if existing_answer:
            await update.message.reply_text(
                'На это задание уже был дан ответ вашей командой. '
                'Повторная сдача ответа на задание не допускается'
            )
            return ConversationHandler.END

        new_answer = GroupTaskAnswer(
            team_id=team.id,
            task_id=task.id,
            answer_text=answer_text
        )
        db_session.add(new_answer)
        await db_session.commit()

        await update.message.reply_text('Ответ вашей команды принят')
        return ConversationHandler.END
