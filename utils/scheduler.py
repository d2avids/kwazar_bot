import logging
from datetime import datetime

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from sqlalchemy.future import select
from telegram.ext import ContextTypes

from database.models import Task, Team, User
from utils.constants import GROUP_TYPE, INDIVIDUAL_TYPE
from utils.utils import adjust_datetime_for_scheduler

scheduler = AsyncIOScheduler()
logger = logging.getLogger(__name__)



async def send_individual_task(task_id: int, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f'Sending individual task with ID: {task_id}')
    db_session = context.chat_data['db_session']
    stmt = select(Task).filter_by(id=task_id)
    result = await db_session.execute(stmt)
    task = result.scalar()

    if not task:
        logger.error(f"Task with ID {task_id} not found")
        return

    stmt = select(User.telegram_id).filter_by(is_verified=True)
    result = await db_session.execute(stmt)
    user_telegram_ids = result.scalars().all()
    message_to_send = (
        f'Появилось новое индивидуальное задание:\n\n<i>{task.text}</i>\n\n'
        f'<u>Дедлайн</u>: <b>{task.deadline}</b>\n'
    )
    for telegram_id in user_telegram_ids:
        await context.bot.send_message(chat_id=telegram_id, text=message_to_send, parse_mode='HTML')
        logger.info(f'Sent task with ID {task_id} to user with telegram ID: {telegram_id}')


async def send_group_task(task_id: int, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f'Sending group task with ID: {task_id}')
    db_session = context.chat_data['db_session']
    stmt = select(Task).filter_by(id=task_id)
    result = await db_session.execute(stmt)
    task = result.scalar()

    if not task:
        logger.error(f'Task with ID {task_id} not found')
        return

    stmt = select(Team.telegram_id)
    result = await db_session.execute(stmt)
    team_telegram_ids = result.scalars().all()
    message_to_send = (
        f'Появилось новое групповое задание:\n\n<i>{task.text}</i>\n\n'
        f'<u>Дедлайн</u>: <b>{task.deadline}</b>\n'
        f'<u>Время начала приема ответов</u>: <b>{task.getting_answers_time}</b>'
    )
    for telegram_id in team_telegram_ids:
        await context.bot.send_message(chat_id=telegram_id, text=message_to_send, parse_mode='HTML')
        logger.info(f'Sent task with ID {task_id} to team with telegram ID: {telegram_id}')


def job_listener(event):
    if event.exception:
        logger.error(f'Job {event.job_id} failed: {event.exception}')
    else:
        logger.info(f'Job {event.job_id} executed successfully')


async def schedule_task(task_id: int, task_type: str, sending_task_time: datetime, context: ContextTypes.DEFAULT_TYPE):
    run_date = adjust_datetime_for_scheduler(sending_task_time)
    if task_type == INDIVIDUAL_TYPE:
        scheduler.add_job(
            send_individual_task,
            DateTrigger(run_date=run_date),
            args=[task_id, context]
        )
    elif task_type == GROUP_TYPE:
        scheduler.add_job(
            send_group_task,
            DateTrigger(run_date=run_date),
            args=[task_id, context]
        )
    if not scheduler.running:
        scheduler.start()

scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
