# на заметку: если не писать return ConversationHandler.END то функция являющаяся этапом диалога (Conversation) полность запуститься заново а не с какой то ее части
import csv
import random
import os
import numpy as np
import prettytable as pt
import pandas
import datetime
from uuid import uuid4
import pytz
from pandas import DataFrame
from prettytable import MSWORD_FRIENDLY, PLAIN_COLUMNS
from telegram import ParseMode, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton
from telegram.utils.helpers import mention_html
from template_of_tasks import some_task, taskes
import sys
import traceback
import logging
import psycopg2
from config import host, user, password, db_name
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
    JobQueue,
    CallbackQueryHandler
)

global black_list
black_list = []
global fot_time
fot_time = {}
global connection
connection = psycopg2.connect(
    host=host,
    user=user,
    password=password,
    database=db_name
)
# автосохранение
connection.autocommit = True  # connection.autocommit=False. В этом случае будет возможность откатить выполненный запрос к оригинальному состоянию в случае неудачи.

# Включим ведение журнала
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Определяем константы этапов разговора
REGISTRATION_FIRST, REGISTRATION_NICK_NAME, REGISTRATION_NAME, REGISTRATION_SURNAME, REGISTRATION_PASSWORD, \
LOGIN, LOGIN_DATA, CANCEL = range(8)

RANDOM_TASK_ANSWER, DICTIONARY_WORD, TIME_FOR_TASK_ANSWER, TASK_ALL_2, BUTTON, RANDOM_TASK, TASK_GRAMMATIKA, TASK_GRAMMATIKA_ANWSER, TASK_PREPOSITIONS, TASK_PREPOSITIONS_ANWSER, TASK_TIMES, TASK_TIMES_ANWSER = range(
    12)
ADMINISTRATOR_FIRST = range(1)
STUDENT_ACHIVMENT_SEOCND, STUDENT_STATISTIC_2, BUTTON_FOR_ADMIN_RESULT, STUDENT_ACHIVMENT_GRAMMA_TASK, STUDENT_ACHIVMENT_PREPOSITIONS_TASK, STUDENT_ACHIVMENT_TIME_TASK, STUDENT_ACHIVMENT_REGULAR_TASK = range(7)


# функция обратного вызова точки входа в разговор
def start(update, _):
    # Список кнопок для ответа

    reply_keyboard = [['/registration', '/login']]
    user = update.message.from_user
    # Создаем простую клавиатуру для ответа
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    # Начинаем разговор с вопроса
    update.message.reply_text('Привет! \n'
                              'Я телеграм бот, который поможет тебе выучить англиский ;)\n'
                              'Зарегистрируйся или войди в аккаунт, что бы перейти к моему функционалу\n'
                              'Чтобы зайти в администратора нажмите - /administrator',
                              reply_markup=markup_key, )
    logger.info("Пользователь %s, start", user.first_name)
    return ConversationHandler.END
    # переходим к этапу `GENDER`, это значит, что ответ
    # отправленного сообщения в виде кнопок будет список
    # обработчиков, определенных в виде значения ключа `GENDER`


def administrator(update: Update, context: CallbackContext):
    user1 = update.message.from_user
    logger.info("Пользователь %s: этап - exit_admin \ словарь - %s", user1.first_name, context.bot_data)
    reply_keyboard = [['/back']]
    user = update.message.from_user
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    ID = update.message.chat_id
    context.bot.send_message(chat_id=ID, text="Введите пароль админа(4321)", reply_markup=markup_key)
    logger.info("Пользователь %s: этап - administrator", user.first_name)
    return ADMINISTRATOR_FIRST


def administrator_first(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - exit_admin \ словарь - %s", user.first_name, context.bot_data)
    ID = update.message.chat_id
    message = update.message.from_user
    logger.info("Пользователь %s: этап - administrator_first", message.first_name)
    if update.message.text == '4321':
        key = str(update.effective_user.id) + ' is_admin'
        context.bot_data[key] = True

        return administrator_main(update, context)
    else:
        context.bot.send_message(chat_id=ID, text="неверный пароль админа")
        return ConversationHandler.END


def administrator_main(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - exit_admin \ словарь - %s", user.first_name, context.bot_data)
    ID = update.message.chat_id
    user = update.message.from_user
    logger.info("Пользователь %s: этап - administrator_main", user.first_name)
    try:
        key = str(update.effective_user.id) + ' is_admin'
        if context.bot_data[key]:
            reply_keyboard = [['/information_of_all_student', '/student_achivment', '/exit_admin']]
            markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
            context.bot.send_message(chat_id=ID, text="Выбирет варианты предлагаемые клавиатурой",
                                     reply_markup=markup_key)
            return ConversationHandler.END
        else:
            context.bot.send_message(chat_id=ID,
                                     text='вы не можете сюда попасть')
    except Exception as _ex:
        print("[INFO] Error while working with administrator_main", _ex)
        context.bot.send_message(chat_id=ID,
                                 text='нужно пройти логин админа')
        return ConversationHandler.END


def information_of_all_student(update: Update, context: CallbackContext):
    reply_keyboard = [['/information_of_all_student', '/student_achivment', '/exit_admin']]
    user = update.message.from_user
    logger.info("Пользователь %s: этап - information_of_all_student \ словарь - %s", user.first_name, context.bot_data)
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    cursor = connection.cursor()
    ID = update.message.chat_id
    try:
        key = str(update.effective_user.id) + ' is_admin'
        if context.bot_data[key]:
            cursor.execute("""
                    SELECT  id, nick_name, user_name, user_surname FROM users;
                    """)
            data = cursor.fetchall()
            with open(f"инфа_обо_всех{update.effective_user.id}.csv", "w") as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(
                    (
                        'id',
                        'nick_name',
                        'user_name',
                        'user_surname'

                    )
                )
            ### записываем данные
            for item in data:
                id = item[0]
                nick_name = item[1]
                user_name = item[2]
                user_surname = item[3]
                with open(f"инфа_обо_всех{update.effective_user.id}.csv", "a", encoding='utf-8',
                          newline='') as csv_file:
                    csv_writer = csv.writer(csv_file, delimiter=",",
                                            lineterminator="\r")
                    csv_writer.writerow(
                        (
                            id,
                            nick_name,
                            user_name,
                            user_surname,
                        )
                    )
            ### отправляем задание
            doc = open(f'инфа_обо_всех{update.effective_user.id}.csv', 'rb')
            context.bot.send_document(chat_id=ID, document=doc, reply_markup=markup_key)
            doc.close()
            os.remove(f'инфа_обо_всех{update.effective_user.id}.csv')
            return ConversationHandler.END
        else:
            context.bot.send_message(chat_id=ID,
                                     text='вы не можете сюда попасть')
            return ConversationHandler.END
    except Exception as _ex:
        print("[INFO] Error while working with PostgreSQL", _ex)
        context.bot.send_message(chat_id=ID,
                                 text='нужно пройти логин админа')
        return ConversationHandler.END

    finally:
        if connection:
            cursor.close()
            # connection.close()
            print("[INFO] PostgreSQL connection closed")





def student_achivment(update: Update, context: CallbackContext):
    ID = update.message.chat_id
    user = update.message.from_user
    logger.info("Пользователь %s: этап - student_achivment \ словарь - %s", user.first_name, context.bot_data)
    try:
        markup_key = ReplyKeyboardRemove()
        key = str(update.effective_user.id) + ' is_admin'
        if context.bot_data[key]:
            keyboard = [

                InlineKeyboardButton("Результаты случайного задания", callback_data='Результаты случайного задания'),
                InlineKeyboardButton("Результаты задания на грамматику", callback_data='Результаты задания на грамматику'),
                InlineKeyboardButton("Результаты задания на предлоги", callback_data='Результаты задания на предлоги'),
                InlineKeyboardButton("Результаты регулярного задания", callback_data='Результаты регулярного задания'),
                InlineKeyboardButton("Результаты задания на времена", callback_data='Результаты задания на времена')
            ]
            context.bot.send_message(chat_id=ID,
                                     text="Все результаты", reply_markup=markup_key)
            reply_markup = InlineKeyboardMarkup(build_menu1(keyboard, n_cols=1))
            context.bot.send_message(chat_id=ID,
                                     text="Выберите", reply_markup=reply_markup)
            return BUTTON_FOR_ADMIN_RESULT
            # return STUDENT_ACHIVMENT_SEOCND
        else:
            context.bot.send_message(chat_id=ID,
                                     text='вы не можете сюда попасть')
    except Exception as _ex:
        print("[INFO] Error while working with administrator_main", _ex)
        context.bot.send_message(chat_id=ID,
                                 text='нужно пройти логин админа')
        return ConversationHandler.END


def button_for_admin_result(update: Update, context: CallbackContext):
    ID = update.effective_message.chat_id
    query = update.callback_query
    query.answer()

    # This will define which button the user tapped on (from what you assigned to "callback_data". As I assigned them "1" and "2"):
    choice = query.data
    print(choice)
    print('11111111111111111')
    # Now u can define what choice ("callback_data") do what like this:
    if choice == 'Результаты случайного задания':
        context.bot.send_message(chat_id=ID,
                                 text='Напишите никнейм ученика'
                                 )
        return STUDENT_ACHIVMENT_SEOCND


    if choice == 'Результаты задания на грамматику':
        context.bot.send_message(chat_id=ID,
                                 text='Напишите никнейм ученика'
                                 )
        return STUDENT_ACHIVMENT_GRAMMA_TASK


    if choice == 'Результаты задания на предлоги':
        context.bot.send_message(chat_id=ID,
                                 text='Напишите никнейм ученика'
                                  )
        return STUDENT_ACHIVMENT_PREPOSITIONS_TASK


    if choice == 'Результаты задания на времена':
        context.bot.send_message(chat_id=ID,
                                 text='Напишите никнейм ученика'
                                 )
        return STUDENT_ACHIVMENT_TIME_TASK

    if choice == 'Результаты регулярного задания':
        context.bot.send_message(chat_id=ID,
                                 text='Напишите никнейм ученика'
                                 )
        return STUDENT_ACHIVMENT_REGULAR_TASK

    if choice == 'Результаты задания на времена':
        context.bot.send_message(chat_id=ID,
                                 text='Напишите никнейм ученика'
                                 )
        return STUDENT_ACHIVMENT_TIME_TASK



def student_achivment_second(update: Update, context: CallbackContext):
    ID = update.message.chat_id
    user = update.message.from_user
    logger.info("Пользователь %s: этап - student_achivment_second \ словарь - %s", user.first_name, context.bot_data)
    cursor = connection.cursor()  # отркываем соединение с базой данных
    reply_keyboard = [['/information_of_all_student', '/student_achivment', '/exit_admin']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    messege = update.message.text
    try:
        key = str(update.effective_user.id) + ' is_admin'
        print(context.bot_data[key])
        if context.bot_data[key]:
            ### get id
            cursor.execute("""
                    SELECT  * FROM users;
                    """)
            users_info = []
            for i in (cursor.fetchall()):
                for item in i:
                    users_info.append(item)
            if messege in users_info:
                cursor.execute("""
                      SELECT  id FROM users WHERE nick_name = (%s);
                      """, (messege,))
                user_id = cursor.fetchone()[0]
                print(user_id)
                ###
                ### get task2
                try:
                    cursor.execute("""
                                        SELECT  errors, attemps,  date_do_task, number_of_tasks, number_of_right_answer, task  FROM time_random_task_result WHERE fk_random_task_user = (%s);
                                        """, (user_id,))
                    time_result_random_task = cursor.fetchall()
                    print(time_result_random_task)
                    ###
                    ### даем имена колонкам
                    with open(f"результаты_обязательного_задания_{update.effective_user.id}.csv", "w") as csv_file:
                        csv_writer = csv.writer(csv_file)
                        csv_writer.writerow(
                            (
                                'unit',
                                'errors',
                                'attemps',
                                'date',
                                'number_of_tasks',
                                'number_of_right_answer'
                            )
                        )
                    ### записываем данные
                    for item in time_result_random_task:
                        unit = item[5]
                        errors = item[0]
                        attemps = item[1]
                        date = item[2]
                        number_of_tasks = item[3]
                        number_of_right_answer = item[4]
                        with open(f"результаты_обязательного_задания_{update.effective_user.id}.csv", "a",
                                  encoding='utf-8', newline='') as csv_file:
                            csv_writer = csv.writer(csv_file, delimiter=",",
                                                    lineterminator="\r")
                            csv_writer.writerow(
                                (
                                    unit,
                                    errors,
                                    attemps,
                                    date,
                                    number_of_tasks,
                                    number_of_right_answer
                                )
                            )
                    ### отправляем задание
                    doc = open(f'результаты_обязательного_задания_{update.effective_user.id}.csv', 'rb')
                    context.bot.send_document(chat_id=ID, document=doc, reply_markup=markup_key)
                    doc.close()
                    os.remove(f'результаты_обязательного_задания_{update.effective_user.id}.csv')
                except Exception as _ex:
                    context.bot.send_document(chat_id=ID,
                                              document='Невозможно сформировать, возможно ученик не выполнял задания',
                                              reply_markup=markup_key)
                    print("[INFO] Error while working with 2", _ex)

            else:
                context.bot.send_message(chat_id=ID,
                                         text='Такого ника не существует', reply_markup=markup_key)
        else:
            context.bot.send_message(chat_id=ID,
                                     text='вы не можете сюда попасть')
            return ConversationHandler.END
    except Exception as _ex:
        print("[INFO] Error while working with 1", _ex)
        context.bot.send_message(chat_id=ID,
                                 text='Такого ника не существует')
    finally:
        if connection:
            cursor.close()
            # connection.close()
            print("[INFO] PostgreSQL connection closed")
            return ConversationHandler.END


def student_achivment_regular_task(update: Update, context: CallbackContext):
    ID = update.message.chat_id
    user = update.message.from_user
    logger.info("Пользователь %s: этап - student_achivment_second \ словарь - %s", user.first_name, context.bot_data)
    cursor = connection.cursor()  # отркываем соединение с базой данных
    reply_keyboard = [['/information_of_all_student', '/student_achivment', '/exit_admin']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    messege = update.message.text
    try:
        key = str(update.effective_user.id) + ' is_admin'
        print(context.bot_data[key])
        if context.bot_data[key]:
            ### get id
            cursor.execute("""
                    SELECT  * FROM users;
                    """)
            users_info = []
            for i in (cursor.fetchall()):
                for item in i:
                    users_info.append(item)
            if messege in users_info:
                cursor.execute("""
                      SELECT  id FROM users WHERE nick_name = (%s);
                      """, (messege,))
                user_id = cursor.fetchone()[0]
                print(user_id)
                ###
                ### get task
                try:
                    cursor.execute("""
                                        SELECT  errors, date_do_task, number_of_tasks, number_of_right_answer, task  FROM random_task_result WHERE fk_random_task_user = (%s);
                                        """, (user_id,))
                    time_result_random_task = cursor.fetchall()
                    print(time_result_random_task)
                    ###
                    ### даем имена колонкам
                    with open(f"результаты_регудярного_задания_{update.effective_user.id}.csv", "w") as csv_file:
                        csv_writer = csv.writer(csv_file)
                        csv_writer.writerow(
                            (
                                'unit',
                                'errors',
                                'date',
                                'number_of_tasks',
                                'number_of_right_answer'
                            )
                        )
                    ### записываем данные
                    for item in time_result_random_task:
                        unit = item[4]
                        errors = item[0]
                        date = item[1]
                        number_of_tasks = item[2]
                        number_of_right_answer = item[3]
                        with open(f"результаты_регудярного_задания_{update.effective_user.id}.csv", "a",
                                  encoding='utf-8', newline='') as csv_file:
                            csv_writer = csv.writer(csv_file, delimiter=",",
                                                    lineterminator="\r")
                            csv_writer.writerow(
                                (
                                    unit,
                                    errors,
                                    date,
                                    number_of_tasks,
                                    number_of_right_answer
                                )
                            )
                    ### отправляем задание
                    doc = open(f'результаты_регудярного_задания_{update.effective_user.id}.csv', 'rb')
                    context.bot.send_document(chat_id=ID, document=doc, reply_markup=markup_key)
                    doc.close()
                    os.remove(f'результаты_регудярного_задания_{update.effective_user.id}.csv')
                except Exception as _ex:
                    context.bot.send_document(chat_id=ID,
                                              document='Невозможно сформировать, возможно ученик не выполнял задания',
                                              reply_markup=markup_key)
                    print("[INFO] Error while working with 2", _ex)

            else:
                context.bot.send_message(chat_id=ID,
                                         text='Такого ника не существует', reply_markup=markup_key)
        else:
            context.bot.send_message(chat_id=ID,
                                     text='вы не можете сюда попасть')
            return ConversationHandler.END
    except Exception as _ex:
        print("[INFO] Error while working with 1", _ex)
        context.bot.send_message(chat_id=ID,
                                 text='Такого ника не существует')
    finally:
        if connection:
            cursor.close()
            # connection.close()
            print("[INFO] PostgreSQL connection closed")
            return ConversationHandler.END


def student_achivment_gramma_task(update: Update, context: CallbackContext):
    ID = update.effective_message.chat_id
    user = update.message.from_user
    logger.info("Пользователь %s: этап - student_achivment_second \ словарь - %s", user.first_name, context.bot_data)
    cursor = connection.cursor()  # отркываем соединение с базой данных
    reply_keyboard = [['/information_of_all_student', '/student_achivment', '/exit_admin']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    messege = update.message.text
    try:
        key = str(update.effective_user.id) + ' is_admin'
        print(context.bot_data[key])
        if context.bot_data[key]:
            ### get id
            cursor.execute("""
                    SELECT  * FROM users;
                    """)
            users_info = []
            for i in (cursor.fetchall()):
                for item in i:
                    users_info.append(item)
            if messege in users_info:
                cursor.execute("""
                      SELECT  id FROM users WHERE nick_name = (%s);
                      """, (messege,))
                user_id = cursor.fetchone()[0]
                print(user_id)
                ###
                ### get task
                print(1)
                try:

                    cursor.execute("""
                                        SELECT  errors,  date_do_task, number_of_tasks, number_of_right_answer, task  FROM task_grammatika_result WHERE fk_random_task_user = (%s);
                                        """, (user_id,))
                    time_result_random_task = cursor.fetchall()
                    ###
                    print(time_result_random_task)
                    ### даем имена колонкам
                    with open(f"результаты_задания_на_грамматику_{update.effective_user.id}.csv", "w") as csv_file:
                        csv_writer = csv.writer(csv_file)
                        csv_writer.writerow(
                            (
                                'unit',
                                'errors',
                                'date',
                                'number_of_tasks',
                                'number_of_right_answer'
                            )
                        )
                    ### записываем данные
                    for item in time_result_random_task:
                        unit = item[4]
                        errors = item[0]
                        date = item[1]
                        number_of_tasks = item[2]
                        number_of_right_answer = item[3]
                        print(3)
                        with open(f"результаты_задания_на_грамматику_{update.effective_user.id}.csv", "a",
                                  encoding='utf-8', newline='') as csv_file:
                            csv_writer = csv.writer(csv_file, delimiter=",",
                                                    lineterminator="\r")
                            csv_writer.writerow(
                                (
                                    unit,
                                    errors,
                                    date,
                                    number_of_tasks,
                                    number_of_right_answer
                                )
                            )
                    ### отправляем задание
                    doc = open(f'результаты_задания_на_грамматику_{update.effective_user.id}.csv', 'rb')
                    print(3)
                    context.bot.send_document(chat_id=ID, document=doc, reply_markup=markup_key)
                    doc.close()
                    os.remove(f'результаты_задания_на_грамматику_{update.effective_user.id}.csv')
                except Exception as _ex:
                    context.bot.send_document(chat_id=ID,
                                              document='Невозможно сформировать, возможно ученик не выполнял задания',
                                              reply_markup=markup_key)
                    print("[INFO] Error while working with 2", _ex)

            else:
                context.bot.send_message(chat_id=ID,
                                         text='Такого ника не существует', reply_markup=markup_key)
        else:
            context.bot.send_message(chat_id=ID,
                                     text='вы не можете сюда попасть')
            return ConversationHandler.END
    except Exception as _ex:
        print("[INFO] Error while working with 1", _ex)
        context.bot.send_message(chat_id=ID,
                                 text='Такого ника не существует')
    finally:
        if connection:
            cursor.close()
            # connection.close()
            print("[INFO] PostgreSQL connection closed")
            return ConversationHandler.END


def student_achivment_prepositions_task(update: Update, context: CallbackContext):
    ID = update.message.chat_id
    user = update.message.from_user
    logger.info("Пользователь %s: этап - student_achivment_second \ словарь - %s", user.first_name, context.bot_data)
    cursor = connection.cursor()  # отркываем соединение с базой данных
    reply_keyboard = [['/information_of_all_student', '/student_achivment', '/exit_admin']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    messege = update.message.text
    try:
        key = str(update.effective_user.id) + ' is_admin'
        print(context.bot_data[key])
        if context.bot_data[key]:
            ### get id
            cursor.execute("""
                    SELECT  * FROM users;
                    """)
            users_info = []
            for i in (cursor.fetchall()):
                for item in i:
                    users_info.append(item)
            if messege in users_info:
                cursor.execute("""
                      SELECT  id FROM users WHERE nick_name = (%s);
                      """, (messege,))
                user_id = cursor.fetchone()[0]
                print(user_id)
                ###
                ### get task
                try:
                    cursor.execute("""
                                        SELECT  errors,  date_do_task, number_of_tasks, number_of_right_answer, task  FROM task_prepositions_result WHERE fk_random_task_user = (%s);
                                        """, (user_id,))
                    time_result_random_task = cursor.fetchall()
                    ###
                    ### даем имена колонкам
                    with open(f"результаты_задания_на_предлоги_{update.effective_user.id}.csv", "w") as csv_file:
                        csv_writer = csv.writer(csv_file)
                        csv_writer.writerow(
                            (
                                'unit',
                                'errors',
                                'date',
                                'number_of_tasks',
                                'number_of_right_answer'
                            )
                        )
                    ### записываем данные
                    for item in time_result_random_task:
                        unit = item[4]
                        errors = item[0]
                        date = item[1]
                        number_of_tasks = item[2]
                        number_of_right_answer = item[3]
                        with open(f"результаты_задания_на_предлоги_{update.effective_user.id}.csv", "a",
                                  encoding='utf-8', newline='') as csv_file:
                            csv_writer = csv.writer(csv_file, delimiter=",",
                                                    lineterminator="\r")
                            csv_writer.writerow(
                                (
                                    unit,
                                    errors,
                                    date,
                                    number_of_tasks,
                                    number_of_right_answer
                                )
                            )
                    ### отправляем задание
                    doc = open(f'результаты_задания_на_предлоги_{update.effective_user.id}.csv', 'rb')
                    context.bot.send_document(chat_id=ID, document=doc, reply_markup=markup_key)
                    doc.close()
                    os.remove(f'результаты_задания_на_предлоги_{update.effective_user.id}.csv')
                except Exception as _ex:
                    context.bot.send_document(chat_id=ID,
                                              document='Невозможно сформировать, возможно ученик не выполнял задания',
                                              reply_markup=markup_key)
                    print("[INFO] Error while working with 2", _ex)

            else:
                context.bot.send_message(chat_id=ID,
                                         text='Такого ника не существует', reply_markup=markup_key)
        else:
            context.bot.send_message(chat_id=ID,
                                     text='вы не можете сюда попасть')
            return ConversationHandler.END
    except Exception as _ex:
        print("[INFO] Error while working with 1", _ex)
        context.bot.send_message(chat_id=ID,
                                 text='Такого ника не существует')
    finally:
        if connection:
            cursor.close()
            # connection.close()
            print("[INFO] PostgreSQL connection closed")
            return ConversationHandler.END


def student_achivment_time_task(update: Update, context: CallbackContext):
    ID = update.message.chat_id
    user = update.message.from_user
    logger.info("Пользователь %s: этап - student_achivment_second \ словарь - %s", user.first_name, context.bot_data)
    cursor = connection.cursor()  # отркываем соединение с базой данных
    reply_keyboard = [['/information_of_all_student', '/student_achivment', '/exit_admin']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    messege = update.message.text
    try:
        key = str(update.effective_user.id) + ' is_admin'
        print(context.bot_data[key])
        if context.bot_data[key]:
            ### get id
            cursor.execute("""
                    SELECT  * FROM users;
                    """)
            users_info = []
            for i in (cursor.fetchall()):
                for item in i:
                    users_info.append(item)
            if messege in users_info:
                cursor.execute("""
                      SELECT  id FROM users WHERE nick_name = (%s);
                      """, (messege,))
                user_id = cursor.fetchone()[0]
                print(user_id)
                ###
                ### get task
                try:
                    cursor.execute("""
                                        SELECT  errors,  date_do_task, number_of_tasks, number_of_right_answer, task  FROM task_time_result WHERE fk_random_task_user = (%s);
                                        """, (user_id,))
                    time_result_random_task = cursor.fetchall()
                    ###
                    ### даем имена колонкам
                    with open(f"результаты_задания_на_времена_{update.effective_user.id}.csv", "w") as csv_file:
                        csv_writer = csv.writer(csv_file)
                        csv_writer.writerow(
                            (
                                'unit',
                                'errors',
                                'date',
                                'number_of_tasks',
                                'number_of_right_answer'
                            )
                        )
                    ### записываем данные
                    for item in time_result_random_task:
                        unit = item[4]
                        errors = item[0]
                        date = item[1]
                        number_of_tasks = item[2]
                        number_of_right_answer = item[3]
                        with open(f"результаты_задания_на_времена_{update.effective_user.id}.csv", "a",
                                  encoding='utf-8', newline='') as csv_file:
                            csv_writer = csv.writer(csv_file, delimiter=",",
                                                    lineterminator="\r")
                            csv_writer.writerow(
                                (
                                    unit,
                                    errors,
                                    date,
                                    number_of_tasks,
                                    number_of_right_answer
                                )
                            )
                    ### отправляем задание
                    doc = open(f'результаты_задания_на_времена_{update.effective_user.id}.csv', 'rb')
                    context.bot.send_document(chat_id=ID, document=doc, reply_markup=markup_key)
                    doc.close()
                    os.remove(f'результаты_задания_на_времена_{update.effective_user.id}.csv')
                except Exception as _ex:
                    context.bot.send_document(chat_id=ID,
                                              document='Невозможно сформировать, возможно ученик не выполнял задания',
                                              reply_markup=markup_key)
                    print("[INFO] Error while working with 2", _ex)

            else:
                context.bot.send_message(chat_id=ID,
                                         text='Такого ника не существует', reply_markup=markup_key)
        else:
            context.bot.send_message(chat_id=ID,
                                     text='вы не можете сюда попасть')
            return ConversationHandler.END
    except Exception as _ex:
        print("[INFO] Error while working with 1", _ex)
        context.bot.send_message(chat_id=ID,
                                 text='Такого ника не существует')
    finally:
        if connection:
            cursor.close()
            # connection.close()
            print("[INFO] PostgreSQL connection closed")
            return ConversationHandler.END


def student_statistic(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - student_statistic \ словарь - %s", user.first_name, context.bot_data)
    ID = update.message.chat_id
    context.bot.send_message(chat_id=ID,
                             text='введите никнейм')
    return STUDENT_STATISTIC_2


def student_statistic_2(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - student_statistic_2 \ словарь - %s", user.first_name, context.bot_data)
    ID = update.message.chat_id
    Messege = update.message.text
    cursor = connection.cursor()
    # random
    cursor.execute("""
    SELECT id FROM users WHERE nick_name = (%s)
    """, (Messege,))
    fk_random_task_user = (cursor.fetchone()[0])
    cursor.execute("""
                      SELECT task, errors,  date_do_task, number_of_tasks, number_of_right_answer FROM random_task WHERE fk_random_task_user = (%s);
                      """, (fk_random_task_user,))
    result_random_task = cursor.fetchall()
    print(result_random_task)
    # time
    cursor.execute("""
                      SELECT task, errors, attemps, date_do_task, number_of_tasks, number_of_right_answer FROM time_random_task WHERE fk_random_task_user = (%s);
                      """, (fk_random_task_user,))
    time_result_random_task = cursor.fetchall()
    print(time_result_random_task)
    # statistic
    df = DataFrame(result_random_task,
                   columns=['task', 'errors', 'date_do_task', 'number_of_tasks', 'number_of_right_answer'])
    df = df.fillna(value=np.nan)
    df = df.astype({'date_do_task': np.datetime64})
    df['number_of_right_answer'] = df['number_of_right_answer'].astype('Int64')
    datatypes = df.dtypes
    # print(datatypes)
    # print(df['number_of_right_answer'])
    # print(df.tail(1))
    # print(df['number_of_right_answer'].value_counts())
    # print(len(df.index)) # df['number_of_right_answer'] - can

    df['sred'] = df.apply(lambda x: x["number_of_right_answer"] / (x["number_of_tasks"] / 100), axis=1)
    print(df['sred'])

    # statistic 2
    df_second = DataFrame(time_result_random_task,
                          columns=['task', 'errors', 'attemps', 'date_do_task', 'number_of_tasks',
                                   'number_of_right_answer'])
    df_second = df_second.fillna(value=np.nan)
    df_second = df_second.astype({'date_do_task': np.datetime64})
    df_second['number_of_right_answer'] = df_second['number_of_right_answer'].astype('Int64')
    df_second = df_second.astype({'attemps': np.int64})

    df_mean_number_of_attemp = df_second["attemps"].mean()
    print('средене кол-во попыток:', df_mean_number_of_attemp)

    df_second['sred'] = df_second.apply(lambda x: x["number_of_right_answer"] / (x["number_of_tasks"] / 100), axis=1)
    print(df_second['sred'].mean())

    context.bot.send_message(chat_id=ID,
                             text=f'средний процент в кажом не обязательном задании:  {df["sred"].mean().round(2)}%\n'
                                  f'средний процент в кажом обязательном задании:  {(df_second["sred"].mean()).round(2)}%\n'
                                  f'средене кол-во попыток: {df_mean_number_of_attemp}')
    # percent_number_of_right_answer = df_second["number_of_right_answer"].sum()/one_percent
    return ConversationHandler.END


def exit_admin(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - exit_admin \ словарь - %s", user.first_name, context.bot_data)
    ID = update.message.chat_id
    try:
        key_admin = str(update.effective_user.id) + ' is_admin'
        print(context.bot_data[key_admin])
        del context.bot_data[key_admin]
        context.bot.send_message(chat_id=ID,
                                 text="Вы успешно вышли из аккаунта, надеюсь еще увидемся -)\n"
                                      "Если хотите снова войти нажмите сюда - /start")
        return ConversationHandler.END
    except Exception as _ex:
        print("[INFO] Error while working with PostgreSQL", _ex)
        context.bot.send_message(chat_id=ID,
                                 text="Нужно пройти вход админа")
        return ConversationHandler.END


def registration(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - registration \ словарь - %s", user.first_name, context.bot_data)
    ID = update.message.chat_id
    try:
        try:
            key = str(update.effective_user.id) + ' is_admin'
            if context.bot_data[key]:
                context.bot.send_message(chat_id=ID,
                                         text='нельзя быть админом и учеником')
                return ConversationHandler.END
        except Exception as _ex:
            reply_keyboard = [['/back']]
            markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
            key = str(update.effective_user.id)
            global black_list
            if key in black_list:
                context.bot.send_message(chat_id=ID, text="Вы уже регистрировались \n"
                                                          "Я отправлю вас на вход в аккаунт.\n"
                                                          "Если хотите восстановить пароль обратитесь к админу(к сожалению пока только так)",
                                         reply_markup=markup_key)
                return login(update, context)
            else:
                context.bot.send_message(chat_id=ID, text="Введите пароль ученика, (1234 , чтобы посторонние не заходили, пока проект на прверке оставлю ппароль тут)", reply_markup=markup_key)
                return REGISTRATION_FIRST
    except Exception as _ex:
        print("[INFO] Error while working with registration", _ex)
        context.bot.send_message(chat_id=ID,
                                 text='что то пошло не иак')
        return ConversationHandler.END


def login(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - login \ словарь - %s, bl_lis - %s", user.first_name, context.bot_data,
                black_list)
    ID = update.message.chat_id
    try:
        try:
            key = str(update.effective_user.id) + ' is_admin'
            if context.bot_data[key]:
                context.bot.send_message(chat_id=ID,
                                         text='нельзя быть админом и учеником')
                return ConversationHandler.END
        except Exception as _ex:
            reply_keyboard = [['/back']]
            markup_key = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

            context.bot.send_message(chat_id=ID, text="Введите свой никнейм и пароль через пробел \n"
                                                      "Пример: user 1234 ", reply_markup=markup_key)
            return LOGIN_DATA
    except Exception as _ex:
        print("[INFO] Error while working with registration", _ex)
        context.bot.send_message(chat_id=ID,
                                 text='что то пошло не иак')
        return ConversationHandler.END


def back(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - back \ словарь - %s", user.first_name, context.bot_data)
    ID = update.message.chat_id
    try:
        key = str(update.effective_user.id)
        if 'after_login' in context.bot_data[key]:
            context.bot.send_message(ID, text='Не возможно использовать после регистрации')

        else:
            user = update.message.from_user
            reply_keyboard = [['/registration', '/login']]
            markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
            logger.info("Юсер %s вернулся назад", user.first_name)
            context.bot.send_message(ID, text='Вы вернулись в самое начало', reply_markup=markup_key)
            return ConversationHandler.END
    except Exception as _ex:
        user = update.message.from_user
        reply_keyboard = [['/registration', '/login']]
        markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        logger.info("Юсер %s вернулся назад", user.first_name)
        context.bot.send_message(ID, text='Вы вернулись в самое начало', reply_markup=markup_key)
        return ConversationHandler.END


def step_back(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - step_back \ словарь - %s", user.first_name, context.bot_data)
    key = str(update.effective_user.id)
    key_for_step = key + 'step'
    for_stages = context.bot_data[key_for_step]
    reply_keyboard = [['/back']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    ID = update.message.chat_id
    context.bot.send_message(chat_id=ID, text="шаг назад", reply_markup=markup_key)
    if for_stages == REGISTRATION_NICK_NAME:
        context.bot_data[key] = context.bot_data[key].replace(f'{context.bot_data[key]}', '')
        context.bot.send_message(chat_id=ID, text="Этап: 1/4 "
                                                  "Введите свой никнейм", reply_markup=markup_key)
    elif for_stages == REGISTRATION_NAME:
        context.bot_data[key].pop(1)
        context.bot.send_message(chat_id=ID,
                                 text="Этап: 2/4 "
                                      "Введите свое имя", reply_markup=markup_key)
    elif for_stages == REGISTRATION_SURNAME:
        context.bot_data[key].pop(2)
        context.bot.send_message(chat_id=ID,
                                 text="Этап: 3/4 "
                                      "Введите свою фамилию", reply_markup=markup_key)
    elif for_stages == REGISTRATION_PASSWORD:
        context.bot_data[key].pop(3)
        context.bot.send_message(chat_id=ID,
                                 text="Этап: 4/4 "
                                      "Введите свой пароль", reply_markup=markup_key)

    context.bot_data.pop(key_for_step)
    return for_stages


def login_data(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - login_data \ словарь - %s", user.first_name, context.bot_data)
    log = True
    pas = True
    password_user_nick_name = None
    password_from_user = None
    ID = update.message.chat_id
    user_data = update.message.text.split()
    print(user_data)
    if len(user_data) != 2:
        context.bot.send_message(chat_id=ID, text="Не правилльный формат ввода")
    else:
        # print('----------', context.bot_data)
        # # print(update.update_id)
        try:
            reply_keyboard = [['/back']]
            markup_key = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)

            ###  Извлекаю все данные из таблицы и смотрю есть ли в нем такой никнейм
            cursor = connection.cursor()
            cursor.execute("""
            SELECT  * FROM users;
            """)
            users_info = []
            for i in (cursor.fetchall()):
                for item in i:
                    users_info.append(item)
            ###

            ### По заданному никнейму смотрю пароль от аккаунта с этим ником в первом execute, потом смотрю есть ли в бд хеш пароля введенного пользователeм\
            if user_data[0] in users_info:
                cursor.execute("""
                        SELECT password
                        FROM users
                        WHERE nick_name = %s;
                        """, (user_data[0],))
                password_user_nick_name = cursor.fetchone()[0]
                cursor.execute("""
                             SELECT password FROM users WHERE password = crypt(%s, password);""",
                               (user_data[1],)
                               )
                password_from_user = cursor.fetchone()[0]
            else:
                log = False
            ###

            ### пароль этого аккауниа, сравниваю первый хеш со вторым, если они равны - значит пароль верный
            print(password_user_nick_name, password_from_user)
            if password_user_nick_name == password_from_user:

                pass
            else:
                pas = False
            ###

            ### если то и то True то все супер
            if pas and log:
                cursor.execute(
                    """
                    SELECT id
                    FROM users
                    WHERE nick_name = %s;
                    """, (user_data[0],)
                )
                user_id = (cursor.fetchall()[0][0])
                key = str(update.effective_user.id)
                context.bot_data[key] = [user_id, password_from_user, user_data[0], user_data[1], 'after_login']
                markup_key = ReplyKeyboardRemove()  # удаление клавы
                global black_list
                if key in black_list:
                    pass
                else:
                    black_list = []
                    black_list.append(key)
                context.bot.send_message(chat_id=ID, text="Все супер, такого вроде помню", reply_markup=markup_key)
                return ConversationHandler.END, after_login(update,
                                                            context)  # выдает предупреждение но работает нормально. Тут завенршается этап регистрации и входа
                # все предадущие функции должны быть заблокированы
            else:
                context.bot.send_message(chat_id=ID,
                                         text="Такого никнейма или пароля не существует, пожалуйста зарегиструйтесь или проверьте правильно ли вы ввели",
                                         reply_markup=markup_key)

            ###

            ###
        except Exception as _ex:
            print("[INFO] Error while working with PostgreSQL", _ex)
        finally:
            if connection:
                cursor.close()
                # connection.close()
                print("[INFO] PostgreSQL connection closed")
            ###


def registration_first(update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - registration_first \ словарь - %s", user.first_name, context.bot_data)
    reply_keyboard = [['/back']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    # определяем пользователя
    ID = update.message.chat_id
    # Пишем в журнал пол пользователя
    if update.message.text == '1234':
        context.bot.send_message(chat_id=ID,
                                 text="Этап: 1/4 "
                                      "Введите свой никнейм", reply_markup=markup_key)
        return REGISTRATION_NICK_NAME
    else:
        context.bot.send_message(chat_id=ID, text="ERROR")
        return ConversationHandler.END


def registration_nick_name(update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - registration_nick_name \ словарь - %s", user.first_name, context.bot_data)
    key = str(update.effective_user.id)
    key_for_step = key + 'step'
    reply_keyboard = [['/back', '/step_back']]
    context.bot_data[key_for_step] = REGISTRATION_NICK_NAME
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    ID = update.message.chat_id  # получаем id пользователя что бы отправлять ему сообщение а не всем
    user_nick_name = update.message.text
    try:
        ### извлекаю все данные из таблицы и смотрю есть ли в нем такой никнейм
        cursor = connection.cursor()
        cursor.execute("""
        SELECT  * FROM users;
        """)
        users_info = []
        for i in (cursor.fetchall()):
            for item in i:
                users_info.append(item)
        ###

        ### если никнейм уже есть такой , меняй иначе перехожу дальше а никнейм сохр
        if user_nick_name in users_info:
            context.bot.send_message(chat_id=ID,
                                     text="Такой никнейм уже занят, пожалуйста выберите другой или войдиете в систему",
                                     reply_markup=markup_key)
        else:
            context.bot_data[
                key] = user_nick_name  # передаем контексту в словарь наш никнейм что бы сохранить промежуточные данные, с ключом-id user в телеге
            context.bot.send_message(chat_id=ID,
                                     text="Этап: 2/4 "
                                          "Введите свое имя", reply_markup=markup_key)
            return REGISTRATION_NAME

        ###
    except Exception as _ex:
        print("[INFO] Error while working with PostgreSQL", _ex)
    finally:
        if connection:
            cursor.close()
            # connection.close()
            print("[INFO] PostgreSQL connection closed")


def registration_name(update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - registration_name \ словарь - %s", user.first_name, context.bot_data)
    key = str(update.effective_user.id)  # id user
    first_stage = context.bot_data.get(key, 'Not found')  # забираем никнейм из предыдущего шага
    reply_keyboard = [['/back', '/step_back']]
    key_for_step = key + 'step'
    context.bot_data[key_for_step] = REGISTRATION_NAME
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    ID = update.message.chat_id  # получаем id пользователя что бы отправлять ему сообщение а не всем
    user_name = update.message.text
    try:
        ### извлекаю все данные из таблицы и смотрю есть ли в нем такой никнейм
        cursor = connection.cursor()
        cursor.execute("""
        SELECT  * FROM users;
        """)
        users_info = []
        for i in (cursor.fetchall()):
            for item in i:
                users_info.append(item)
        ###

        context.bot_data[key] = [''.join(first_stage),
                                 user_name]  # помещаем так же в словарь контекста по ключю - id usera, тлько теперь список из имени и ника
        context.bot.send_message(chat_id=ID,
                                 text="Этап: 3/4 "
                                      "Введите свою фамилию", reply_markup=markup_key)
        return REGISTRATION_SURNAME

        ###
    except Exception as _ex:
        print("[INFO] Error while working with PostgreSQL", _ex)
    finally:
        if connection:
            cursor.close()
            # connection.close()
            print("[INFO] PostgreSQL connection closed")


def registration_surname(update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - registration_surname \ словарь - %s", user.first_name, context.bot_data)
    key = str(update.effective_user.id)  # user id
    second_stage = context.bot_data.get(key, 'Not found')  # список имени и ника
    reply_keyboard = [['/back', '/step_back']]
    key_for_step = key + 'step'
    context.bot_data[key_for_step] = REGISTRATION_SURNAME
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    ID = update.message.chat_id  # получаем id пользователя что бы отправлять ему сообщение а не всем
    user_surname = update.message.text
    try:
        ### извлекаю все данные из таблицы и смотрю есть ли в нем такой никнейм
        cursor = connection.cursor()
        cursor.execute("""
        SELECT  * FROM users;
        """)
        users_info = []
        for i in (cursor.fetchall()):
            for item in i:
                users_info.append(item)
        ###

        context.bot_data[key] = second_stage + [
            user_surname]  # помещаем так же в словарь контекста по ключю - id usera, список,\
        # хз почему выделяется если по человечески делать то не работает
        # print('--------',context.bot_data[key])
        context.bot.send_message(chat_id=ID,
                                 text="Этап: 4/4 "
                                      "Введите свой пароль", reply_markup=markup_key)
        return REGISTRATION_PASSWORD

        ###
    except Exception as _ex:
        print("[INFO] Error while working with PostgreSQL", _ex)
    finally:
        if connection:
            cursor.close()
            # connection.close()
            print("[INFO] PostgreSQL connection closed")


def registration_password(update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - registration_password \ словарь - %s", user.first_name, context.bot_data)
    key = str(update.effective_user.id)  # user id
    third_stage = context.bot_data.get(key, 'Not found')  # список ник,имя,фамилия
    reply_keyboard = [['/back', '/step_back']]
    key_for_step = key + 'step'
    context.bot_data[key_for_step] = REGISTRATION_PASSWORD
    ID = update.message.chat_id  # получаем id пользователя что бы отправлять ему сообщение а не всем
    user_password = update.message.text
    cursor = connection.cursor()
    try:

        markup_key = ReplyKeyboardRemove()  # удаление клавы
        context.bot_data[key] = third_stage + [
            user_password]  # помещаем так же в словарь контекста по ключю - id usera, список,\
        # хз почему выделяется если по человечески делать то не работает
        nick_name = context.bot_data[key][0]
        user_name = context.bot_data[key][1]
        user_surname = context.bot_data[key][2]
        password_usr = context.bot_data[key][3]
        ### извлекаю все данные из таблицы и смотрю есть ли в нем такой никнейм
        cursor.execute(
            """INSERT INTO users (nick_name, user_name, user_surname, password) VALUES
                (%s, %s, %s, crypt(%s, gen_salt('bf', 8)));""",
            (nick_name, user_name, user_surname, password_usr))
        print("[INFO] Data was succefully inserted")
        ###
        context.bot_data.pop(key)
        context.bot_data.pop(key_for_step)
        context.bot.send_message(chat_id=ID,
                                 text="Вы успешно зарегистрировались, я сразу перенесу вас на вход в аккаунт\n"
                                      "Не благодорите ;}"
                                      "", reply_markup=markup_key)
        global black_list
        black_list = []
        black_list.append(key)
        return login(update, context)

        ###
    except Exception as _ex:
        print("[INFO] Error while working with PostgreSQL", _ex)
    finally:
        if connection:
            cursor.close()
            # connection.close()
            print("[INFO] PostgreSQL connection closed")


# посредник между окончанием регистрации и начлаом пользовтаельских возможностей, до входа запустить нельзя стоит защита
def after_login(update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - after_login \ словарь - %s", user.first_name, context.bot_data)
    key = str(update.effective_user.id)
    ID = update.message.chat_id
    if 'after_login' in context.bot_data[
        key]:  # context.bot_data[key] where key = str(update.effective_user.id) хранит данные о пользователи после логина его изменять нельзя
        reply_keyboard = [['/task_all', '/dictionary', '/your_dictionary', '/exit']]
        markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)

        context.bot.send_message(chat_id=ID,
                                 text="Теперь вам доступен - /help\n"
                                      "Выберите чем хотите заняться",
                                 reply_markup=markup_key)
        return timer_task(update, context)
    else:
        context.bot.send_message(chat_id=ID,
                                 text="Сначала нужно войти или зарегистрироваться")

        return back(update, context)


def build_menu(buttons, n_cols,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, [header_buttons])
    if footer_buttons:
        menu.append([footer_buttons])
    return menu


def choose_time_random_task(update, context: CallbackContext):
    query = update.callback_query
    variant = query.data
    print(query, variant)
    # `CallbackQueries` требует ответа, даже если
    # уведомление для пользователя не требуется, в противном
    #  случае у некоторых клиентов могут возникнуть проблемы.
    # смотри https://core.telegram.org/bots/api#callbackquery.
    print(query.answer())
    # редактируем сообщение, тем самым кнопки
    # в чате заменятся на этот ответ.
    global fot_time
    key = str(update.effective_user.id)
    fot_time[key] = variant
    print(fot_time[key])
    query.edit_message_text(text=f"Выбранный вариант: {variant}")


def build_menu1(buttons, n_cols,
                header_buttons=None,
                footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, [header_buttons])
    if footer_buttons:
        menu.append([footer_buttons])
    print(menu)
    return menu


def task_all(update, context: CallbackContext):
    user = update.message.from_user
    ID = update.message.chat_id
    logger.info("Пользователь %s: этап - task_all \ словарь - %s", user.first_name, context.bot_data)
    markup_key = ReplyKeyboardRemove()
    ### проверка
    try:
        key = str(
            update.effective_user.id)  # ключ во всех функция это id пользователя, по этому ключю context содержит всю информацию о пользоваиеле
    except KeyError:
        context.bot.send_message(chat_id=ID,
                                 text="Сначала нужно войти или зарегистрироваться")  # почему то не всплывапет сообщение введите пароль
        return ConversationHandler.END
    ###
    else:
        key_1 = key + ' answer'
        if 'after_login' in context.bot_data[key]:
            context.bot.send_message(chat_id=ID,
                                     text='Все доступне задания\n'
                                     , reply_markup = markup_key)
            ### buttons block - возможно если будет много кнопок некотрекная работа, асинхронная
            keyboard = [

                InlineKeyboardButton("Случайное задание", callback_data='Случайное задание'),
                InlineKeyboardButton("Задания на грамматику", callback_data='Задания на грамматику'),
                InlineKeyboardButton("Задания на предлоги", callback_data='Задания на предлоги'),
                InlineKeyboardButton("Задания на времена", callback_data='Задания на времена'),

            ]
            reply_markup = InlineKeyboardMarkup(build_menu1(keyboard, n_cols=2))
            context.bot.send_message(chat_id=ID,
                                     text="Выберите", reply_markup=reply_markup)
            return BUTTON

        else:
            context.bot.send_message(chat_id=ID,
                                     text="Сначала нужно войти или зарегистрироваться, /back", reply_markup=markup_key)
            return ConversationHandler.END


# def task_all_2(update, context: CallbackContext):
#     user = update.message.from_user
#     ID = update.message.chat_id
#     logger.info("Пользователь %s: этап - random_task \ словарь - %s", user.first_name, context.bot_data)
#     markup_key = ReplyKeyboardRemove()
#     keyboard = [
#         [
#             InlineKeyboardButton("Button 1", callback_data='pizdec'),
#             InlineKeyboardButton("Button 2", callback_data='2'),
#         ]
#     ]
#
#     reply_markup = InlineKeyboardMarkup(keyboard)
#     update.message.reply_text("Replying to text", reply_markup=reply_markup)
#     return BUTTON


def button(update: Update, context: CallbackContext):
    ID = update.effective_message.chat_id
    query = update.callback_query
    query.answer()

    # This will define which button the user tapped on (from what you assigned to "callback_data". As I assigned them "1" and "2"):
    choice = query.data
    print(choice)
    # Now u can define what choice ("callback_data") do what like this:
    if choice == 'Случайное задание':
        buttons = [[KeyboardButton('Да'), KeyboardButton('Нет')]]
        markup_key = ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)
        context.bot.send_message(chat_id=ID,
                                 text='Вы готовы приступить к выполнению задания?'
                                 , reply_markup=markup_key, )
        return RANDOM_TASK

    if choice == 'Задания на грамматику':
        buttons = [[KeyboardButton('Да'), KeyboardButton('Нет')]]
        markup_key = ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)
        context.bot.send_message(chat_id=ID,
                                 text='Вы готовы приступить к выполнению задания?'
                                 , reply_markup=markup_key, )
        return TASK_GRAMMATIKA

    if choice == 'Задания на предлоги':
        buttons = [[KeyboardButton('Да'), KeyboardButton('Нет')]]
        markup_key = ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)
        context.bot.send_message(chat_id=ID,
                                 text='Вы готовы приступить к выполнению задания?'
                                 , reply_markup=markup_key, )
        return TASK_PREPOSITIONS

    if choice == 'Задания на времена':
        buttons = [[KeyboardButton('Да'), KeyboardButton('Нет')]]
        markup_key = ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)
        context.bot.send_message(chat_id=ID,
                                 text='Вы готовы приступить к выполнению задания?'
                                 , reply_markup=markup_key, )
        return TASK_TIMES


def task_times(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - task_grammatika \ словарь - %s", user.first_name, context.bot_data)
    if 'Да' in update.message.text:
        markup_key = ReplyKeyboardRemove()
        ID = update.message.chat_id
        try:
            key = str(
                update.effective_user.id)  # ключ во всех функция это id пользователя, по этому ключю context содержит всю информацию о пользоваиеле
        except KeyError:
            context.bot.send_message(chat_id=ID,
                                     text="Сначала нужно войти или зарегистрироваться")  # почему то не всплывапет сообщение введите пароль
            return ConversationHandler.END
        else:
            key_1 = key + ' answer'  # передаем в ключ-посредник ответ что бы сверить его в след функции
            if 'after_login' in context.bot_data[key]:
                ID = update.message.chat_id
                context.bot.send_message(chat_id=ID,
                                         text='Сейчас я пришлю вам случайное задания из одного из лучших учебников!\n'
                                              'На выполнение у тебя будет одна попытка, после ответа я пришлю ваши ошибки\n'
                                              'Если вы введете слишком много или мало ответов, то попытка не засчитается\n'
                                              'Ответ вводите в одно сообщение, каждый ответ строго через запятую.')

                r_t = random.randint(1, 2)
                print(r_t)

                with connection.cursor() as cursor: # отправляю задание
                    cursor.execute(
                        """SELECT id, task_text, task_name, anwsers, task_from FROM task_times where id=(%s);""",
                        (r_t,)

                    )

                    f = (cursor.fetchall())
                    id = f[0][0]
                    task_text = f[0][1]  # задание
                    task_name = f[0][2]
                    anwsers = f[0][3]
                    task_from = f[0][4]
                    print(task_text, '/n', task_name)
                    print(anwsers, task_from)
                # if connection:
                #     # cursor.close()
                #     connection.close()
                #     print("[INFO] PostgreSQL connection closed")
                context.bot.send_message(chat_id=ID,
                                         text=task_text
                                         )
                context.bot_data[key_1] = id
                return TASK_TIMES_ANWSER

                # return RANDOM_TASK_ANSWER
            else:
                context.bot.send_message(chat_id=ID,
                                         text="Сначала нужно войти или зарегистрироваться, /back",
                                         reply_markup=markup_key)
                return ConversationHandler.END
    else:

        reply_keyboard = [['/task_all', '/dictionary', '/your_dictionary', '/exit']]
        markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text='возращаю к главному меню', reply_markup=markup_key)

        return ConversationHandler.END


def task_times_anwser(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - task_grammatika_anwser \ словарь - %s", user.first_name, context.bot_data)
    key = str(
        update.effective_user.id)  # ключ во всех функция это id пользователя, по этому ключю context содержит всю информацию о пользоваиеле
    key_1 = key + ' answer'
    user_id = context.bot_data[key][0]  # id из базы данной - user
    reply_keyboard = [['/task_all', '/dictionary', '/your_dictionary', '/exit']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    ID = update.message.chat_id  # id чата в тг
    messege_from_user = update.message.text  # сообщение от юзера
    answer = messege_from_user.split(',')  # преобразуем сообщение в список
    answer = list(filter(len, map(str.strip, answer)))  # убирает все пробелы
    answer = list(map(str.lower, answer))
    print(answer)
    if 'after_login' in context.bot_data[key]:  # проверка на регистрацию
        try:
            ## берем данные из бд
            date = datetime.date.today()  # дата выполнения задания
            task_id = context.bot_data[key_1]  # id задания
            with connection.cursor() as cursor:
                cursor.execute(
                    """SELECT id, anwsers FROM task_times WHERE id=(%s);""",
                    (task_id,)
                )
                f = (cursor.fetchall())
                r_anwsers = f[0][1]
                right_answer = (r_anwsers.split('0'))
                print(right_answer, 'right')
            right_answer.remove('\n')  # pop - not working
            right_answer = list(map(str.lower, right_answer))  # на нижний регистр
            right_answer = list(filter(len, map(str.strip, right_answer)))  # убирает все пробелы
            for i in range(len(right_answer)):
                if '/' in right_answer[i]:
                    right_answer[i] = right_answer[i].split('/')
                    right_answer[i] = list(filter(len, map(str.strip, right_answer[i])))
            print(right_answer)
            # [' step\n', ' free\n', ' order\n', [' vacancies', 'entry', 'exit\n'], [' lean out of the window', 'leave bags unattended\n'], ' other side\n', ' head\n', [' disturb', 'Please do not feed the animals\n'], ' the grass\n', [' right', 'left\n'], ' in progress\n']
            ##

            ## процесс логики программы, которая находить ошибки
            le_answer = len(right_answer)
            print(le_answer)
            result = {}  # словарь гду будут храниться ошибки
            errors = []  # список что бы записать все ошибки в бд
            result_ratio = ''  # строка по типу 4/5 - соотношение результата для записи в бд
            right_answer_number = 0
            if len(right_answer) == len(answer):  # проверка на недостаток или избыток ответов
                for i in range(len(right_answer)):
                    if right_answer[i] == answer[i] or answer[i] in right_answer[i]:
                        pass
                    else:
                        result[i + 1] = [answer[i], right_answer[i]]
                if len(result) == 0:  # если результат равен нулю соответственно ошибок нет
                    errors.append('нет ошибок')
                    result_ratio = f"{len(right_answer)}/{len(right_answer)}"
                    right_answer_number = len(right_answer)
                    context.bot.send_message(chat_id=ID,
                                             text="все правильно", reply_markup=markup_key)
                else:  # смотрим какие ошибки в каком задании
                    count = 0
                    for i in result:
                        context.bot.send_message(chat_id=ID,
                                                 text=f"в задании {i} оишбка"
                                                      f"- {result[i][0]}, правильно будет - {(', '.join(result[i][1])) if type(result[i][1]) == list else result[i][1]}")  # если строка то он тпе и выводит если список то делает из него строку, ставит запятую и потом выводит
                        errors.append(
                            f"задние {str(i)}, оишбка {str(result[i][0])}, правильно {str(result[i][1])} ||| ")
                        count += 1
                    result_ratio = f"{len(right_answer) - count}/{len(right_answer)}"
                    right_answer_number = len(right_answer) - count
                    context.bot.send_message(chat_id=ID,
                                             text=f"результат: {result_ratio}", reply_markup=markup_key)
                ### добавляю бд все данные о выполненом задании
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                                INSERT INTO task_time_result(errors, date_do_task, fk_random_task_user, number_of_tasks, number_of_right_answer, task) VALUES
                                (%s, %s, %s, %s, %s, %s);
                        """,
                        (' '.join(errors), date, int(user_id), le_answer, right_answer_number, task_id,))
                    print("[INFO] Data was succefully inserted")
                return ConversationHandler.END
            else:
                context.bot.send_message(chat_id=ID,
                                         text="слишком много или мало ответов))")
        except Exception as _ex:
            print("[INFO] Error while working with PostgreSQL", _ex)
            context.bot.send_message(chat_id=ID,
                                     text="все плохо")
        finally:
            if connection:
                cursor.close()
                # connection.close()
                print("[INFO] PostgreSQL connection closed")
    else:
        context.bot.send_message(chat_id=ID,
                                 text="cccccccc")
        return ConversationHandler.END


def task_prepositions(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - task_grammatika \ словарь - %s", user.first_name, context.bot_data)
    if 'Да' in update.message.text:
        markup_key = ReplyKeyboardRemove()
        ID = update.message.chat_id
        try:
            key = str(
                update.effective_user.id)  # ключ во всех функция это id пользователя, по этому ключю context содержит всю информацию о пользоваиеле
        except KeyError:
            context.bot.send_message(chat_id=ID,
                                     text="Сначала нужно войти или зарегистрироваться")  # почему то не всплывапет сообщение введите пароль
            return ConversationHandler.END
        else:
            key_1 = key + ' answer'  # передаем в ключ-посредник ответ что бы сверить его в след функции
            if 'after_login' in context.bot_data[key]:
                ID = update.message.chat_id
                context.bot.send_message(chat_id=ID,
                                         text='Сейчас я пришлю вам случайное задания из одного из лучших учебников!\n'
                                              'На выполнение у тебя будет одна попытка, после ответа я пришлю ваши ошибки\n'
                                              'Если вы введете слишком много или мало ответов, то попытка не засчитается\n'
                                              'Ответ вводите в одно сообщение,каждый ответ строго через запятую.', reply_markup=markup_key)

                r_t = random.randint(1, 2)
                print(r_t)

                with connection.cursor() as cursor:
                    cursor.execute(
                        """SELECT id, task_text, task_name, anwsers, task_from FROM task_prepositions where id =(%s);""",
                        (r_t,)

                    )

                    f = (cursor.fetchall())
                    id = f[0][0]
                    task_text = f[0][1]  # задание
                    task_name = f[0][2]
                    anwsers = f[0][3]
                    task_from = f[0][4]
                    print(task_text, '/n', task_name)
                    print(anwsers, task_from)
                # if connection:
                #     # cursor.close()
                #     connection.close()
                #     print("[INFO] PostgreSQL connection closed")
                context.bot.send_message(chat_id=ID,
                                         text=task_text
                                         )
                context.bot_data[key_1] = id
                return TASK_PREPOSITIONS_ANWSER

                # return RANDOM_TASK_ANSWER
            else:
                context.bot.send_message(chat_id=ID,
                                         text="Сначала нужно войти или зарегистрироваться, /back",
                                         reply_markup=markup_key)
                return ConversationHandler.END
    else:
        reply_keyboard = [['/task_all', '/dictionary', '/your_dictionary', '/exit']]
        markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text='возращаю к главному меню', reply_markup=markup_key)

        return ConversationHandler.END


def task_prepositions_anwser(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - task_grammatika_anwser \ словарь - %s", user.first_name, context.bot_data)
    key = str(
        update.effective_user.id)  # ключ во всех функция это id пользователя, по этому ключю context содержит всю информацию о пользоваиеле
    key_1 = key + ' answer'
    user_id = context.bot_data[key][0]  # id из базы данной - user
    reply_keyboard = [['/task_all', '/dictionary', '/your_dictionary', '/exit']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    ID = update.message.chat_id  # id чата в тг
    messege_from_user = update.message.text  # сообщение от юзера
    answer = messege_from_user.split(',')  # преобразуем сообщение в список
    answer = list(filter(len, map(str.strip, answer)))  # убирает все пробелы
    answer = list(map(str.lower, answer))
    if 'after_login' in context.bot_data[key]:  # проверка на регистрацию
        try:
            ## берем данные из бд
            date = datetime.date.today()  # дата выполнения задания
            task_id = context.bot_data[key_1]  # id задания
            with connection.cursor() as cursor:
                cursor.execute(
                    """SELECT id, anwsers FROM task_prepositions WHERE id=(%s);""",
                    (task_id,)
                )
                f = (cursor.fetchall())
                r_anwsers = f[0][1]
                right_answer = (r_anwsers.split('0'))
                print(right_answer, 'right')
            right_answer.remove('\n')  # pop - not working
            right_answer = list(map(str.lower, right_answer))  # на нижний регистр
            right_answer = list(filter(len, map(str.strip, right_answer)))  # убирает все пробелы
            for i in range(len(right_answer)):
                if '/' in right_answer[i]:
                    right_answer[i] = right_answer[i].split('/')
                    right_answer[i] = list(filter(len, map(str.strip, right_answer[i])))
            # [' step\n', ' free\n', ' order\n', [' vacancies', 'entry', 'exit\n'], [' lean out of the window', 'leave bags unattended\n'], ' other side\n', ' head\n', [' disturb', 'Please do not feed the animals\n'], ' the grass\n', [' right', 'left\n'], ' in progress\n']
            ##

            ## процесс логики программы, которая находить ошибки
            le_answer = len(right_answer)
            print(le_answer)
            result = {}  # словарь гду будут храниться ошибки
            errors = []  # список что бы записать все ошибки в бд
            result_ratio = ''  # строка по типу 4/5 - соотношение результата для записи в бд
            right_answer_number = 0
            if len(right_answer) == len(answer):  # проверка на недостаток или избыток ответов
                for i in range(len(right_answer)):
                    if right_answer[i] == answer[i] or answer[i] in right_answer[i]:
                        pass
                    else:
                        result[i + 1] = [answer[i], right_answer[i]]
                if len(result) == 0:  # если результат равен нулю соответственно ошибок нет
                    errors.append('нет ошибок')
                    result_ratio = f"{len(right_answer)}/{len(right_answer)}"
                    right_answer_number = len(right_answer)
                    context.bot.send_message(chat_id=ID,
                                             text="все правильно", reply_markup=markup_key)
                else:  # смотрим какие ошибки в каком задании
                    count = 0
                    for i in result:
                        context.bot.send_message(chat_id=ID,
                                                 text=f"в задании {i} оишбка"
                                                      f"- {result[i][0]}, правильно будет - {(', '.join(result[i][1])) if type(result[i][1]) == list else result[i][1]}")  # если строка то он тпе и выводит если список то делает из него строку, ставит запятую и потом выводит
                        errors.append(
                            f"задние {str(i)}, оишбка {str(result[i][0])}, правильно {str(result[i][1])} ||| ")
                        count += 1
                    result_ratio = f"{len(right_answer) - count}/{len(right_answer)}"
                    right_answer_number = len(right_answer) - count
                    context.bot.send_message(chat_id=ID,
                                             text=f"результат: {result_ratio}", reply_markup=markup_key)
                ### добавляю бд все данные о выполненом задании
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                                INSERT INTO task_prepositions_result(errors, date_do_task, fk_random_task_user, number_of_tasks, number_of_right_answer, task) VALUES
                                (%s, %s, %s, %s, %s, %s);
                        """,
                        (' '.join(errors), date, int(user_id), le_answer, right_answer_number, task_id,))
                    print("[INFO] Data was succefully inserted")
                return ConversationHandler.END
            else:
                context.bot.send_message(chat_id=ID,
                                         text="слишком много или мало ответов))")
        except Exception as _ex:
            print("[INFO] Error while working with PostgreSQL", _ex)
            context.bot.send_message(chat_id=ID,
                                     text="все плохо")
        finally:
            if connection:
                cursor.close()
                # connection.close()
                print("[INFO] PostgreSQL connection closed")
    else:
        context.bot.send_message(chat_id=ID,
                                 text="cccccccc")
        return ConversationHandler.END


def task_grammatika(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - task_grammatika \ словарь - %s", user.first_name, context.bot_data)
    if 'Да' in update.message.text:
        markup_key = ReplyKeyboardRemove()
        ID = update.message.chat_id
        try:
            key = str(
                update.effective_user.id)  # ключ во всех функция это id пользователя, по этому ключю context содержит всю информацию о пользоваиеле
        except KeyError:
            context.bot.send_message(chat_id=ID,
                                     text="Сначала нужно войти или зарегистрироваться")  # почему то не всплывапет сообщение введите пароль
            return ConversationHandler.END
        else:
            key_1 = key + ' answer'  # передаем в ключ-посредник ответ что бы сверить его в след функции
            if 'after_login' in context.bot_data[key]:
                ID = update.message.chat_id
                context.bot.send_message(chat_id=ID,
                                         text='Сейчас я пришлю вам случайное задания из одного из лучших учебников!\n'
                                              'На выполнение у тебя будет одна попытка, после ответа я пришлю ваши ошибки\n'
                                              'Если вы введете слишком много или мало ответов, то попытка не засчитается\n'
                                              'Ответ вводите в одно сообщение, каждый ответ строго через запятую', reply_markup=markup_key)
                r_t = random.randint(1,3)
                print(r_t)

                with connection.cursor() as cursor:
                    cursor.execute(
                        """SELECT id, task_text, task_name, anwsers, task_from FROM task_grammatika where id = (%s);""",
                        (r_t,)

                    )

                    f = (cursor.fetchall())
                    print(f)
                    id = f[0][0]
                    task_text = f[0][1]  # задание
                    task_name = f[0][2]
                    anwsers = f[0][3]
                    task_from = f[0][4]
                    print(task_text, '/n', task_name)
                    print(anwsers, task_from)
                # if connection:
                #     # cursor.close()
                #     connection.close()
                #     print("[INFO] PostgreSQL connection closed")
                context.bot.send_message(chat_id=ID,
                                         text=task_text
                                         )
                context.bot_data[key_1] = id
                return TASK_GRAMMATIKA_ANWSER

                # return RANDOM_TASK_ANSWER
            else:
                context.bot.send_message(chat_id=ID,
                                         text="Сначала нужно войти или зарегистрироваться, /back",
                                         reply_markup=markup_key)
                return ConversationHandler.END
    else:
        reply_keyboard = [['/task_all', '/dictionary', '/your_dictionary', '/exit']]
        markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text='возращаю к главному меню', reply_markup=markup_key)

        return ConversationHandler.END


def task_grammatika_anwser(update: Update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - task_grammatika_anwser \ словарь - %s", user.first_name, context.bot_data)
    key = str(
        update.effective_user.id)  # ключ во всех функция это id пользователя, по этому ключю context содержит всю информацию о пользоваиеле
    key_1 = key + ' answer'
    user_id = context.bot_data[key][0]  # id из базы данной - user
    reply_keyboard = [['/task_all', '/dictionary', '/your_dictionary', '/exit']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    ID = update.message.chat_id  # id чата в тг
    messege_from_user = update.message.text  # сообщение от юзера
    answer = messege_from_user.split(',')  # преобразуем сообщение в список
    answer = list(filter(len, map(str.strip, answer))) # убирает все пробелы
    answer = list(map(str.lower, answer))
    if 'after_login' in context.bot_data[key]:  # проверка на регистрацию
        try:
            ## берем данные из бд
            date = datetime.date.today()  # дата выполнения задания
            task_id = context.bot_data[key_1] # id задания
            with connection.cursor() as cursor:
                cursor.execute(
                    """SELECT id, anwsers FROM task_grammatika WHERE id=(%s);""",
                    (task_id,)
                )
                f = (cursor.fetchall())
                r_anwsers = f[0][1]
                right_answer = (r_anwsers.split('0'))
                print(right_answer, 'right')
            right_answer.remove('\n') # pop - not working
            right_answer = list(map(str.lower, right_answer)) # на нижний регистр
            right_answer = list(filter(len, map(str.strip, right_answer))) # убирает все пробелы
            for i in range(len(right_answer)):
                if '/' in right_answer[i]:
                    right_answer[i] = right_answer[i].split('/')
                    right_answer[i] = list(filter(len, map(str.strip, right_answer[i])))
            # [' step\n', ' free\n', ' order\n', [' vacancies', 'entry', 'exit\n'], [' lean out of the window', 'leave bags unattended\n'], ' other side\n', ' head\n', [' disturb', 'Please do not feed the animals\n'], ' the grass\n', [' right', 'left\n'], ' in progress\n']
            ##

            ## процесс логики программы, которая находить ошибки
            le_answer = len(right_answer)
            print(le_answer)
            result = {}  # словарь гду будут храниться ошибки
            errors = []  # список что бы записать все ошибки в бд
            result_ratio = ''  # строка по типу 4/5 - соотношение результата для записи в бд
            right_answer_number = 0
            if len(right_answer) == len(answer):  # проверка на недостаток или избыток ответов
                for i in range(len(right_answer)):
                    if right_answer[i] == answer[i] or answer[i] in right_answer[i]:
                        pass
                    else:
                        result[i + 1] = [answer[i], right_answer[i]]
                if len(result) == 0:  # если результат равен нулю соответственно ошибок нет
                    errors.append('нет ошибок')
                    result_ratio = f"{len(right_answer)}/{len(right_answer)}"
                    right_answer_number = len(right_answer)
                    context.bot.send_message(chat_id=ID,
                                             text="все правильно", reply_markup=markup_key)
                else:  # смотрим какие ошибки в каком задании
                    count = 0
                    for i in result:
                        context.bot.send_message(chat_id=ID,
                                                 text=f"в задании {i} оишбка"
                                                      f"- {result[i][0]}, правильно будет - {(', '.join(result[i][1])) if type(result[i][1]) == list else result[i][1] }") # если строка то он тпе и выводит если список то делает из него строку, ставит запятую и потом выводит
                        errors.append(
                            f"задние {str(i)}, оишбка {str(result[i][0])}, правильно {str(result[i][1])} ||| ")
                        count += 1
                    result_ratio = f"{len(right_answer) - count}/{len(right_answer)}"
                    right_answer_number = len(right_answer) - count
                    context.bot.send_message(chat_id=ID,
                                             text=f"результат: {result_ratio}", reply_markup=markup_key)
                ### добавляю бд все данные о выполненом задании
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                                INSERT INTO task_grammatika_result(errors, date_do_task, fk_random_task_user, number_of_tasks, number_of_right_answer, task) VALUES
                                (%s, %s, %s, %s, %s, %s);
                        """,
                        ( ' '.join(errors), date, int(user_id), le_answer, right_answer_number, task_id,))
                    print("[INFO] Data was succefully inserted")
                return ConversationHandler.END
            else:
                context.bot.send_message(chat_id=ID,
                                         text="слишком много или мало ответов))")
        except Exception as _ex:
            print("[INFO] Error while working with PostgreSQL", _ex)
            context.bot.send_message(chat_id=ID,
                                     text="все плохо")
        finally:
            if connection:
                cursor.close()
                # connection.close()
                print("[INFO] PostgreSQL connection closed")
    else:
        context.bot.send_message(chat_id=ID,
                                 text="cccccccc")
        return ConversationHandler.END


# # случайное задание

def random_task(update: Update, context: CallbackContext):
    if 'Да' in update.message.text:
        user = update.message.from_user
        logger.info("Пользователь %s: этап - random_task \ словарь - %s", user.first_name, context.bot_data)
        markup_key = ReplyKeyboardRemove()
        ID = update.message.chat_id
        try:
            key = str(
                update.effective_user.id)  # ключ во всех функция это id пользователя, по этому ключю context содержит всю информацию о пользоваиеле
        except KeyError:
            context.bot.send_message(chat_id=ID,
                                     text="Сначала нужно войти или зарегистрироваться")  # почему то не всплывапет сообщение введите пароль
            return ConversationHandler.END
        else:
            key_1 = key + ' answer'  # передаем в ключ-посредник ответ что бы сверить его в след функции
            if 'after_login' in context.bot_data[key]:
                ID = update.message.chat_id
                context.bot.send_message(chat_id=ID,
                                         text='Сейчас я пришлю вам случайное задания из одного из лучших учебников!\n'
                                              'На выполнение у тебя будет одна попытка, после ответа я пришлю ваши ошибки\n'
                                              'Если вы введете слишком много или мало ответов, то попытка не засчитается\n'
                                              'Ответ вводите в одно сообщение,каждый ответ строго через запятую', reply_markup=markup_key)

                with connection.cursor() as cursor:
                    cursor.execute(
                        """SELECT id, task_text, task_name, anwsers, task_from FROM task_grammatika ;""",

                    )

                    f = (cursor.fetchall())
                    id = f[0][0]
                    task_text = f[0][1]  # задание
                    task_name = f[0][2]
                    anwsers = f[0][3]
                    task_from = f[0][4]
                    print(task_text, '/n', task_name)
                    print(anwsers, task_from)
                context.bot.send_message(chat_id=ID,
                                         text=task_text
                                         )
                context.bot_data[key_1] = id
                print('-------------', context.bot_data[key_1])
                return RANDOM_TASK_ANSWER

            else:
                context.bot.send_message(chat_id=ID,
                                         text="Сначала нужно войти или зарегистрироваться, /back",
                                         reply_markup=markup_key)
                return ConversationHandler.END
    else:
        reply_keyboard = [['/task_all', '/dictionary', '/your_dictionary', '/exit']]
        markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text='возращаю к главному меню', reply_markup=markup_key)

        return ConversationHandler.END


def random_task_answer(update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - task_grammatika_anwser \ словарь - %s", user.first_name, context.bot_data)
    key = str(
        update.effective_user.id)  # ключ во всех функция это id пользователя, по этому ключю context содержит всю информацию о пользоваиеле
    key_1 = key + ' answer'
    user_id = context.bot_data[key][0]  # id из базы данной - user
    reply_keyboard = [['/task_all', '/dictionary', '/your_dictionary', '/exit']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    ID = update.message.chat_id  # id чата в тг
    messege_from_user = update.message.text  # сообщение от юзера
    answer = messege_from_user.split(',')  # преобразуем сообщение в список
    answer = list(filter(len, map(str.strip, answer)))  # убирает все пробелы
    answer = list(map(str.lower, answer))
    if 'after_login' in context.bot_data[key]:  # проверка на регистрацию
        try:
            ## берем данные из бд
            date = datetime.date.today()  # дата выполнения задания
            task_id = context.bot_data[key_1]  # id задания
            with connection.cursor() as cursor:
                cursor.execute(
                    """SELECT id, anwsers FROM task_grammatika WHERE id=(%s);""",
                    (task_id,)
                )
                f = (cursor.fetchall())
                r_anwsers = f[0][1]
                right_answer = (r_anwsers.split('0'))
                print(right_answer, 'right')
            right_answer.remove('\n')  # pop - not working
            right_answer = list(map(str.lower, right_answer))  # на нижний регистр
            right_answer = list(filter(len, map(str.strip, right_answer)))  # убирает все пробелы
            for i in range(len(right_answer)):
                if '/' in right_answer[i]:
                    right_answer[i] = right_answer[i].split('/')
                    right_answer[i] = list(filter(len, map(str.strip, right_answer[i])))
            # [' step\n', ' free\n', ' order\n', [' vacancies', 'entry', 'exit\n'], [' lean out of the window', 'leave bags unattended\n'], ' other side\n', ' head\n', [' disturb', 'Please do not feed the animals\n'], ' the grass\n', [' right', 'left\n'], ' in progress\n']
            ##

            ## процесс логики программы, которая находить ошибки
            le_answer = len(right_answer)
            print(le_answer)
            result = {}  # словарь гду будут храниться ошибки
            errors = []  # список что бы записать все ошибки в бд
            result_ratio = ''  # строка по типу 4/5 - соотношение результата для записи в бд
            right_answer_number = 0
            if len(right_answer) == len(answer):  # проверка на недостаток или избыток ответов
                for i in range(len(right_answer)):
                    if right_answer[i] == answer[i] or answer[i] in right_answer[i]:
                        pass
                    else:
                        result[i + 1] = [answer[i], right_answer[i]]
                if len(result) == 0:  # если результат равен нулю соответственно ошибок нет
                    errors.append('нет ошибок')
                    result_ratio = f"{len(right_answer)}/{len(right_answer)}"
                    right_answer_number = len(right_answer)
                    context.bot.send_message(chat_id=ID,
                                             text="все правильно", reply_markup=markup_key)
                else:  # смотрим какие ошибки в каком задании
                    count = 0
                    for i in result:
                        context.bot.send_message(chat_id=ID,
                                                 text=f"в задании {i} оишбка"
                                                      f"- {result[i][0]}, правильно будет - {(', '.join(result[i][1])) if type(result[i][1]) == list else result[i][1]}")  # если строка то он тпе и выводит если список то делает из него строку, ставит запятую и потом выводит
                        errors.append(
                            f"задние {str(i)}, оишбка {str(result[i][0])}, правильно {str(result[i][1])} ||| ")
                        count += 1
                    result_ratio = f"{len(right_answer) - count}/{len(right_answer)}"
                    right_answer_number = len(right_answer) - count
                    context.bot.send_message(chat_id=ID,
                                             text=f"результат: {result_ratio}", reply_markup=markup_key)
                print(user_id)
                print('result', result_ratio)
                print('errors', ' '.join(errors))
                print('date', date)
                print('id', int(user_id))
                ### добавляю бд все данные о выполненом задании
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                                INSERT INTO random_task_result(errors, date_do_task, fk_random_task_user, number_of_tasks, number_of_right_answer, task) VALUES
                                (%s, %s, %s, %s, %s, %s);
                        """,
                        (' '.join(errors), date, int(user_id), le_answer, right_answer_number, task_id,))
                    print("[INFO] Data was succefully inserted")
                return ConversationHandler.END
            else:
                context.bot.send_message(chat_id=ID,
                                         text="слишком много или мало ответов))")
        except Exception as _ex:
            print("[INFO] Error while working with PostgreSQL", _ex)
            context.bot.send_message(chat_id=ID,
                                     text="все плохо")
        finally:
            if connection:
                cursor.close()
                # connection.close()
                print("[INFO] PostgreSQL connection closed")
    else:
        context.bot.send_message(chat_id=ID,
                                 text="cccccccc")
        return ConversationHandler.END


def dictionary(update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - dictionary \ словарь - %s", user.first_name, context.bot_data)
    ID = update.message.chat_id
    try:
        key = str(update.effective_user.id)
    except KeyError:
        context.bot.send_message(chat_id=ID,
                                 text="Сначала нужно войти или зарегистрироваться")  # почему то не всплывапет сообщение введите пароль
        return ConversationHandler.END
    else:
        if 'after_login' in context.bot_data[key]:
            markup_key = ReplyKeyboardRemove()
            context.bot.send_message(chat_id=ID,
                                     text="введите слово и перевод, через пробел\n"
                                          "пример: Кот Cat", reply_markup=markup_key)
            return DICTIONARY_WORD
        else:
            context.bot.send_message(chat_id=ID,
                                     text="нужно пройти регистрацию")
            return ConversationHandler.END


def dictionary_word(update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - dictionary_word \ словарь - %s", user.first_name, context.bot_data)
    reply_keyboard = [['/task_all', '/dictionary', '/your_dictionary', '/exit']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    key = str(update.effective_user.id)
    ID = update.message.chat_id
    if 'after_login' in context.bot_data[key]:
        words = (
            update.message.text).split()  # сделать строгий пррием ответа, пока делит сообщение на три части разделяя пробелом(одна из частей пробел)
        if len(words) != 2:
            context.bot.send_message(chat_id=ID,
                                     text="Проверьте правильно ли вы ввели слово и перевод(формат)",
                                     reply_markup=markup_key)
        else:
            try:
                word = words[0]
                translate = words[1]
                user_id = context.bot_data[key][0]
                cursor = connection.cursor()
                cursor.execute("""
                        INSERT into  user_dictionary(word, word_translate, fk_user_dictionary_users) VALUES 
                        (%s, %s, %s);
                        """,
                               (word, translate, user_id)
                               )
                context.bot.send_message(chat_id=ID,
                                         text="Слово добалено", reply_markup=markup_key)
                return ConversationHandler.END

            ###
            except Exception as _ex:
                print("[INFO] Error while working with PostgreSQL", _ex)
            finally:
                if connection:
                    cursor.close()
                    # connection.close()
                    print("[INFO] PostgreSQL connection closed")
                ###
    else:
        context.bot.send_message(chat_id=ID,
                                 text="Нужно пройти регистрацию")
        return ConversationHandler.END


######
def your_dictionary(update, context: CallbackContext):
    user = update.message.from_user
    reply_keyboard = [['/random_task', '/dictionary', '/your_dictionary', '/exit']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    logger.info("Пользователь %s: этап - your_dictionary \ словарь - %s", user.first_name, context.bot_data)
    reply_keyboard = [['/task_all', '/dictionary', '/your_dictionary', '/exit']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    ID = update.message.chat_id
    cursor = connection.cursor()
    try:
        key = str(update.effective_user.id)
        if 'after_login' in context.bot_data[key]:
            user_id = context.bot_data[key][0]
            cursor.execute("""
            SELECT * FROM  user_dictionary WHERE fk_user_dictionary_users = (%s);
            """,
                           (user_id,)
                           )
            # в это блоке мы делаем табличку с пмощью pandas, колонки которые нам нужны превращаем в списки, делаем из них список \
            # со слов русским-английским и помещаем в таблицу с помощью какой то билблиотеки
            df = pandas.DataFrame(cursor.fetchall(),
                                  columns=['id', 'word', 'word_translate', 'fk_user_dictionary_users'])
            x = (df['word'].tolist())
            y = (df['word_translate'].tolist())
            len_l = len(x)
            dic = []
            for i in range(len_l):
                dic.append([x[i], y[i]])
            print(dic)
            table = pt.PrettyTable(['Rus', 'Eng'])
            table.align['Rus'] = 'l'
            table.align['Eng'] = 'r'

            for r, e in dic:
                table.add_row([r, e])
            table.set_style(PLAIN_COLUMNS)
            context.bot.send_message(chat_id=ID,
                                     text=f'{table}', reply_markup=markup_key)
            return ConversationHandler.END
        else:
            context.bot.send_message(chat_id=ID,
                                     text="Нужно пройти регистрацию")
            return ConversationHandler.END

    except Exception as _ex:
        print("[INFO] Error while working with PostgreSQL", _ex)
        context.bot.send_message(chat_id=ID,
                                 text="Скорее всего ваш словарь пуст, пожалуйста запишите туда сначала что нибудь. Если вы уже записывали обратитесь в поддержку.",
                                 reply_markup=markup_key)
        return ConversationHandler.END
    finally:
        if connection:
            cursor.close()
            # connection.close()
            print("[INFO] PostgreSQL connection closed")


# начало мохголомки

# удаляет работку с именем которое ему присвоено(id) current_jobs - кортеж запланированword has been addedных работ
def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


# def unset(update: Update, context: CallbackContext) -> None:
#     """Remove the job if the user changed their mind."""
#     reply_keyboard = [['/random_task', '/dictionary']]
#     markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
#     chat_id = update.message.chat_id
#     job_removed = remove_job_if_exists(str(update.effective_user.id), context)
#     text = 'Timer successfully cancelled!' if job_removed else 'You have no active timer.'
#     context.bot.send_message(chat_id=chat_id,
#                              text=text, reply_markup=markup_key)
#     return ConversationHandler.END


def timer_task(update, context: CallbackContext):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - timer_task \ словарь - %s", user.first_name, context.bot_data)
    ID = update.message.chat_id
    try:
        key = str(update.effective_user.id)
        print(key)
        # global fot_time
        # print(fot_time[key])
    except KeyError:
        context.bot.send_message(chat_id=ID,
                                 text="Сначала нужно войти или зарегистрироваться")  # почему то не всплывапет сообщение введите пароль
        return ConversationHandler.END
    else:
        if 'after_login' in context.bot_data[key]:
            key_1 = str(update.effective_user.id) + ' timer_task'
            attempt_counter_key = str(update.effective_user.id) + 'attempt'
            context.bot_data[attempt_counter_key] = 0
            context.bot_data[key_1] = ID
            context.bot.send_message(chat_id=ID,
                                     text="Обязательно суточное задание в пути\n"
                                          "Прибудет в 16:10 по московскому времени")
            context.job_queue.run_daily(time_for_task,
                                        datetime.time(hour=16, minute=10, tzinfo=pytz.timezone('Europe/Moscow')),
                                        days=(0, 1, 2, 3, 4, 5, 6), context=[ID, str(ID) + 'time'],
                                        name=str(update.effective_user.id))  # вызов функции с заданием
            # context.job_queue.run_repeating(time_for_task,interval=20,context=[ID, str(ID)+'time'], name=str(update.effective_user.id))
            # передаем в context данные необходимое той функции тк update по дефолту передать нельзя
        else:
            context.bot.send_message(chat_id=ID,
                                     text="нужно зарегистрироваться")
            return ConversationHandler.END


def time_for_task(context: CallbackContext):
    print('time_for_task')
    print(context.job.context[0])
    ID = context.job.context[0]
    job = context.job.context[1]
    with connection.cursor() as cursor:
        cursor.execute(
            """SELECT id, task_text, task_name, anwsers, task_from FROM task_grammatika ;""",

        )

        f = (cursor.fetchall())
        id = f[0][0]
        task_text = f[0][1]  # задание
        task_name = f[0][2]
        anwsers = f[0][3]
        task_from = f[0][4]
        print(task_text, '/n', task_name)
        print(anwsers, task_from)
    # if connection:
    #     # cursor.close()
    #     connection.close()
    #     print("[INFO] PostgreSQL connection closed")
    context.bot.send_message(chat_id=ID,
                             text=f'{task_text} /time_for_task_answer ....'
                             ) # отправляем задание
    context.bot_data[job] = [id, True]  # передаем функции посреднику ответ
    print(context.bot_data[job])



# обработчик ответа
def time_for_task_answer(update, context):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - time_for_task_answer \ словарь - %s", user.first_name, context.bot_data)
    key = str(update.effective_user.id)
    attempt_counter_key = str(update.effective_user.id) + 'attempt'
    key_1 = str(update.effective_user.id) + 'time'
    user_id = context.bot_data[key][0]  # id из базы данной
    reply_keyboard = [['/task_all', '/dictionary', '/your_dictionary', '/exit']]
    messege_from_user = update.message.text  # сообщение от юзера
    answer = (messege_from_user.split('/time_for_task_answer')[1]).split(',')  # преобразуем сообщение в список
    answer = list(filter(len, map(str.strip, answer)))  # убирает все пробелы
    print(answer)
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    ID = update.message.chat_id  # id чата в тг
    if 'after_login' in context.bot_data[key]:
        if True in context.bot_data[key_1]:
            try:
                task_id = context.bot_data[key_1][0]  # id задания
                # task = (context.bot_data[key_1][2])  # задание юнит
                date = datetime.date.today()  # дата выполнения задани
                with connection.cursor() as cursor:
                    cursor.execute(
                        """SELECT id, anwsers FROM task_grammatika WHERE id=(%s);""",
                        (task_id,)
                    )
                    f = (cursor.fetchall())
                    r_anwsers = f[0][1]
                    right_answer = (r_anwsers.split('0'))
                    print(right_answer, 'right')  # правильный ответ
                right_answer.remove('\n')  # pop - not working
                right_answer = list(map(str.lower, right_answer))  # на нижний регистр
                right_answer = list(filter(len, map(str.strip, right_answer)))  # убирает все пробелы
                le_answer = len(right_answer)
                for i in range(len(right_answer)):
                    if '/' in right_answer[i]:
                        right_answer[i] = right_answer[i].split('/')
                        right_answer[i] = list(filter(len, map(str.strip, right_answer[i])))
                print(right_answer)
                # [' step\n', ' free\n', ' order\n', [' vacancies', 'entry', 'exit\n'], [' lean out of the window', 'leave bags unattended\n'], ' other side\n', ' head\n', [' disturb', 'Please do not feed the animals\n'], ' the grass\n', [' right', 'left\n'], ' in progress\n']
                ##
                context.bot_data[attempt_counter_key] += 1  # попытки выполнения задания
                result = {}  # словарь гду будут храниться ошибки
                errors = []  # список что бы записать все ошибки в бд
                result_ratio = ''  # строка по типу 4/5 - соотношение результата для записи в бд
                right_answer_number = 0
                all_right = True  # будем передаывать для понимания правиильно ои выполнены все задания
                if len(right_answer) == len(answer):  # проверка на недостаток или избыток ответов
                    for i in range(len(right_answer)):
                        if right_answer[i] == answer[i] or answer[i] in right_answer[i]:
                            pass
                        else:
                            result[i + 1] = [answer[i], right_answer[i]]  # добавляем элемент словарю тк отчет начинается с 0 а наши здания с 1
                    if len(result) == 0:  # если результат равен нулю соответственно ошибок нет
                        all_right = True
                        errors.append('нет ошибок')
                        result_ratio = f"{len(right_answer)}/{len(right_answer)}"
                        right_answer_number = len(right_answer)
                        context.bot.send_message(chat_id=ID,
                                                 text="все правильно", reply_markup=markup_key)
                    else:  # смотрим какие ошибки в каком задании
                        all_right = False
                        context.bot.send_message(chat_id=ID,
                                                 text=f"осталось попыток {context.bot_data[attempt_counter_key]}/3")
                        if context.bot_data[attempt_counter_key] == 3:
                            count = 0
                            for i in result:
                                context.bot.send_message(chat_id=ID,
                                                         text=f"в задании {i} оишбка"
                                                              f"- {result[i][0]}, правильно будет - {(', '.join(result[i][1])) if type(result[i][1]) == list else result[i][1]}")  # если строка то он тпе и выводит если список то делает из него строку, ставит запятую и потом выводит
                                errors.append(
                                    f"задние {str(i)}, оишбка {str(result[i][0])}, правильно {str(result[i][1])} ||| ")
                                count += 1
                            result_ratio = f"{len(right_answer) - count}/{len(right_answer)}"
                            right_answer_number = len(right_answer) - count
                            context.bot.send_message(chat_id=ID,
                                                     text=f"результат: {result_ratio}", reply_markup=markup_key)
                        ### добавляю бд все данные о выполненом задании
                    if context.bot_data[attempt_counter_key] >= 3 or all_right:
                        # print(right_answer_number, len_answer)
                        # print('result', result_ratio)
                        # print('task', task)
                        # print('errors', ' '.join(errors))
                        # print('attempts:', context.bot_data[attempt_counter_key])
                        # print('date', date)
                        # print('id', int(user_id))
                        # print(user_id)
                        ### добавляю бд все данные о выполненом задании
                        with connection.cursor() as cursor:
                            cursor.execute(
                                """
                                        INSERT INTO time_random_task_result(errors,attemps, date_do_task, fk_random_task_user, number_of_tasks, number_of_right_answer, task) VALUES
                                        (%s, %s, %s, %s, %s, %s, %s);
                                """,
                                (' '.join(errors), context.bot_data[attempt_counter_key], date, int(user_id), le_answer, right_answer_number, task_id,))
                            print("[INFO] Data was succefully inserted")
                        context.bot_data[attempt_counter_key] = 0
                        context.bot_data[key_1][1] = False
                        return ConversationHandler.END
                else:
                    context.bot.send_message(chat_id=ID,
                                             text="слишком много или мало ответов))", reply_markup=markup_key)
                    if context.bot_data[attempt_counter_key] >= 3:
                        context.bot.send_message(chat_id=ID,
                                                 text="вы исчерпали 3 попытки переизбытком ответов")
                        with connection.cursor() as cursor:
                            cursor.execute(
                                """
                                        INSERT INTO time_random_task_result(errors, attemps, date_do_task, fk_random_task_user, number_of_tasks, number_of_right_answer, task) VALUES
                                        (%s, %s, %s, %s, %s, %s, %s);
                                """,
                                (' '.join(errors), context.bot_data[attempt_counter_key], date, int(user_id), le_answer, right_answer_number, task_id,))
                            print("[INFO] Data was succefully inserted")
                        context.bot_data[attempt_counter_key] = 0
                        context.bot_data[key_1][1] = False
                        return ConversationHandler.END

            except Exception as _ex:
                print("[INFO] Error while working with time", _ex)
                context.bot.send_message(chat_id=ID,
                                         text="все плохо")
            finally:
                if connection:
                    cursor.close()
                    # connection.close()
                    print("[INFO] PostgreSQL connection closed")
        # обработчик - если присылают ответ с упоминанием функции пока задание не было отправлено
        else:
            context.bot.send_message(chat_id=ID,
                                     text="Задание еще не было отправлено")
            return ConversationHandler.END
    # обработчик - не зарегистрирован
    else:
        context.bot.send_message(chat_id=ID,
                                 text="Надо зарегистрироваться")
        return ConversationHandler.END


def exit(update, context):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - exit \ словарь - %s", user.first_name, context.bot_data)
    ID = update.message.chat_id
    try:
        key = str(update.effective_user.id)
        chat_id = update.message.chat_id
        job_removed = remove_job_if_exists(str(update.effective_user.id), context)
        text = 'Timer successfully cancelled!' if job_removed else 'You have no active timer.'
        global black_list
        ind = black_list.index(key)
        black_list.pop(ind)
        del context.bot_data[key + ' timer_task']
        del context.bot_data[key]
        try:
            del context.bot_data[key + 'attempt']
        except Exception as _ex:
            print('here')
            pass

        try:
            del context.bot_data[key + 'step']
        except Exception as _ex:
            print('here')
            pass

        try:
            del context.bot_data[key + ' answer']
        except Exception as _ex:
            print('here')
            pass
        # context.bot_data[key+' timer_task'].clear()
        # context.bot_data[key].clear()
        logger.info("Пользователь %s: этап - exit \ словарь - %s", user.first_name, context.bot_data)
        context.bot.send_message(chat_id=ID,
                                 text="Вы успешно вышли из аккаунта, надеюсь еще увидемся -)\n"
                                      "Если хотите снова войти нажмите сюда - /back")
        return ConversationHandler.END
    except Exception as _ex:
        print("[INFO] Error while working with PostgreSQL", _ex)
        context.bot.send_message(chat_id=ID,
                                 text="Нужно пройти регистрацию")
        return ConversationHandler.END


def help(update, context):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - help \ словарь - %s", user.first_name, context.bot_data)
    ID = update.message.chat_id
    reply_keyboard = [['/random_task', '/dictionary', '/your_dictionary', '/exit']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    context.bot.send_message(chat_id=ID,
                             text="/task_all - все задания, /exit - выход\n"
                                 , reply_markup=markup_key)


def delete(update, context):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - delete \ словарь - %s", user.first_name, context.bot_data)
    ID = update.message.chat_id
    try:
        reply_keyboard = [['/Yes', '/No']]
        markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        key = str(update.effective_user.id)
        if 'after_login' in context.bot_data[key]:
            context.bot.send_message(chat_id=ID,
                                     text="Вы точно хотите удалить аккаунт?", reply_markup=markup_key)
            context.bot_data[key + 'delete'] = True
        else:
            context.bot.send_message(chat_id=ID,
                                     text="Войдите в аккаунт, чтобы удалить его")
            return ConversationHandler.END
    except Exception as _ex:
        context.bot.send_message(chat_id=ID,
                                 text="Войдите в аккаунт, чтобы удалить его")
        return ConversationHandler.END


def delete_Yes(update, context):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - delete_Yes \ словарь - %s", user.first_name, context.bot_data)
    ID = update.message.chat_id
    try:
        key = str(update.effective_user.id)
        if context.bot_data[key + 'delete']:

            context.bot.send_message(chat_id=ID,
                                     text="Если хотите снова войти нажмите сюда - /back")
            return ConversationHandler.END
        else:
            context.bot.send_message(chat_id=ID,
                                     text="Как ты умудрился сюда попасть?")
            return ConversationHandler.END
    except Exception as _ex:
        context.bot.send_message(chat_id=ID,
                                 text="Войдите в аккаунт, чтобы удалить его")
        return ConversationHandler.END


def delete_No(update, context):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - delete_No \ словарь - %s", user.first_name, context.bot_data)
    reply_keyboard = [['/random_task', '/dictionary', '/your_dictionary', '/exit']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    ID = update.message.chat_id
    try:
        key = str(update.effective_user.id)
        if context.bot_data[key + 'delete']:
            context.bot.send_message(chat_id=ID,
                                     text="Тогда посмотри чем ты можешь заняться", reply_markup=markup_key)
        else:
            context.bot.send_message(chat_id=ID,
                                     text="Как ты умудрился сюда попасть?")
            return ConversationHandler.END
    except Exception as _ex:
        context.bot.send_message(chat_id=ID,
                                 text="Войдите в аккаунт, чтобы удалить его")
        return ConversationHandler.END


# TODO: почитать еще про хэш паролей и посмотреть как их могу узнавать я например для восстановления, \
#  так же если это не возможно записывать паролли и данные юзера в какой нибудь файл пока локальный


### error обработчик каких то ошибок как я понял свзанных с смим телеграмом или внешними показателяит не свазаными с программой по типу ошибки отпраки сообщения из за интернета
# это общая функция обработчика ошибок.
# Если нужна дополнительная информация о конкретном типе сообщения,
# добавьте ее в полезную нагрузку в соответствующем предложении `if ...`
def error(update, context):
    user = update.message.from_user
    logger.info("Пользователь %s: этап - error \ словарь - %s", user.first_name, context.bot_data)
    # добавьте все идентификаторы разработчиков в этот список.
    # Можно добавить идентификаторы каналов или групп.
    devs = [713119906]
    # Уведомление пользователя об этой проблеме.
    # Уведомления будут работать, только если сообщение НЕ является
    # обратным вызовом, встроенным запросом или обновлением опроса.
    # В случае, если это необходимо, то имейте в виду, что отправка
    # сообщения может потерпеть неудачу
    if update.effective_message:
        text = "К сожалению произошла ошибка в момент обработки сообщения. " \
               "Мы уже работаем над этой проблемой."
        update.effective_message.reply_text(text)
    # Трассировка создается из `sys.exc_info`, которая возвращается в
    # как третье значение возвращаемого кортежа. Затем используется
    # `traceback.format_tb`, для получения `traceback` в виде строки.
    trace = "".join(traceback.format_tb(sys.exc_info()[2]))
    # попробуем получить как можно больше информации из обновления telegram
    payload = []
    # обычно всегда есть пользователь. Если нет, то это
    # либо канал, либо обновление опроса.
    if update.effective_user:
        bad_user = mention_html(update.effective_user.id, update.effective_user.first_name)
        payload.append(f' с пользователем {bad_user}')
    # есть ситуаций, когда что то с чатом
    if update.effective_chat:
        payload.append(f' внутри чата <i>{update.effective_chat.title}</i>')
        if update.effective_chat.username:
            payload.append(f' (@{update.effective_chat.username})')
    # полезная нагрузка - опрос
    if update.poll:
        payload.append(f' с id опроса {update.poll.id}.')
    # Поместим это в 'хорошо' отформатированный текст
    text = f"Ошибка <code>{context.error}</code> случилась{''.join(payload)}. " \
           f"Полная трассировка:\n\n<code>{trace}</code>"
    # и отправляем все разработчикам
    for dev_id in devs:
        context.bot.send_message(dev_id, text, parse_mode=ParseMode.HTML)
    # Необходимо снова вызывать ошибку, для того, чтобы модуль `logger` ее записал.
    # Если вы не используете этот модуль, то самое время задуматься.
    raise


###

if __name__ == '__main__':
    # Создаем Updater и передаем ему токен вашего бота.
    updater = Updater("1533304329:AAHVhvmtXETWT4eDJrjzmbMn7Ac1XScSbwM")
    # получаем диспетчера для регистрации обработчиков
    dispatcher = updater.dispatcher

    # Определяем обработчик разговоров `ConversationHandler`
    # с состояниями GENDER, PHOTO, LOCATION и BIO
    dispatcher.add_handler(CommandHandler("start", start, run_async=True))
    dispatcher.add_handler(CommandHandler("time_for_task_answer", time_for_task_answer, run_async=True))
    dispatcher.add_handler(CommandHandler('exit', exit, run_async=True))
    dispatcher.add_handler(CommandHandler('help', help, run_async=True))
    dispatcher.add_handler(CommandHandler('Yes', delete_Yes, run_async=True))
    dispatcher.add_handler(CommandHandler('No', delete_No, run_async=True))
    dispatcher.add_handler(CommandHandler('information_of_all_student', information_of_all_student, run_async=True))
    updater.dispatcher.add_handler(CallbackQueryHandler(choose_time_random_task))
    # dispatcher.add_handler(CommandHandler('student_achivment', student_achivment, run_async=True))
    dispatcher.add_handler(CommandHandler('exit_admin', exit_admin, run_async=True))
    # dispatcher.add_handler(CommandHandler('delete', delete, run_async=True))
    # dispatcher.add_handler(CommandHandler("back", back))
    # dispatcher.add_handler(CommandHandler("login", login))
    conv_handler = ConversationHandler(  # здесь строится логика разговора
        # точка входа в разговор
        entry_points=[CommandHandler('registration', registration, run_async=True),
                      CommandHandler("login", login, run_async=True)],
        # MessageHandler(Filters.text & Filters.regex & (~ Filters.command)
        # этапы разговора, каждый со своим списком обработчиков сообщений
        states={
            REGISTRATION_FIRST: [
                MessageHandler(Filters.text & (~ Filters.command), registration_first, run_async=True)],
            REGISTRATION_NICK_NAME: [
                MessageHandler(Filters.text & (~ Filters.command), registration_nick_name, run_async=True)],
            REGISTRATION_NAME: [MessageHandler(Filters.text & (~ Filters.command), registration_name, run_async=True)],
            REGISTRATION_SURNAME: [
                MessageHandler(Filters.text & (~ Filters.command), registration_surname, run_async=True)],
            REGISTRATION_PASSWORD: [
                MessageHandler(Filters.text & (~ Filters.command), registration_password, run_async=True)],
            LOGIN: [MessageHandler(Filters.text & (~ Filters.command), login, run_async=True)],
            LOGIN_DATA: [MessageHandler(Filters.text & (~ Filters.command), login_data, run_async=True)],
            # LOGIN_PASSWORD: [MessageHandler(Filters.text & (~ Filters.command), login_password,run_async=True)],
            # AFTER_LOGIN: [MessageHandler(Filters.text & (~ Filters.command), after_login)]

        },
        # точка выхода из разговора
        fallbacks=[CommandHandler('back', back, run_async=True),
                   CommandHandler('start', start, run_async=True),
                   CommandHandler('step_back', step_back, run_async=True),
                   CommandHandler('delete', delete, run_async=True)]
    )

    conv_handler_2 = ConversationHandler(
        entry_points=[
            # CommandHandler('random_task', random_task, run_async=True),
            CommandHandler('dictionary', dictionary, run_async=True),
            CommandHandler('your_dictionary', your_dictionary, run_async=True),
            CommandHandler('task_all', task_all, run_async=True)
        ],

        states={
            RANDOM_TASK: [MessageHandler(Filters.text & (~ Filters.command), random_task, run_async=True)],
            RANDOM_TASK_ANSWER: [
                MessageHandler(Filters.text & (~ Filters.command), random_task_answer, run_async=True)],
            DICTIONARY_WORD: [MessageHandler(Filters.text & (~ Filters.command), dictionary_word, run_async=True)],
            # TASK_ALL_2: [MessageHandler(Filters.text & (~ Filters.command), task_all_2, run_async=True)],
            BUTTON: [CallbackQueryHandler(button)],
            TASK_GRAMMATIKA: [MessageHandler(Filters.text & (~ Filters.command), task_grammatika, run_async=True)],
            TASK_GRAMMATIKA_ANWSER: [
                MessageHandler(Filters.text & (~ Filters.command), task_grammatika_anwser, run_async=True)],
            TASK_PREPOSITIONS: [
                MessageHandler(Filters.text & (~ Filters.command), task_prepositions, run_async=True)],
            TASK_PREPOSITIONS_ANWSER: [
                MessageHandler(Filters.text & (~ Filters.command), task_prepositions_anwser, run_async=True)],
            TASK_TIMES: [
                MessageHandler(Filters.text & (~ Filters.command), task_times, run_async=True)],
            TASK_TIMES_ANWSER: [
                MessageHandler(Filters.text & (~ Filters.command), task_times_anwser, run_async=True)],

        },
        fallbacks=[]

    )

    conv_handler_admin = ConversationHandler(
        entry_points=[CommandHandler('Administrator', administrator, run_async=True)
                      ],

        states={
            ADMINISTRATOR_FIRST: [
                MessageHandler(Filters.text & (~ Filters.command), administrator_first, run_async=True)]

        },
        fallbacks=[CommandHandler('back', back, run_async=True),
                   CommandHandler('Administrator_main', administrator_main, run_async=True),
                   ]

    )
    conv_handler_admin_main = ConversationHandler(
        entry_points=[CommandHandler('student_achivment', student_achivment, run_async=True),
                      CommandHandler('student_statistic', student_statistic, run_async=True)],

        states={
            STUDENT_ACHIVMENT_SEOCND: [
                MessageHandler(Filters.text & (~ Filters.command), student_achivment_second, run_async=True)],
            STUDENT_STATISTIC_2: [
                MessageHandler(Filters.text & (~ Filters.command), student_statistic_2, run_async=True)],
            BUTTON_FOR_ADMIN_RESULT: [CallbackQueryHandler(button_for_admin_result, run_async=True)],
            STUDENT_ACHIVMENT_GRAMMA_TASK: [MessageHandler(Filters.text & (~ Filters.command), student_achivment_gramma_task, run_async=True)],
            STUDENT_ACHIVMENT_PREPOSITIONS_TASK: [MessageHandler(Filters.text & (~ Filters.command), student_achivment_prepositions_task, run_async=True)],
            STUDENT_ACHIVMENT_TIME_TASK: [MessageHandler(Filters.text & (~ Filters.command), student_achivment_time_task, run_async=True)],
            STUDENT_ACHIVMENT_REGULAR_TASK: [MessageHandler(Filters.text & (~ Filters.command), student_achivment_regular_task, run_async=True)],

        },
        fallbacks=[]

    )

    #  run_async=True
    # Добавляем обработчик разговоров `conv_handler`
    dispatcher.add_handler(conv_handler, 1)
    dispatcher.add_handler(conv_handler_2, 2)
    dispatcher.add_handler(conv_handler_admin)
    dispatcher.add_handler(conv_handler_admin_main, 3)

    # Запуск бота
    updater.start_polling()
    updater.idle()
