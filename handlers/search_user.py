from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from database.models import User
from utils.constants import (REQUEST_LAST_NAME,
                             SEARCH_USER, USERS_NOT_FOUND)
from utils.decorators import admin_required, with_db_session


class SearchUser:
    @staticmethod
    @admin_required
    async def ask_last_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> SEARCH_USER:
        await update.message.reply_text(REQUEST_LAST_NAME)
        return SEARCH_USER

    @staticmethod
    @with_db_session
    async def search_users_by_last_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> ConversationHandler.END:
        last_name = update.message.text.capitalize()
        db_session: AsyncSession = context.chat_data['db_session']
        stmt = select(User).filter(User.last_name.ilike(f"%{last_name}%"))
        result = await db_session.execute(stmt)
        users = result.scalars().all()

        if not users:
            await update.message.reply_text(USERS_NOT_FOUND)
            return ConversationHandler.END

        message = 'Найденные пользователи:\n\n'
        counter = 0
        for user in users:
            message += (
                f'ID: {user.id}, Фамилия: {user.last_name}, Имя: {user.first_name}, Отчество: {user.patronymic}\n\n'
            )
            if counter == 15:
                counter = 0
                await update.message.reply_text(message, parse_mode='HTML')
                message = ''
            counter += 1
        await update.message.reply_text(message)
        return ConversationHandler.END
