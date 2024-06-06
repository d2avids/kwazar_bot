from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from utils.constants import VERIFICATION_MESSAGE, VERIFICATION_PROCESS, VERIFICATION_ACCEPT_COMMAND, \
    VERIFICATION_REJECT_COMMAND, USER_REJECTED_NOTIFICATION, USER_ACCEPTED_NOTIFICATION, INCORRECT_IDS, INCORRECT_ID, \
    ID_NOT_FOUND_OR_NOT_VERIFIED, IDS_ACCEPTED, INCORRECT_COMMAND, NO_USERS_TO_VERIFY, USERS_TO_VERIFY_OUTPUT_MESSAGE
from sqlalchemy import select
from utils.decorators import with_db_session, admin_required
from database.models import User


class Verification:

    @staticmethod
    @with_db_session
    @admin_required
    async def start_verification(update: Update, context: ContextTypes.DEFAULT_TYPE):
        db_session = context.chat_data['db_session']
        stmt = select(User).filter_by(is_verified=False, verification_waiting=True)
        result = await db_session.execute(stmt)
        not_verified_users = result.scalars().all()
        message = USERS_TO_VERIFY_OUTPUT_MESSAGE if not_verified_users else NO_USERS_TO_VERIFY
        counter = 0
        for user in not_verified_users:
            user_patronymic = f' {user.patronymic}' if user.patronymic else ''
            message += (
                f'ID {user.id}, {user.last_name} {user.first_name}{user_patronymic}, '
                f'{user.school_name}, {user.class_number}-{user.class_symbol}. '
                f'{user.registration_attempts}-я попытка. '
                f'Дата последней попытки: {user.updated}\n\n'
            )
            # по 15 записей на каждое сообщение (чтобы избежать превышение лимита символов)
            if counter == 15:
                counter = 0
                await update.message.reply_text(message, parse_mode='HTML')
                message = ''
            counter += 1
        await update.message.reply_text(message, parse_mode='HTML')
        if not_verified_users:
            await update.message.reply_text(VERIFICATION_MESSAGE)
        else:
            return ConversationHandler.END
        return VERIFICATION_PROCESS

    @staticmethod
    @with_db_session
    async def process_verification(update: Update, context: ContextTypes.DEFAULT_TYPE):
        db_session = context.chat_data['db_session']
        text_parts = update.message.text.split()
        action = text_parts[0].lower()  # Принять или отклонить
        user_ids = text_parts[1:]  # Айдишники пользователей

        if action not in [VERIFICATION_ACCEPT_COMMAND.lower(), VERIFICATION_REJECT_COMMAND.lower()]:
            await update.message.reply_text(INCORRECT_COMMAND)
            return VERIFICATION_PROCESS

        valid_ids = []
        for user_id in user_ids:
            try:
                user_id = int(user_id)
                stmt = select(User).filter_by(id=user_id, verification_waiting=True)
                result = await db_session.execute(stmt)
                user = result.scalar()

                if user:
                    valid_ids.append(user)
                else:
                    await update.message.reply_text(ID_NOT_FOUND_OR_NOT_VERIFIED.format(id=user_id))
            except ValueError:
                await update.message.reply_text(INCORRECT_ID.format(id=user_id))

        if not valid_ids:
            await update.message.reply_text(INCORRECT_IDS)
            return VERIFICATION_PROCESS

        for user in valid_ids:
            if action == VERIFICATION_ACCEPT_COMMAND.lower():
                user.is_verified = True
                try:
                    await context.bot.send_message(chat_id=user.telegram_id, text=USER_ACCEPTED_NOTIFICATION)
                except Exception:
                    pass
            else:
                try:
                    await context.bot.send_message(
                        chat_id=user.telegram_id,
                        text=USER_REJECTED_NOTIFICATION
                    )
                except Exception:
                    pass
            user.verification_waiting = False
            db_session.add(user)

        await db_session.commit()
        await update.message.reply_text(IDS_ACCEPTED.format(ids=", ".join([str(user.id) for user in valid_ids])))
        return ConversationHandler.END
