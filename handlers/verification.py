from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from utils.constants import VERIFICATION_MESSAGE, VERIFICATION_PROCESS, VERIFICATION_ACCEPT_COMMAND, \
    VERIFICATION_REJECT_COMMAND
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
        print(f'Получены не верифицированные пользователи: {not_verified_users}')
        message = (
            'Вывод в формате <i>ID, ФИО, название школы, '
            'цифра-буква класса, номер попытки регистрации, дата последней попытки</i>:\n\n'
        ) if not_verified_users else 'Сейчас нет пользователей, ожидающих верификацию'
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
            await update.message.reply_text(
                f'Неправильная команда. Используйте "{VERIFICATION_ACCEPT_COMMAND}" '
                f'или "{VERIFICATION_REJECT_COMMAND}".'
            )
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
                    await update.message.reply_text(
                        f'Пользователь с ID {user_id} не найден или не ожидает верификации.'
                    )
            except ValueError:
                await update.message.reply_text(f'Недопустимый ID пользователя: {user_id}')

        if not valid_ids:
            await update.message.reply_text('Нет действительных ID для обработки. Пожалуйста, введите корректные ID.')
            return VERIFICATION_PROCESS

        for user in valid_ids:
            if action == VERIFICATION_ACCEPT_COMMAND.lower():
                user.is_verified = True
                try:
                    await context.bot.send_message(
                        chat_id=user.telegram_id, text='Ваша регистрация подтверждена администратором!'
                    )
                except Exception:
                    pass
            else:
                try:
                    await context.bot.send_message(
                        chat_id=user.telegram_id,
                        text='Администратор отклонил вашу заявку на регистрацию'
                    )
                except Exception:
                    pass
            user.verification_waiting = False
            db_session.add(user)

        await db_session.commit()
        await update.message.reply_text(
            f'Успешно обработаны пользователи с ID {", ".join([str(user.id) for user in valid_ids])}.')
        return ConversationHandler.END
