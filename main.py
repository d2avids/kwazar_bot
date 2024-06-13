import asyncio
import logging
import os
from logging.handlers import TimedRotatingFileHandler

import nest_asyncio
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())
nest_asyncio.apply()

from sqlalchemy import select
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (ApplicationBuilder, CommandHandler, ContextTypes,
                          ConversationHandler, MessageHandler, filters)

from database.engine import create_db
from database.models import User
from handlers.add_task import AddTask, finish_test
from handlers.add_task_answer import AddGroupTaskAnswer, AddTaskUserAnswer
from handlers.add_tutor import AddTutor
from handlers.feedback import AddFeedback, GetFeedback, next_action
from handlers.registration import Registration, TeamRegistration
from handlers.reports import IndividualReport, TeamReport
from handlers.search_user import SearchUser
from handlers.verification import Verification
from utils.constants import (ABOUT_PROJECT_MESSAGE, ADD_NEW_TASK, ADD_TUTOR,
                             ADMIN_INSTRUCTIONS_MESSAGE_1,
                             ADMIN_INSTRUCTIONS_MESSAGE_2, ADMIN_TELEGRAM_ID,
                             BOT_INSTRUCTION, CHECK_ANSWERS, CHOOSE_FEEDBACK,
                             CLASS_NUMBER, CLASS_SYMBOL, CURATOR_BUTTONS,
                             CURATOR_INSTRUCTIONS_MESSAGE, END_DATE,
                             FEEDBACK_TYPE, GET_INDIVIDUAL_REPORT,
                             GET_TEAM_REPORT, GETTING_ANSWERS_TIME,
                             GIVE_FEEDBACK, GIVE_INDIVIDUAL_ANSWER,
                             GIVE_TEAM_ANSWER, INDIVIDUAL_MARKS, NAME,
                             NEXT_ACTION, PATRONYMIC, REGISTRATION_MESSAGE,
                             SCHOOL_NAME, SEARCH_USER, SENDING_TASK_TIME,
                             START_DATE, START_MESSAGE, SURNAME,
                             TASK_ANSWER_TEXT, TASK_DEADLINE, TASK_TEXT,
                             TASK_TYPE, TEAM_BUTTONS, TEAM_CLASS_NUMBER,
                             TEAM_CLASS_SYMBOL, TEAM_CONFIRMATION, TEAM_MARKS,
                             TEAM_NAME, TEAM_REGISTRATION_MESSAGE,
                             TEAM_SCHOOL_NAME, USER_BUTTONS,
                             USER_INSTRUCTIONS_MESSAGE, VERIFICATION_PROCESS,
                             VERIFICATION_START)
from utils.decorators import with_db_session

BOT_TOKEN = os.environ.get('BOT_TOKEN')


class ExcludeLoggerFilter(logging.Filter):
    def __init__(self, name):
        self.name = name

    def filter(self, record):
        return not record.name.startswith(self.name)


LOG_DIR = 'logs'
logging.basicConfig(level=logging.DEBUG)
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, 'bot.log')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = TimedRotatingFileHandler(log_file, when='midnight', interval=1, backupCount=3)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
exclude_httpcore_filter = ExcludeLoggerFilter('httpcore.http11')
handler.addFilter(exclude_httpcore_filter)
handler.setFormatter(formatter)
logger.addHandler(handler)


@with_db_session
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_type = update.message.chat.type
    if chat_type not in ['group', 'supergroup']:
        user_telegram_id = update.message.chat_id
        db_session = context.chat_data['db_session']
        stmt = select(User).filter_by(telegram_id=user_telegram_id)
        result = await db_session.execute(stmt)
        user = result.scalars().one_or_none()
        if user and user.is_curator or str(user_telegram_id) == ADMIN_TELEGRAM_ID:
            buttons = CURATOR_BUTTONS
        else:
            buttons = USER_BUTTONS
    else:
        buttons = TEAM_BUTTONS
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(START_MESSAGE, reply_markup=reply_markup)


async def send_about_project_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(ABOUT_PROJECT_MESSAGE)


@with_db_session
async def send_instruction_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_telegram_id = update.message.chat_id
    if str(user_telegram_id) == ADMIN_TELEGRAM_ID:
        await update.message.reply_text(ADMIN_INSTRUCTIONS_MESSAGE_1, parse_mode='HTML')
        await asyncio.sleep(0.05)
        await update.message.reply_text(ADMIN_INSTRUCTIONS_MESSAGE_2, parse_mode='HTML')
        return
    db_session = context.chat_data['db_session']
    stmt = select(User).filter_by(telegram_id=user_telegram_id)
    result = await db_session.execute(stmt)
    user = result.scalars().one_or_none()
    if not user or not user.is_curator:
        await update.message.reply_text(USER_INSTRUCTIONS_MESSAGE, parse_mode='HTML')
    elif user and user.is_curator:
        await update.message.reply_text(CURATOR_INSTRUCTIONS_MESSAGE, parse_mode='HTML')


async def cancel(update: Update, context: ContextTypes):
    return ConversationHandler.END


async def main():
    await create_db()
    app = ApplicationBuilder().token("7051184649:AAHkfbd_ghMDI-SgDJfvxhbrQ7iwZYPn49A").build()

    registration_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text([REGISTRATION_MESSAGE]), Registration.start_registration)],
        states={
            SURNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, Registration.last_name_received)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, Registration.first_name_received)],
            PATRONYMIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, Registration.patronymic_received)],
            SCHOOL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, Registration.school_name_received)],
            CLASS_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, Registration.class_number_received)],
            CLASS_SYMBOL: [MessageHandler(filters.TEXT & ~filters.COMMAND, Registration.class_symbol_received)]
        },
        fallbacks=[MessageHandler(filters.COMMAND, cancel)],
    )
    team_registration_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text([TEAM_REGISTRATION_MESSAGE]), TeamRegistration.start_team_registration)],
        states={
            TEAM_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, TeamRegistration.team_name_received)],
            TEAM_SCHOOL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, TeamRegistration.school_name_received)],
            TEAM_CLASS_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, TeamRegistration.class_number_received)],
            TEAM_CLASS_SYMBOL: [MessageHandler(filters.TEXT & ~filters.COMMAND, TeamRegistration.class_symbol_received)],
            TEAM_CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, TeamRegistration.confirm_team)]
        },
        fallbacks=[MessageHandler(filters.COMMAND, cancel)],
    )
    verification_handler = ConversationHandler(
        entry_points=[CommandHandler('verify', Verification.start_verification)],
        states={
            VERIFICATION_START: [MessageHandler(filters.TEXT & ~filters.COMMAND, Verification.start_verification)],
            VERIFICATION_PROCESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, Verification.process_verification)],
        },
        fallbacks=[MessageHandler(filters.COMMAND, cancel)],
    )
    search_user_handler = ConversationHandler(
        entry_points=[CommandHandler('search_user', SearchUser.ask_last_name)],
        states={
            SEARCH_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, SearchUser.search_users_by_last_name)]
        },
        fallbacks=[MessageHandler(filters.COMMAND, cancel)],
    )
    add_tutor_handler = ConversationHandler(
        entry_points=[CommandHandler('add_tutor', AddTutor.ask_user_id)],
        states={
            ADD_TUTOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, AddTutor.add_tutor)]
        },
        fallbacks=[MessageHandler(filters.COMMAND, cancel)],
    )
    add_task_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text([ADD_NEW_TASK]), AddTask.ask_task_type)],
        states={
            TASK_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, AddTask.get_task_text)],
            TASK_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, AddTask.get_task_deadline)],
            TASK_DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, AddTask.get_sending_task_time)],
            SENDING_TASK_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, AddTask.get_getting_answers_time)],
            GETTING_ANSWERS_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, AddTask.handle_getting_answers_time)]
        },
        fallbacks=[MessageHandler(filters.COMMAND, cancel)],
    )
    add_user_task_answer_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f'^{GIVE_INDIVIDUAL_ANSWER}$'),
                                     AddTaskUserAnswer.prompt_task_answer)],
        states={
            TASK_ANSWER_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, AddTaskUserAnswer.receive_task_answer)]
        },
        fallbacks=[MessageHandler(filters.COMMAND, cancel)],
    )
    add_feedback_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f'^{CHECK_ANSWERS}'), AddFeedback.start_feedback)],
        states={
            FEEDBACK_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, AddFeedback.choose_answer_id_to_estimate)],
            CHOOSE_FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, AddFeedback.choose_allowed_feedback)],
            GIVE_FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, AddFeedback.give_feedback)],
            NEXT_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, next_action)]
        },
        fallbacks=[MessageHandler(filters.COMMAND, cancel)],
    )
    get_individual_report_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f'^{GET_INDIVIDUAL_REPORT}$'), IndividualReport.start_report)],
        states={
            START_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, IndividualReport.get_start_date)],
            END_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, IndividualReport.get_end_date)]
        },
        fallbacks=[MessageHandler(filters.COMMAND, cancel)],
    )
    get_team_report_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(f'^{GET_TEAM_REPORT}$'), TeamReport.start_report)],
        states={
            START_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, TeamReport.get_start_date)],
            END_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, TeamReport.get_end_date)]
        },
        fallbacks=[MessageHandler(filters.COMMAND, cancel)],
    )
    add_team_task_answer_handler = ConversationHandler(
        entry_points=[MessageHandler(
            filters.Regex(f'^{GIVE_TEAM_ANSWER}$'), AddGroupTaskAnswer.prompt_task_answer)
        ],
        states={
            TASK_ANSWER_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, AddGroupTaskAnswer.receive_task_answer)]
        },
        fallbacks=[MessageHandler(filters.COMMAND, cancel)],
    )

    app.add_handler(get_individual_report_handler, 1)
    app.add_handler(get_team_report_handler, 2)
    app.add_handler(add_feedback_handler, 3)
    app.add_handler(add_user_task_answer_handler, 4)
    app.add_handler(add_team_task_answer_handler, 5)
    app.add_handler(add_task_handler, 6)
    app.add_handler(search_user_handler, 7)
    app.add_handler(add_tutor_handler, 8)
    app.add_handler(team_registration_handler, 9)
    app.add_handler(registration_handler, 10)
    app.add_handler(verification_handler, 11)
    app.add_handler(MessageHandler(filters.Regex(f'^{INDIVIDUAL_MARKS}$'), GetFeedback.get_individual_feedback), 12)
    app.add_handler(MessageHandler(filters.Regex(f'^{TEAM_MARKS}$'), GetFeedback.get_team_feedback), 13)
    app.add_handler(CommandHandler('start', start), 14)
    app.add_handler(CommandHandler('finish_test', finish_test), 15)
    app.add_handler(MessageHandler(filters.Text([ABOUT_PROJECT_MESSAGE]), send_about_project_message), 16)
    app.add_handler(MessageHandler(filters.Text([BOT_INSTRUCTION]), send_instruction_message), 17)
    app.add_handler(CommandHandler('cancel', cancel), 18)
    app.run_polling()


if __name__ == '__main__':
    asyncio.run(main())
