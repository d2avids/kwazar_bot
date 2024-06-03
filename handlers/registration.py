from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils.constants import SURNAME, REGISTRATION_MESSAGE_SURNAME, \
    REGISTRATION_MESSAGE_NAME, NAME, REGISTRATION_MESSAGE_PATRONYMIC, PATRONYMIC, REGISTRATION_MESSAGE_SCHOOL_NAME, \
    SCHOOL_NAME, REGISTRATION_MESSAGE_CLASS_NUMBER, CLASS_NUMBER, REGISTRATION_MESSAGE_CLASS_SYMBOL, CLASS_SYMBOL, \
    FIO_VALIDATION_MESSAGE, SCHOOL_NAME_VALIDATION_MESSAGE, CLASS_NUMBER_VALIDATION_MESSAGE, \
    REGISTRATION_FINISHED_MESSAGE, REGISTRATION_CANCELED_MESSAGE, CLASS_SYMBOL_VALIDATION_MESSAGE, \
    EXCEEDED_REGISTRATION_LIMIT_MESSAGE, ADMIN_TELEGRAM_ID, NEW_USER_NOTIFICATION, MSG_PROCESS_CANCELLED, \
    MSG_TEAM_REGISTRATION_CANCELLED, MSG_TEAM_REGISTERED_SUCCESS, MSG_CONFIRM_TEAM_REGISTRATION, \
    MSG_INVALID_CLASS_SYMBOL, MSG_INVALID_CLASS_NUMBER, MSG_ENTER_CLASS_SYMBOL, MSG_ENTER_CLASS_NUMBER, \
    MSG_SCHOOL_NAME_TOO_LONG, MSG_TEAM_NAME_TOO_LONG, MSG_ENTER_SCHOOL_NAME, MSG_ENTER_TEAM_NAME, MSG_USER_NOT_VERIFIED, \
    MSG_USER_NOT_FOUND, MSG_GROUP_CHAT_ONLY, CONFIRMATION_BUTTONS, TEAM_NAME, TEAM_SCHOOL_NAME, TEAM_CLASS_NUMBER, \
    TEAM_CLASS_SYMBOL, TEAM_CONFIRMATION, MSG_CHAT_ALREADY_REGISTERED
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from utils.decorators import with_db_session
from database.models import User, Team


class Registration:
    NAME_SYMBOLS_LIMIT = 100
    SCHOOL_NAME_SYMBOLS_LIMIT = 200

    @staticmethod
    @with_db_session
    async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
        db_session: AsyncSession = context.chat_data['db_session']
        stmt = select(User).filter_by(telegram_id=update.message.chat_id)
        result = await db_session.execute(stmt)
        user = result.scalar_one_or_none()
        if user and user.is_verified:
            await update.message.reply_text('Вы уже зарегистрированы и верифицированы администратором')
            return ConversationHandler.END
        if user and not user.is_verified and user.verification_waiting:
            await update.message.reply_text('Вы уже зарегистрированы, но еще не были зарегистрированы администратором')
            return ConversationHandler.END
        await update.message.reply_text(REGISTRATION_MESSAGE_SURNAME)
        return SURNAME

    @staticmethod
    async def validate_name_and_proceed(
            update: Update,
            context:
            ContextTypes.DEFAULT_TYPE,
            key: str,
            key_repr: str,
            next_state: int,
            prompt_next: str
    ):
        user_input = update.message.text
        if len(user_input) <= Registration.NAME_SYMBOLS_LIMIT:
            context.user_data[key] = None if key == 'patronymic' and 'нет' in user_input.lower() else user_input
            await update.message.reply_text(prompt_next)
            return next_state
        else:
            await update.message.reply_text(
                FIO_VALIDATION_MESSAGE.format(key_repr=key_repr, symbols_limit=Registration.NAME_SYMBOLS_LIMIT)
            )
            return next_state - 1

    @staticmethod
    async def last_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await Registration.validate_name_and_proceed(
            update, context, 'last_name', 'Поле "фамилия"', NAME, REGISTRATION_MESSAGE_NAME
        )

    @staticmethod
    async def first_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await Registration.validate_name_and_proceed(
            update, context, 'first_name', 'Поле "имя"', PATRONYMIC, REGISTRATION_MESSAGE_PATRONYMIC
        )

    @staticmethod
    async def patronymic_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        return await Registration.validate_name_and_proceed(
            update, context, 'patronymic', 'Поле "отчество"', SCHOOL_NAME, REGISTRATION_MESSAGE_SCHOOL_NAME
        )

    @staticmethod
    async def school_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_input = update.message.text
        if len(user_input) <= Registration.SCHOOL_NAME_SYMBOLS_LIMIT:
            context.user_data['school_name'] = user_input
            await update.message.reply_text(REGISTRATION_MESSAGE_CLASS_NUMBER)
            return CLASS_NUMBER
        else:
            await update.message.reply_text(
                SCHOOL_NAME_VALIDATION_MESSAGE.format(symbols_limit=Registration.SCHOOL_NAME_SYMBOLS_LIMIT)
            )
        return CLASS_NUMBER

    @staticmethod
    async def class_number_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user_input = int(update.message.text)
            if user_input in range(1, 12):
                context.user_data['class_number'] = update.message.text
                await update.message.reply_text(REGISTRATION_MESSAGE_CLASS_SYMBOL)
            else:
                await update.message.reply_text(CLASS_NUMBER_VALIDATION_MESSAGE)
                return CLASS_NUMBER
        except ValueError:
            await update.message.reply_text(CLASS_NUMBER_VALIDATION_MESSAGE)
            return CLASS_NUMBER
        return CLASS_SYMBOL

    @staticmethod
    @with_db_session
    async def class_symbol_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_input = update.message.text
        db_session: AsyncSession = context.chat_data['db_session']

        if len(user_input) == 1 and user_input.isalpha():
            context.user_data['class_symbol'] = user_input.upper()

            telegram_id = update.message.chat_id
            last_name = context.user_data['last_name'].capitalize()
            first_name = context.user_data['first_name'].capitalize()
            patronymic = context.user_data['patronymic']
            school_name = context.user_data['school_name']
            class_number = context.user_data['class_number']
            class_symbol = context.user_data['class_symbol']

            stmt = select(User).filter_by(telegram_id=telegram_id)
            result = await db_session.execute(stmt)
            user = result.scalars().one_or_none()

            if user:
                user.registration_attempts += 1
                if user.registration_attempts > 3:
                    await update.message.reply_text(EXCEEDED_REGISTRATION_LIMIT_MESSAGE)
                    return ConversationHandler.END
                user.last_name = last_name
                user.first_name = first_name
                user.patronymic = patronymic
                user.school_name = school_name
                user.class_number = class_number
                user.class_symbol = class_symbol
                user.verification_waiting = True

            else:
                user = User(
                    telegram_id=telegram_id,
                    last_name=last_name,
                    first_name=first_name,
                    patronymic=patronymic,
                    school_name=school_name,
                    class_number=class_number,
                    class_symbol=class_symbol,
                    registration_attempts=1
                )
                db_session.add(user)

            await db_session.commit()
            await update.message.reply_text(REGISTRATION_FINISHED_MESSAGE)
        else:
            await update.message.reply_text(CLASS_SYMBOL_VALIDATION_MESSAGE)
            return CLASS_SYMBOL
        await context.bot.send_message(chat_id=ADMIN_TELEGRAM_ID, text=NEW_USER_NOTIFICATION)
        return ConversationHandler.END

    @staticmethod
    async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(REGISTRATION_CANCELED_MESSAGE)
        return ConversationHandler.END


class TeamRegistration:
    TEAM_NAME_LIMIT = 100
    SCHOOL_NAME_LIMIT = 200

    @staticmethod
    @with_db_session
    async def start_team_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_id = update.message.from_user.id
        chat_id = update.message.chat.id
        chat_type = update.message.chat.type

        if chat_type not in ['group', 'supergroup']:
            await update.message.reply_text(MSG_GROUP_CHAT_ONLY)
            return ConversationHandler.END

        db_session = context.chat_data['db_session']

        stmt = select(Team).filter_by(telegram_id=chat_id)
        result = await db_session.execute(stmt)
        existing_team = result.scalars().one_or_none()

        if existing_team:
            await update.message.reply_text(
                MSG_CHAT_ALREADY_REGISTERED.format(
                    team_name=existing_team.name,
                    school_name=existing_team.school_name,
                    class_number=existing_team.class_number,
                    class_symbol=existing_team.class_symbol
                )
            )
            return ConversationHandler.END

        stmt = select(User).filter_by(telegram_id=user_id)
        result = await db_session.execute(stmt)
        user = result.scalars().one_or_none()

        if not user:
            await update.message.reply_text(MSG_USER_NOT_FOUND)
            return ConversationHandler.END

        if not user.is_verified:
            await update.message.reply_text(MSG_USER_NOT_VERIFIED)
            return ConversationHandler.END

        await update.message.reply_text(MSG_ENTER_TEAM_NAME)
        return TEAM_NAME

    @staticmethod
    async def team_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        team_name = update.message.text
        if len(team_name) > TeamRegistration.TEAM_NAME_LIMIT:
            await update.message.reply_text(
                MSG_TEAM_NAME_TOO_LONG.format(team_name_limit=TeamRegistration.TEAM_NAME_LIMIT)
            )
            return TEAM_NAME

        context.user_data['team_name'] = team_name
        await update.message.reply_text(MSG_ENTER_SCHOOL_NAME)
        return TEAM_SCHOOL_NAME

    @staticmethod
    async def school_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        school_name = update.message.text
        if len(school_name) > TeamRegistration.SCHOOL_NAME_LIMIT:
            await update.message.reply_text(
                MSG_SCHOOL_NAME_TOO_LONG.format(school_name_limit=TeamRegistration.SCHOOL_NAME_LIMIT)
            )
            return TEAM_SCHOOL_NAME

        context.user_data['school_name'] = school_name
        await update.message.reply_text(MSG_ENTER_CLASS_NUMBER)
        return TEAM_CLASS_NUMBER

    @staticmethod
    async def class_number_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        try:
            class_number = int(update.message.text)
            if class_number not in range(1, 12):
                await update.message.reply_text(MSG_INVALID_CLASS_NUMBER)
                return TEAM_CLASS_NUMBER

            context.user_data['class_number'] = class_number
            await update.message.reply_text(MSG_ENTER_CLASS_SYMBOL)
            return TEAM_CLASS_SYMBOL
        except ValueError:
            await update.message.reply_text(MSG_INVALID_CLASS_NUMBER)
            return TEAM_CLASS_NUMBER

    @staticmethod
    async def class_symbol_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        class_symbol = update.message.text
        if len(class_symbol) != 1 or not class_symbol.isalpha():
            await update.message.reply_text(MSG_INVALID_CLASS_SYMBOL)
            return TEAM_CLASS_SYMBOL

        context.user_data['class_symbol'] = class_symbol.upper()

        team_name = context.user_data['team_name']
        school_name = context.user_data['school_name']
        class_number = context.user_data['class_number']
        class_symbol = context.user_data['class_symbol']

        await update.message.reply_text(
            MSG_CONFIRM_TEAM_REGISTRATION.format(
                team_name=team_name,
                school_name=school_name,
                class_number=class_number,
                class_symbol=class_symbol
            ),
            reply_markup=ReplyKeyboardMarkup(CONFIRMATION_BUTTONS, resize_keyboard=True, one_time_keyboard=True)
        )
        return TEAM_CONFIRMATION

    @staticmethod
    @with_db_session
    async def confirm_team(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        confirmation = update.message.text.lower()
        if confirmation == 'да':
            user_id = update.message.from_user.id

            db_session = context.chat_data['db_session']

            stmt = select(User).filter_by(telegram_id=user_id)
            result = await db_session.execute(stmt)
            user = result.scalars().one_or_none()

            team_name = context.user_data['team_name']
            school_name = context.user_data['school_name']
            class_number = context.user_data['class_number']
            class_symbol = context.user_data['class_symbol']

            new_team = Team(
                telegram_id=update.message.chat.id,
                name=team_name,
                class_number=class_number,
                class_symbol=class_symbol,
                school_name=school_name,
                author_id=user.id
            )

            db_session.add(new_team)
            await db_session.commit()

            await update.message.reply_text(MSG_TEAM_REGISTERED_SUCCESS, reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END
        else:
            await update.message.reply_text(MSG_TEAM_REGISTRATION_CANCELLED, reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END

    @staticmethod
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text(MSG_PROCESS_CANCELLED, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
