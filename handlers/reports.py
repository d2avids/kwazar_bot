import os
from datetime import datetime

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from telegram import ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, ConversationHandler

from database.models import GroupTaskAnswer, Task, Team, User, UserAnswer
from utils.constants import (END_DATE, END_PERIOD_MESSAGE, GROUP_TYPE,
                             INCORRECT_DATE_MESSAGE, INDIVIDUAL_TYPE,
                             NO_DATA_FOR_PERIOD, REPORTS_PATH, START_DATE,
                             START_PERIOD_MESSAGE)
from utils.decorators import tutor_or_admin_required, with_db_session


class IndividualReport:
    @staticmethod
    @tutor_or_admin_required
    async def start_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            START_PERIOD_MESSAGE,
            reply_markup=ReplyKeyboardRemove()
        )
        return START_DATE

    @staticmethod
    async def get_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
        start_date_str = update.message.text
        try:
            start_date = datetime.strptime(start_date_str, '%d.%m.%Y')
            context.user_data['start_date'] = start_date
            await update.message.reply_text(END_PERIOD_MESSAGE)
            return END_DATE
        except ValueError:
            await update.message.reply_text(INCORRECT_DATE_MESSAGE)
            return START_DATE

    @staticmethod
    @with_db_session
    async def get_end_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
        end_date_str = update.message.text
        try:
            end_date = datetime.strptime(end_date_str, '%d.%m.%Y')
            context.user_data['end_date'] = end_date

            db_session = context.chat_data['db_session']
            stmt = select(UserAnswer, User, Task).join(User).join(Task).filter(
                UserAnswer.created >= context.user_data['start_date'],
                UserAnswer.created <= context.user_data['end_date'],
                Task.type == INDIVIDUAL_TYPE
            )
            result = await db_session.execute(stmt)
            answers = result.fetchall()

            if not answers:
                await update.message.reply_text(NO_DATA_FOR_PERIOD)
                return ConversationHandler.END

            data = []
            for answer, user, task in answers:
                data.append({
                    'ФИО': f'{user.last_name} {user.first_name} {user.patronymic or ""}'.strip(),
                    'Школа': user.school_name,
                    'Класс': f'{user.class_number}{user.class_symbol}',
                    'Текст задания': task.text,
                    'Ответ': answer.answer_text,
                    'Фидбек': answer.curator_feedback or '',
                    'Дата ответа': answer.created.strftime('%d.%m.%Y %H:%M'),
                    'Дата фидбека': answer.updated.strftime('%d.%m.%Y %H:%M') if answer.curator_feedback else ''
                })

            df = pd.DataFrame(data)
            os.makedirs(REPORTS_PATH, exist_ok=True)
            file_path = f'{REPORTS_PATH}/individual_report.xlsx'
            df.to_excel(file_path, index=False)

            await context.bot.send_document(chat_id=update.message.chat_id, document=open(file_path, 'rb'))
            return ConversationHandler.END

        except ValueError:
            await update.message.reply_text(INCORRECT_DATE_MESSAGE)
            return END_DATE


class TeamReport:
    @staticmethod
    @tutor_or_admin_required
    async def start_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            START_PERIOD_MESSAGE,
            reply_markup=ReplyKeyboardRemove()
        )
        return START_DATE

    @staticmethod
    async def get_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
        start_date_str = update.message.text
        try:
            start_date = datetime.strptime(start_date_str, '%d.%m.%Y')
            context.user_data['start_date'] = start_date
            await update.message.reply_text(END_PERIOD_MESSAGE)
            return END_DATE
        except ValueError:
            await update.message.reply_text(INCORRECT_DATE_MESSAGE)
            return START_DATE

    @staticmethod
    @with_db_session
    async def get_end_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
        end_date_str = update.message.text
        try:
            end_date = datetime.strptime(end_date_str, '%d.%m.%Y')
            context.user_data['end_date'] = end_date

            db_session = context.chat_data['db_session']
            stmt = select(GroupTaskAnswer).options(
                joinedload(GroupTaskAnswer.team).joinedload(Team.user),
                joinedload(GroupTaskAnswer.task)
            ).join(GroupTaskAnswer.task).filter(
                GroupTaskAnswer.created >= context.user_data['start_date'],
                GroupTaskAnswer.created <= context.user_data['end_date'],
                Task.type == GROUP_TYPE
            )
            result = await db_session.execute(stmt)
            answers = result.fetchall()

            if not answers:
                await update.message.reply_text(NO_DATA_FOR_PERIOD)
                return ConversationHandler.END

            data = []
            for row in answers:
                answer = row[0]
                team = answer.team
                task = answer.task
                data.append({
                    'Команда': team.name,
                    'Школа': team.school_name,
                    'Класс': f'{team.class_number}{team.class_symbol}',
                    'ФИО основателя команды': f'{team.user.last_name} {team.user.first_name} {team.user.patronymic or ""}'.strip(),
                    'Текст задания': task.text,
                    'Ответ на задание': answer.answer_text,
                    'Фидбек': answer.curator_feedback or '',
                    'Дата ответа': answer.created.strftime('%d.%m.%Y %H:%M'),
                    'Дата фидбека': answer.updated.strftime('%d.%m.%Y %H:%M') if answer.curator_feedback else ''
                })

            df = pd.DataFrame(data)
            os.makedirs(REPORTS_PATH, exist_ok=True)
            file_path = f'{REPORTS_PATH}/team_report.xlsx'
            df.to_excel(file_path, index=False)

            await context.bot.send_document(chat_id=update.message.chat_id, document=open(file_path, 'rb'))
            return ConversationHandler.END

        except ValueError as e:
            await update.message.reply_text(INCORRECT_DATE_MESSAGE)
            return END_DATE
