from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from utils.constants import TASK_TYPES_BUTTONS, \
    ADD_INDIVIDUAL_TASK_BUTTON, ADD_GROUP_TASK_BUTTON, ADD_TASK_TEXT_MESSAGE, ADD_DEADLINE_MESSAGE, \
    ADD_GETTING_ANSWERS_TIME_MESSAGE, ADD_TASK_SUCCESS_MESSAGE, ADD_SENDING_TASK_TIME_MESSAGE, TASK_TYPE, TASK_TEXT, \
    TASK_DEADLINE, SENDING_TASK_TIME, GETTING_ANSWERS_TIME, ADD_TASK_TYPE_MESSAGE, TASK_ALREADY_EXISTS, \
    TASK_FINISHED_ADMIN_MESSAGE, INDIVIDUAL_TYPE, GROUP_TYPE, CANCEL_ACTION, ADD_TASK_CANCEL_MESSAGE, CANCEL_BUTTON, \
    INVALID_DATE_MESSAGE

from database.models import Task
from utils.decorators import tutor_or_admin_required, with_db_session
from utils.scheduler import schedule_task


@tutor_or_admin_required
@with_db_session
async def finish_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db_session: AsyncSession = context.chat_data['db_session']
    stmt = select(Task).filter_by(is_finished=False)
    result = await db_session.execute(stmt)
    not_finished_tasks = result.scalars().all()
    for task in not_finished_tasks:
        task.is_finished = True
    await db_session.commit()
    await update.message.reply_text(TASK_FINISHED_ADMIN_MESSAGE)


async def create_task(
        db_session: AsyncSession,
        text: str,
        task_type: str,
        deadline: datetime,
        sending_task_time: datetime,
        getting_answers_time: datetime | None
):
    new_task = Task(
        text=text,
        type=task_type,
        deadline=deadline,
        sending_task_time=sending_task_time,
        getting_answers_time=getting_answers_time
    )
    db_session.add(new_task)
    await db_session.commit()
    return new_task.id


def validate_datetime(date_text, date_format):
    try:
        datetime.strptime(date_text, date_format)
        return True
    except ValueError:
        return False


class AddTask:

    @staticmethod
    @tutor_or_admin_required
    @with_db_session
    async def ask_task_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
        db_session = context.chat_data['db_session']
        stmt = select(Task).filter_by(is_finished=False)
        result = await db_session.execute(stmt)
        not_finished_tasks = result.fetchall()
        if not_finished_tasks:
            await update.message.reply_text(TASK_ALREADY_EXISTS)
            return ConversationHandler.END
        reply_markup = ReplyKeyboardMarkup(TASK_TYPES_BUTTONS + CANCEL_BUTTON, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(ADD_TASK_TYPE_MESSAGE, reply_markup=reply_markup)
        return TASK_TYPE

    @staticmethod
    async def get_task_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.text == CANCEL_ACTION:
            await update.message.reply_text(ADD_TASK_CANCEL_MESSAGE, reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END

        task_type = update.message.text
        if task_type == ADD_INDIVIDUAL_TASK_BUTTON:
            context.user_data['task_type'] = INDIVIDUAL_TYPE
        elif task_type == ADD_GROUP_TASK_BUTTON:
            context.user_data['task_type'] = GROUP_TYPE
        else:
            await update.message.reply_text(
                'Некорректный тип задания. Пожалуйста, выберите тип задания или нажмите "Отменить".'
            )
            return TASK_TYPE
        await update.message.reply_text(
            ADD_TASK_TEXT_MESSAGE,
            reply_markup=ReplyKeyboardMarkup(CANCEL_BUTTON, resize_keyboard=True, one_time_keyboard=True)
        )
        return TASK_TEXT

    @staticmethod
    async def get_task_deadline(update: Update, context: ContextTypes):
        if update.message.text == CANCEL_ACTION:
            await update.message.reply_text(ADD_TASK_CANCEL_MESSAGE, reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END

        context.user_data['task_text'] = update.message.text
        await update.message.reply_text(
            ADD_DEADLINE_MESSAGE,
            reply_markup=ReplyKeyboardMarkup(CANCEL_BUTTON, resize_keyboard=True, one_time_keyboard=True)
        )
        return TASK_DEADLINE

    @staticmethod
    async def get_sending_task_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
        deadline_text = update.message.text
        if deadline_text == CANCEL_ACTION:
            await update.message.reply_text(ADD_TASK_CANCEL_MESSAGE, reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END

        if not validate_datetime(deadline_text, '%d.%m.%Y %H:%M'):
            await update.message.reply_text(INVALID_DATE_MESSAGE)
            return TASK_DEADLINE

        task_deadline = datetime.strptime(deadline_text, '%d.%m.%Y %H:%M')
        if task_deadline < datetime.now():
            await update.message.reply_text(
                'Дедлайн не может быть меньше текущего времени. '
                'Пожалуйста, введите корректное время или нажмите "Отменить".'
            )
            return TASK_DEADLINE

        context.user_data['task_deadline'] = task_deadline
        await update.message.reply_text(
            ADD_SENDING_TASK_TIME_MESSAGE,
            reply_markup=ReplyKeyboardMarkup(CANCEL_BUTTON, resize_keyboard=True, one_time_keyboard=True)
        )
        return SENDING_TASK_TIME

    @staticmethod
    @with_db_session
    async def get_getting_answers_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.text == CANCEL_ACTION:
            await update.message.reply_text(ADD_TASK_CANCEL_MESSAGE, reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END

        sending_task_time_text = update.message.text
        if not validate_datetime(sending_task_time_text, '%d.%m.%Y %H:%M'):
            await update.message.reply_text(
                'Некорректный формат времени отправки задания. '
                'Пожалуйста, введите корректное время или нажмите "Отменить".'
            )
            return SENDING_TASK_TIME
        sending_task_time = datetime.strptime(sending_task_time_text, '%d.%m.%Y %H:%M')

        if sending_task_time > context.user_data['task_deadline']:
            await update.message.reply_text(
                'Время отправки задания не может быть позже дедлайна. '
                'Пожалуйста, введите корректное время или нажмите "Отменить".'
            )
            return SENDING_TASK_TIME

        if sending_task_time < datetime.now():
            await update.message.reply_text(
                'Время отправки задания не может быть меньше текущего времени. '
                'Пожалуйста, введите корректное время или нажмите "Отменить".'
            )
            return SENDING_TASK_TIME

        context.user_data['sending_task_time'] = sending_task_time

        if context.user_data['task_type'] == GROUP_TYPE:
            await update.message.reply_text(
                ADD_GETTING_ANSWERS_TIME_MESSAGE,
                reply_markup=ReplyKeyboardMarkup(CANCEL_BUTTON, resize_keyboard=True, one_time_keyboard=True)
            )
            return GETTING_ANSWERS_TIME
        elif context.user_data['task_type'] == INDIVIDUAL_TYPE:
            task_id = await create_task(
                context.chat_data['db_session'],
                context.user_data['task_text'],
                context.user_data['task_type'],
                context.user_data['task_deadline'],
                context.user_data['sending_task_time'],
                None
            )
            await schedule_task(task_id, INDIVIDUAL_TYPE, context.user_data['sending_task_time'], context)
            await update.message.reply_text(ADD_TASK_SUCCESS_MESSAGE.format(
                date_time=context.user_data['sending_task_time'].strftime('%d.%m.%Y %H:%M')
            ), reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END

    @staticmethod
    @with_db_session
    async def handle_getting_answers_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message.text == CANCEL_ACTION:
            await update.message.reply_text(ADD_TASK_CANCEL_MESSAGE, reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END

        getting_answers_time_text = update.message.text
        if not validate_datetime(getting_answers_time_text, '%d.%m.%Y %H:%M'):
            await update.message.reply_text(
                'Некорректный формат времени начала принятия ответов. '
                'Пожалуйста, введите корректное время или нажмите "Отменить".'
            )
            return GETTING_ANSWERS_TIME
        getting_answers_time = datetime.strptime(getting_answers_time_text, '%d.%m.%Y %H:%M')

        if getting_answers_time > context.user_data['task_deadline']:
            await update.message.reply_text(
                'Время начала принятия ответов не может быть позже дедлайна. '
                'Пожалуйста, введите корректное время или нажмите "Отменить".'
            )
            return GETTING_ANSWERS_TIME

        if getting_answers_time > context.user_data['sending_task_time']:
            await update.message.reply_text(
                'Время начала принятия ответов не может быть позже времени отправки задания. '
                'Пожалуйста, введите корректное время или нажмите "Отменить".'
            )
            return GETTING_ANSWERS_TIME

        context.user_data['getting_answers_time'] = getting_answers_time

        task_id = await create_task(
            context.chat_data['db_session'],
            context.user_data['task_text'],
            context.user_data['task_type'],
            context.user_data['task_deadline'],
            context.user_data['sending_task_time'],
            context.user_data['getting_answers_time'],
        )
        await schedule_task(task_id, GROUP_TYPE, context.user_data['sending_task_time'], context)
        await update.message.reply_text(ADD_TASK_SUCCESS_MESSAGE.format(
            date_time=context.user_data['sending_task_time'].strftime('%d.%m.%Y %H:%M')
        ), reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
