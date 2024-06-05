import logging
import asyncio
import os
from logging.handlers import TimedRotatingFileHandler

import nest_asyncio
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())
nest_asyncio.apply()

from sqlalchemy import select

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
from utils.constants import START_MESSAGE, ABOUT_PROJECT_MESSAGE, INSTRUCTIONS_MESSAGE, SURNAME, NAME, PATRONYMIC, \
    SCHOOL_NAME, CLASS_NUMBER, CLASS_SYMBOL, \
    VERIFICATION_START, VERIFICATION_PROCESS, SEARCH_USER, ADD_TUTOR, USER_BUTTONS, CURATOR_BUTTONS, TASK_TYPE, \
    TASK_DEADLINE, TASK_TEXT, SENDING_TASK_TIME, GETTING_ANSWERS_TIME, TASK_ANSWER_TEXT, FEEDBACK_TYPE, CHOOSE_FEEDBACK, \
    GIVE_FEEDBACK, NEXT_ACTION, START_DATE, END_DATE, TEAM_NAME, TEAM_SCHOOL_NAME, TEAM_CLASS_NUMBER, TEAM_CLASS_SYMBOL, \
    TEAM_CONFIRMATION

from utils.decorators import with_db_session
from database.engine import create_db
from handlers.feedback import AddFeedback, next_action, GetFeedback
from handlers.registration import Registration, TeamRegistration
from handlers.verification import Verification
from handlers.reports import IndividualReport, TeamReport
from handlers.add_task_answer import AddTaskUserAnswer, AddGroupTaskAnswer
from handlers.add_task import AddTask, finish_test
from handlers.add_tutor import AddTutor
from handlers.search_user import SearchUser
from database.models import User


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
    user_telegram_id = update.message.chat_id
    db_session = context.chat_data['db_session']
    stmt = select(User).filter_by(telegram_id=user_telegram_id)
    result = await db_session.execute(stmt)
    user = result.scalars().one_or_none()
    if not user or not user.is_curator:
        buttons = USER_BUTTONS
    elif user and user.is_curator:
        buttons = CURATOR_BUTTONS
    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(START_MESSAGE, reply_markup=reply_markup)


async def send_about_project_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(ABOUT_PROJECT_MESSAGE)


async def send_instruction_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(INSTRUCTIONS_MESSAGE, parse_mode='HTML')


async def cancel(update: Update, context: ContextTypes):
    return ConversationHandler.END


async def main():
    await create_db()
    app = ApplicationBuilder().token("7051184649:AAHkfbd_ghMDI-SgDJfvxhbrQ7iwZYPn49A").build()
    registration_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text(['Регистрация']), Registration.start_registration)],
        states={
            SURNAME: [MessageHandler(filters.TEXT, Registration.last_name_received)],
            NAME: [MessageHandler(filters.TEXT, Registration.first_name_received)],
            PATRONYMIC: [MessageHandler(filters.TEXT, Registration.patronymic_received)],
            SCHOOL_NAME: [MessageHandler(filters.TEXT, Registration.school_name_received)],
            CLASS_NUMBER: [MessageHandler(filters.TEXT, Registration.class_number_received)],
            CLASS_SYMBOL: [MessageHandler(filters.TEXT, Registration.class_symbol_received)]
        },
        fallbacks=[MessageHandler(filters.COMMAND, cancel)],
    )
    team_registration_handler = ConversationHandler(
        entry_points=[CommandHandler('register_team', TeamRegistration.start_team_registration)],
        states={
            TEAM_NAME: [MessageHandler(filters.TEXT, TeamRegistration.team_name_received)],
            TEAM_SCHOOL_NAME: [MessageHandler(filters.TEXT, TeamRegistration.school_name_received)],
            TEAM_CLASS_NUMBER: [MessageHandler(filters.TEXT, TeamRegistration.class_number_received)],
            TEAM_CLASS_SYMBOL: [MessageHandler(filters.TEXT, TeamRegistration.class_symbol_received)],
            TEAM_CONFIRMATION: [MessageHandler(filters.TEXT, TeamRegistration.confirm_team)]
        },
        fallbacks=[MessageHandler(filters.COMMAND, cancel)],
    )
    verification_handler = ConversationHandler(
        entry_points=[CommandHandler('verify', Verification.start_verification)],
        states={
            VERIFICATION_START: [MessageHandler(filters.TEXT, Verification.start_verification)],
            VERIFICATION_PROCESS: [MessageHandler(filters.TEXT, Verification.process_verification)],
        },
        fallbacks=[MessageHandler(filters.COMMAND, cancel)],
    )
    search_user_handler = ConversationHandler(
        entry_points=[CommandHandler('search_user', SearchUser.ask_last_name)],
        states={
            SEARCH_USER: [MessageHandler(filters.TEXT, SearchUser.search_users_by_last_name)]
        },
        fallbacks=[MessageHandler(filters.COMMAND, cancel)],
    )
    add_tutor_handler = ConversationHandler(
        entry_points=[CommandHandler('add_tutor', AddTutor.ask_user_id)],
        states={
            ADD_TUTOR: [MessageHandler(filters.TEXT, AddTutor.add_tutor)]
        },
        fallbacks=[MessageHandler(filters.COMMAND, cancel)],
    )
    add_task_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text(['Новое задание']), AddTask.ask_task_type)],
        states={
            TASK_TYPE: [MessageHandler(filters.TEXT, AddTask.get_task_text)],
            TASK_TEXT: [MessageHandler(filters.TEXT, AddTask.get_task_deadline)],
            TASK_DEADLINE: [MessageHandler(filters.TEXT, AddTask.get_sending_task_time)],
            SENDING_TASK_TIME: [MessageHandler(filters.TEXT, AddTask.get_getting_answers_time)],
            GETTING_ANSWERS_TIME: [
                MessageHandler(filters.TEXT, AddTask.handle_getting_answers_time)]
        },
        fallbacks=[MessageHandler(filters.COMMAND, cancel)],
    )
    add_user_task_answer_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Дать ответ на индивидуальное задание$'),
                                     AddTaskUserAnswer.prompt_task_answer)],
        states={
            TASK_ANSWER_TEXT: [MessageHandler(filters.TEXT, AddTaskUserAnswer.receive_task_answer)]
        },
        fallbacks=[MessageHandler(filters.COMMAND, cancel)],
    )
    add_feedback_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^Проверка домашнего задания'), AddFeedback.start_feedback)],
        states={
            FEEDBACK_TYPE: [MessageHandler(filters.TEXT, AddFeedback.choose_answer_id_to_estimate)],
            CHOOSE_FEEDBACK: [MessageHandler(filters.TEXT, AddFeedback.choose_allowed_feedback)],
            GIVE_FEEDBACK: [MessageHandler(filters.TEXT, AddFeedback.give_feedback)],
            NEXT_ACTION: [MessageHandler(filters.TEXT, next_action)]
        },
        fallbacks=[MessageHandler(filters.COMMAND, cancel)],
    )
    get_individual_report_handler = ConversationHandler(
        entry_points=[CommandHandler('report_individual', IndividualReport.start_report)],
        states={
            START_DATE: [MessageHandler(filters.TEXT, IndividualReport.get_start_date)],
            END_DATE: [MessageHandler(filters.TEXT, IndividualReport.get_end_date)]
        },
        fallbacks=[MessageHandler(filters.COMMAND, cancel)],
    )
    get_team_report_handler = ConversationHandler(
        entry_points=[CommandHandler('report_group', TeamReport.start_report)],
        states={
            START_DATE: [MessageHandler(filters.TEXT, TeamReport.get_start_date)],
            END_DATE: [MessageHandler(filters.TEXT, TeamReport.get_end_date)]
        },
        fallbacks=[MessageHandler(filters.COMMAND, cancel)],
    )
    add_team_task_answer_handler = ConversationHandler(
        entry_points=[CommandHandler('give_answer', AddGroupTaskAnswer.prompt_task_answer)],
        states={
            TASK_ANSWER_TEXT: [MessageHandler(filters.TEXT, AddGroupTaskAnswer.receive_task_answer)]
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
    app.add_handler(CommandHandler('individual_feedback', GetFeedback.get_individual_feedback), 12)
    app.add_handler(CommandHandler('group_feedback', GetFeedback.get_team_feedback), 13)
    app.add_handler(CommandHandler('start', start), 14)
    app.add_handler(CommandHandler('finish_test', finish_test), 15)
    app.add_handler(MessageHandler(filters.Text(['О проекте']), send_about_project_message), 16)
    app.add_handler(MessageHandler(filters.Text(['Инструкция бота']), send_instruction_message), 17)

    app.run_polling()


if __name__ == '__main__':
    asyncio.run(main())
