from sqlalchemy import select
from sqlalchemy.orm import joinedload
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils.constants import TASK_ANSWER_TEXT, FEEDBACK_TYPE, CHOOSE_TASK_TYPE_MESSAGE, \
    CHOOSE_SCHOOL_NUMBER_MESSAGE, CHOOSE_CLASS_NUMBER_MESSAGE, CLASS_NUMBER, INDIVIDUAL_TYPE, GIVE_FEEDBACK, \
    NO_ANSWERS_TO_ESTIMATE, NEXT_ACTION, ALLOWED_FEEDBACK, NOT_ALLOWED_FEEDBACK_MESSAGE, \
    ESTIMATED_ALL_ANSWERS_MESSAGE, STOPPED_ESTIMATING, INCORRECT_ACTION_CHOSEN, CHOOSE_ACTION_MESSAGE, \
    USER_FEEDBACK_NOTIFICATION_MESSAGE, CHOOSE_FEEDBACK, INDIVIDUAL_ANSWER, GROUP_ANSWER, ANSWER_TYPES_BUTTONS, \
    GROUP_TYPE

from database.models import Task, User, UserAnswer, GroupTaskAnswer, Team
from utils.decorators import with_db_session, tutor_or_admin_required

NEXT_ANSWER = 'Следующий ответ'
STOP = 'Завершить'


@with_db_session
async def next_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = update.message.text
    feedback_type = INDIVIDUAL_TYPE if context.user_data['feedback_type'] == INDIVIDUAL_ANSWER else GROUP_TYPE
    if action == NEXT_ANSWER:
        db_session = context.chat_data['db_session']
        if feedback_type == INDIVIDUAL_TYPE:
            stmt = select(UserAnswer).options(joinedload(UserAnswer.user), joinedload(UserAnswer.task)).filter(
                Task.type == feedback_type,
                UserAnswer.curator_feedback.is_(None)
            )
        else:
            stmt = select(GroupTaskAnswer).options(joinedload(GroupTaskAnswer.team),
                                                   joinedload(GroupTaskAnswer.task)).filter(
                Task.type == feedback_type,
                GroupTaskAnswer.curator_feedback.is_(None)
            )
        result = await db_session.execute(stmt)
        answers = result.scalars().all()
        if not answers:
            await update.message.reply_text(
                NO_ANSWERS_TO_ESTIMATE.format(
                    type='индивидуальных' if feedback_type == INDIVIDUAL_TYPE else 'групповых'
                )
            )
            return ConversationHandler.END
        await display_all_answers(update, context, answers, feedback_type)
        return CHOOSE_FEEDBACK
    elif action == STOP:
        await update.message.reply_text(STOPPED_ESTIMATING)
        return ConversationHandler.END
    else:
        await update.message.reply_text(INCORRECT_ACTION_CHOSEN.format(next_answer=NEXT_ANSWER, stop=STOP))
        return NEXT_ACTION


async def display_all_answers(update: Update, context: ContextTypes.DEFAULT_TYPE, answers, feedback_type):
    message = 'Список неоцененных заданий:\n\n'
    counter = 0
    for answer in answers:
        if feedback_type == INDIVIDUAL_TYPE:
            user = answer.user
            full_name = f'{user.last_name} {user.first_name} {user.patronymic if user.patronymic else ""}'.strip()
            message += (
                f'ID {answer.id}, {full_name}, школа: {user.school_name}, '
                f'класс: {user.class_number}{user.class_symbol}, '
            )
        else:
            team = answer.team
            message += (
                f'ID {answer.id}, команда: {team.name}, школа: {team.school_name}, '
                f'класс: {team.class_number}{team.class_symbol}, '
            )

        task = answer.task
        answer_date = answer.created.strftime('%d.%m.%Y %H:%M')
        message += (
            f'дата ответа: {answer_date}\n'
            f'Текст задания: {task.text}\n'
            f'Ответ: {answer.answer_text}\n\n'
        )

        counter += 1
        if counter == 6:
            await update.message.reply_text(message, parse_mode='HTML')
            message = ''
            counter = 0

    if message:
        await update.message.reply_text(message, parse_mode='HTML')

    await update.message.reply_text('Введите ID ответа, который хотите оценить.', parse_mode='HTML')


class AddFeedback:
    @staticmethod
    @tutor_or_admin_required
    async def start_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        reply_markup = ReplyKeyboardMarkup(ANSWER_TYPES_BUTTONS, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(CHOOSE_TASK_TYPE_MESSAGE, reply_markup=reply_markup)
        return FEEDBACK_TYPE

    @staticmethod
    @with_db_session
    async def choose_answer_id_to_estimate(update: Update, context: ContextTypes.DEFAULT_TYPE):
        feedback_type = update.message.text
        if feedback_type in (INDIVIDUAL_ANSWER, GROUP_ANSWER):
            context.user_data[
                'feedback_type'] = INDIVIDUAL_ANSWER if feedback_type == INDIVIDUAL_ANSWER else GROUP_ANSWER
            db_session = context.chat_data['db_session']
            if feedback_type == INDIVIDUAL_ANSWER:
                stmt = select(UserAnswer).options(joinedload(UserAnswer.user), joinedload(UserAnswer.task)).filter(
                    Task.type == INDIVIDUAL_TYPE,
                    UserAnswer.curator_feedback.is_(None),
                    UserAnswer.task_id == Task.id
                )
            else:
                stmt = select(GroupTaskAnswer).options(joinedload(GroupTaskAnswer.team),
                                                       joinedload(GroupTaskAnswer.task)).filter(
                    Task.type == GROUP_TYPE,
                    GroupTaskAnswer.curator_feedback.is_(None),
                    GroupTaskAnswer.task_id == Task.id
                )
            result = await db_session.execute(stmt)
            answers = result.scalars().all()
            if not answers:
                await update.message.reply_text(NO_ANSWERS_TO_ESTIMATE.format(
                    type='индивидуальных' if feedback_type == INDIVIDUAL_ANSWER else 'групповых'
                ))
                return ConversationHandler.END
            await display_all_answers(
                update,
                context,
                answers,
                INDIVIDUAL_TYPE if feedback_type == INDIVIDUAL_ANSWER else GROUP_TYPE
            )
            return CHOOSE_FEEDBACK
        else:
            await update.message.reply_text(f'Пожалуйста, выберите "{INDIVIDUAL_ANSWER}" или "{GROUP_ANSWER}".')
            return FEEDBACK_TYPE

    @staticmethod
    @with_db_session
    async def choose_allowed_feedback(update: Update, context: ContextTypes):
        answer_id = update.message.text
        context.user_data['answer_id'] = answer_id
        db_session = context.chat_data['db_session']
        feedback_type = INDIVIDUAL_TYPE if context.user_data['feedback_type'] == INDIVIDUAL_ANSWER else GROUP_TYPE
        if feedback_type == INDIVIDUAL_TYPE:
            stmt = select(UserAnswer).filter(
                UserAnswer.id == answer_id,
                UserAnswer.curator_feedback.is_(None)
            )
        else:
            stmt = select(GroupTaskAnswer).filter(
                GroupTaskAnswer.id == answer_id,
                GroupTaskAnswer.curator_feedback.is_(None)
            )
        result = await db_session.execute(stmt)
        answer = result.scalar()

        if not answer:
            await update.message.reply_text('Некорректный ID ответа')
            return ConversationHandler.END

        reply_markup = ReplyKeyboardMarkup([[*ALLOWED_FEEDBACK]], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(f'Введите оценку ({", ".join(ALLOWED_FEEDBACK)}):', reply_markup=reply_markup)
        return GIVE_FEEDBACK

    @staticmethod
    @with_db_session
    async def give_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        feedback = update.message.text
        if feedback not in ALLOWED_FEEDBACK:
            await update.message.reply_text(NOT_ALLOWED_FEEDBACK_MESSAGE.format(allowed_feedback=ALLOWED_FEEDBACK))
            return GIVE_FEEDBACK

        feedback = int(feedback)
        db_session = context.chat_data['db_session']
        answer_id = context.user_data['answer_id']
        feedback_type = INDIVIDUAL_TYPE if context.user_data['feedback_type'] == INDIVIDUAL_ANSWER else GROUP_TYPE
        if feedback_type == INDIVIDUAL_TYPE:
            stmt = select(UserAnswer).options(joinedload(UserAnswer.user)).filter(
                UserAnswer.id == answer_id,
                UserAnswer.curator_feedback.is_(None)
            )
        else:
            stmt = select(GroupTaskAnswer).options(joinedload(GroupTaskAnswer.team)).filter(
                GroupTaskAnswer.id == answer_id,
                GroupTaskAnswer.curator_feedback.is_(None)
            )
        result = await db_session.execute(stmt)
        answer = result.scalar()

        if not answer:
            await update.message.reply_text('Некорректный ID ответа')
            return ConversationHandler.END

        answer.curator_feedback = feedback
        await db_session.commit()

        if feedback_type == INDIVIDUAL_TYPE:
            user = answer.user
            await context.bot.send_message(
                chat_id=user.telegram_id, text=USER_FEEDBACK_NOTIFICATION_MESSAGE.format(
                    task_type='индивидуальное'
                )
            )
        else:
            team = answer.team
            await context.bot.send_message(
                chat_id=team.telegram_id, text=USER_FEEDBACK_NOTIFICATION_MESSAGE.format(
                    task_type='групповое'
                )
            )

        reply_markup = ReplyKeyboardMarkup([[NEXT_ANSWER, STOP]], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(CHOOSE_ACTION_MESSAGE, reply_markup=reply_markup)
        return NEXT_ACTION


class GetFeedback:
    @staticmethod
    @with_db_session
    async def get_individual_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.message.from_user.id
        db_session = context.chat_data['db_session']

        stmt = select(User).filter_by(telegram_id=telegram_id)
        result = await db_session.execute(stmt)
        user = result.scalar()

        if not user:
            await update.message.reply_text('Сначала необходимо зарегистрироваться')
            return
        elif user and not user.is_verified:
            await update.message.reply_text('Для этого действия необходимо быть верифицированным пользователем')
            return

        stmt = select(UserAnswer).join(Task).filter(
            UserAnswer.user_id == user.id,
            Task.type == INDIVIDUAL_TYPE
        ).order_by(UserAnswer.created.desc())
        result = await db_session.execute(stmt)
        last_answer = result.scalars().first()

        if not last_answer:
            await update.message.reply_text('Нет ответов на индивидуальные задания.')
            return

        if last_answer.curator_feedback is not None:
            await update.message.reply_text(
                f'Ваша оценка за последнее индивидуальное задание: {last_answer.curator_feedback}'
            )
        else:
            await update.message.reply_text(
                'Работа еще не проверена. Когда работа будет оценена, вам придет оповещение.'
            )

    @staticmethod
    @with_db_session
    async def get_team_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat.id
        chat_type = update.message.chat.type
        db_session = context.chat_data['db_session']

        if chat_type not in ['group', 'supergroup']:
            await update.message.reply_text('Эту команду можно использовать только в групповом чате.')
            return

        stmt = select(Team).filter_by(telegram_id=chat_id)
        result = await db_session.execute(stmt)
        team = result.scalars().first()

        if not team:
            await update.message.reply_text('Этот чат не зарегистрирован как команда.')
            return

        stmt = select(GroupTaskAnswer).join(Task).filter(
            GroupTaskAnswer.team_id == team.id,
            Task.type == GROUP_TYPE
        ).order_by(GroupTaskAnswer.created.desc())
        result = await db_session.execute(stmt)
        last_answer = result.scalars().first()

        if not last_answer:
            await update.message.reply_text('Нет ответов на групповые задания.')
            return

        if last_answer.curator_feedback is not None:
            await update.message.reply_text(
                f'Ваша оценка за последнее групповое задание: {last_answer.curator_feedback}'
            )
        else:
            await update.message.reply_text(
                'Работа еще не проверена. Когда работа будет оценена, вам придет оповещение.'
            )
