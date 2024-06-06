from sqlalchemy import select
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from utils.constants import ADD_TUTOR_SUCCESS, ADD_TUTOR, ASK_ID_TUTOR_TO_ADD, CANCEL_ACTION, CANCEL_BUTTON, \
    INCORRECT_ID, TUTOR_ID_NOT_FOUND
from utils.decorators import with_db_session, admin_required
from database.models import User


class AddTutor:
    @staticmethod
    @admin_required
    async def ask_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> ADD_TUTOR:
        reply_markup = ReplyKeyboardMarkup(CANCEL_BUTTON, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(ASK_ID_TUTOR_TO_ADD, reply_markup=reply_markup)
        return ADD_TUTOR

    @staticmethod
    @with_db_session
    async def add_tutor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> ConversationHandler.END:
        tutor_id = update.message.text
        if tutor_id == CANCEL_ACTION:
            return ConversationHandler.END
        if not tutor_id.isdigit():
            await update.message.reply_text(INCORRECT_ID.format(id=tutor_id))
            return ConversationHandler.END
        db_session = context.chat_data['db_session']
        stmt = select(User).filter_by(id=tutor_id)
        result = await db_session.execute(stmt)
        user = result.scalars().first()
        if not user:
            await update.message.reply_text(TUTOR_ID_NOT_FOUND.format(id=tutor_id))
            return ConversationHandler.END
        user.is_curator = True
        await db_session.commit()
        await update.message.reply_text(ADD_TUTOR_SUCCESS)
        return ConversationHandler.END
