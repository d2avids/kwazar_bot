import logging
from functools import wraps

from sqlalchemy import select
from telegram.ext import ConversationHandler
from database.engine import session_maker
from utils.constants import ADMIN_TELEGRAM_ID, ADMIN_ACCESS_FAILURE, NOT_CURATOR_ATTEMPT
from database.models import User


logger = logging.getLogger(__name__)


def with_db_session(func):
    @wraps(func)
    async def wrapped(update, context, *args, **kwargs):
        async with session_maker() as session:
            context.chat_data['db_session'] = session
            return await func(update, context, *args, **kwargs)
    return wrapped


def admin_required(func):
    @wraps(func)
    async def wrapped(update, context, *args, **kwargs):
        user_id = str(update.message.chat_id)
        if user_id != ADMIN_TELEGRAM_ID:
            await update.message.reply_text(ADMIN_ACCESS_FAILURE)
            return ConversationHandler.END
        return await func(update, context, *args, **kwargs)
    return wrapped


def tutor_or_admin_required(func):
    @wraps(func)
    async def wrapped(update, context, *args, **kwargs):
        async with session_maker() as session:
            user_id = update.message.chat_id
            logger.info(
                f'user_id: {user_id} | chat_id: {update.message.chat_id}, '
                f'types: chat_id - {type(update.message.chat_id)}, user_id - {type(user_id)}'
            )
            if user_id != ADMIN_TELEGRAM_ID:
                stmt = select(User).filter_by(telegram_id=user_id, is_curator=True)
                is_curator = await session.execute(stmt)
                result = is_curator.scalar_one_or_none()
                if not result:
                    await update.message.reply_text(NOT_CURATOR_ATTEMPT)
                    return ConversationHandler.END
        return await func(update, context, *args, **kwargs)
    return wrapped
