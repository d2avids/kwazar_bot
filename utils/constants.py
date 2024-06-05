import os

from telegram import KeyboardButton

# Buttons
USER_BUTTONS = [
    [KeyboardButton('О проекте')],
    [KeyboardButton('Инструкция бота')],
    [KeyboardButton('Регистрация')],
    [KeyboardButton('Дать ответ на индивидуальное задание')]
]
CURATOR_BUTTONS = [
    [KeyboardButton('Проверка домашнего задания')],
    [KeyboardButton('Новое задание')],
]
ADD_GROUP_TASK_BUTTON = 'Создать новое групповое задание'
ADD_INDIVIDUAL_TASK_BUTTON = 'Создать новое индивидуальное задание'
TASK_TYPES_BUTTONS = [
    [KeyboardButton(ADD_GROUP_TASK_BUTTON)],
    [KeyboardButton(ADD_INDIVIDUAL_TASK_BUTTON)]
]

# General
CANCEL_ACTION = 'Отменить'
CANCEL_BUTTON = [[KeyboardButton(CANCEL_ACTION)]]
ADMIN_TELEGRAM_ID = os.getenv('ADMIN_TELEGRAM_ID')
NEW_USER_NOTIFICATION = (
    'У нас новый зарегистрированный пользователь! Чтобы верифицировать или отклонить пользователей, '
    'используйте команду /verify.'
)

START_MESSAGE = (
    'Привет! Я - твой проводник в увлекательный мир КВАЗАР! '
    'Чем я могу тебе помочь?'
)
INSTRUCTIONS_MESSAGE = (
    'Инструкция:\n\n'
    '<b>1. Регистрация</b>\n'
    '1.1. Зайти в чат-бот.\n'
    '1.2. Прописать команду “/start”.\n'
    '1.3. В появившихся после приветственного сообщения бота кнопках нажать на кнопку варианта ”Регистрация”.\n'
    '1.4. В появившемся окне ввести свое имя, фамилию, номер школы, номер класса '
    'и отправить введенные данные, нажав н а кнопку “Отправить”.\n\n'
    '<b>2. Добавление чат-бота в канал Telegram</b>\n'
    '2.1. После прохождения регистрации, зайти в канал в Telegram, в которую Вы хотели бы добавить бота.\n'
    '2.2. Нажать на строку с названием канала, расположенную в верхней части экрана, чтобы зайти в настройки канала.\n'
    '2.3. В разделе “Участники”  нажать на кнопку “Добавить участников”.\n'
    '2.4. В появившемся списке профилей выбрать “Чат-бот КВАЗАР”.\n'
    '2.5. В настройках группы в списке участников группы найти чат-бота КВАЗАР. '
    'Нажать на него и выбрать в появившемся окне вариант “Назначить администратором”.\n\n'
    '<b>3. Отправка ответа на индивидуальное задание</b>\n'
    '3.1. Войти в чат-бот.\n'
    '3.2. Прописать команду “/start”.\n'
    '3.3. Среди появившихся кнопок нажать на кнопку ”Дать ответ на индивидуальное задание”.\n'
    '3.4. Написать в виде текста или ссылки на файл в облаке '
    'текст ответа на задание и нажать на кнопку “Отправить”.\n\n'
    '<b>4. Отправка ответа на групповое задание</b>\n'
    '4.1. Войти в личный канал, в который уже добавлен чат-бот (см. пункт 2).\n'
    '4.2. Прописать команду “/give_answer”.\n'
    '4.3. Написать в виде текста или ссылки на файл в облаке текст ответа на задание и нажать на кнопку “Отправить”.'
)
ABOUT_PROJECT_MESSAGE = (
    'Проект “КВАЗАР” направлен на помощь 9-классникам в подготовке к ОГЭ '
    'через увлекательный игровой мир и интересных персонажей для ролевой интеллектуальной '
    'игры в жанре "эволюция", повышая их мотивацию и результаты обучения.\n\n'

    'Игра и её мир способствуют созданию комфортного и дружелюбного сообщества участников, '
    'а также предоставляют возможность решать задания, разработанные авторами проекта. '
    'Результаты игроков формируются в рейтинги, что делает процесс еще более увлекательным. '
    'Мы стремимся к тому, чтобы каждый участник проекта "КВАЗАР" не только успешно подготовился '
    'к ОГЭ, но и обрел новых друзей, развил свои интеллектуальные способности, а также научился '
    'работать в команде и принимать решения.\n\n'

    'Наша цель - создать стимулирующую и вдохновляющую среду, где каждый участник может '
    'раскрыть свой потенциал и достичь высоких результатов. Погрузись в захватывающий мир '
    'КВАЗАР и начни свое увлекательное путешествие к знаниям и успеху!'
)

# Registration
SURNAME, NAME, PATRONYMIC, SCHOOL_NAME, CLASS_NUMBER, CLASS_SYMBOL = range(6)
FIO_VALIDATION_MESSAGE = (
    '{key_repr} должно быть не более {symbols_limit} символов. '
    'Пожалуйста, введите снова'
)
SCHOOL_NAME_VALIDATION_MESSAGE = (
    'Поле "название школы" не должно содержать {symbols_limit} символов. '
    'Пожалуйста, введите снова'
)
CLASS_NUMBER_VALIDATION_MESSAGE = (
    f'Поле "номер класса" должно быть заполнено числом от 1 до 11. Пожалуйста, введите снова'
)
CLASS_SYMBOL_VALIDATION_MESSAGE = (
    f'Поле "буква класса" должно быть заполнено единственной кириллической буквой. Пожалуйста, введите снова'
)

REGISTRATION_FINISHED_MESSAGE = (
    'Ваши данные были переданы администратору для подтверждения их корректности. '
    'Если ваша личность будет подтверждена, вы будете зарегистрированы.'
)
REGISTRATION_CANCELED_MESSAGE = 'Регистрация отменена'

REGISTRATION_MESSAGE_SURNAME = (
    'Введите фамилию'
)
REGISTRATION_MESSAGE_NAME = (
    'Введите имя'
)
REGISTRATION_MESSAGE_PATRONYMIC = (
    'Введите отчество (если отчества нет, укажите "нет")'
)
REGISTRATION_MESSAGE_SCHOOL_NAME = (
    'Введите название и номер школы'
)
REGISTRATION_MESSAGE_CLASS_NUMBER = (
    'Введите номер класса (без буквы)'
)
REGISTRATION_MESSAGE_CLASS_SYMBOL = (
    'Введите букву класса'
)
EXCEEDED_REGISTRATION_LIMIT_MESSAGE = (
    'Превышен лимит попыток прохождения регистрации'
)

# Team Registration
TEAM_NAME, TEAM_SCHOOL_NAME, TEAM_CLASS_NUMBER, TEAM_CLASS_SYMBOL, TEAM_CONFIRMATION = range(5)
CONFIRMATION_BUTTONS = [
    [KeyboardButton('Да')],
    [KeyboardButton('Нет')]
]
MSG_GROUP_CHAT_ONLY = 'Эту команду можно использовать только в групповом чате.'
MSG_USER_NOT_FOUND = 'Пользователь не найден. Пожалуйста, зарегистрируйтесь сначала.'
MSG_USER_NOT_VERIFIED = 'Вы не верифицированы для регистрации команды.'
MSG_ENTER_TEAM_NAME = 'Введите название команды:'
MSG_TEAM_NAME_TOO_LONG = 'Название команды слишком длинное. Максимальная длина - {team_name_limit} символов.'
MSG_ENTER_SCHOOL_NAME = 'Введите название школы:'
MSG_SCHOOL_NAME_TOO_LONG = 'Название школы слишком длинное. Максимальная длина - {school_name_limit} символов.'
MSG_ENTER_CLASS_NUMBER = 'Введите номер класса:'
MSG_INVALID_CLASS_NUMBER = 'Неверный номер класса. Введите число от 1 до 11.'
MSG_ENTER_CLASS_SYMBOL = 'Введите символ класса:'
MSG_INVALID_CLASS_SYMBOL = 'Неверный символ класса. Введите одну букву.'
MSG_CONFIRM_TEAM_REGISTRATION = (
    'Название команды: {team_name}\n'
    'Школа: {school_name}\n'
    'Класс: {class_number}{class_symbol}\n'
    'Подтвердите регистрацию команды? (да/нет)'
)
MSG_CHAT_ALREADY_REGISTERED = (
    'Данный чат уже зарегистрирован под названием {team_name}, '
    'для школы {school_name}, класс {class_number}{class_symbol}.'
)
MSG_TEAM_REGISTERED_SUCCESS = 'Команда успешно зарегистрирована.'
MSG_TEAM_REGISTRATION_CANCELLED = 'Регистрация команды отменена.'
MSG_PROCESS_CANCELLED = 'Процесс регистрации команды отменен.'

# Verification
VERIFICATION_START, VERIFICATION_PROCESS = range(2)
VERIFICATION_ACCEPT_COMMAND = 'Принять'
VERIFICATION_REJECT_COMMAND = 'Отклонить'
VERIFICATION_MESSAGE = (
    f'Для верификации или отклонения запросов пользователей, используйте команду '
    f'"{VERIFICATION_ACCEPT_COMMAND}" или "{VERIFICATION_REJECT_COMMAND}". '
    'После указания команды, укажите через пробел ID пользователей, которых хотите верифицировать или отклонить. '
    'Пример: "Принять 1, 2, 3"'
)

# Search user
SEARCH_USER = 0
REQUEST_LAST_NAME = (
    'Введите фамилию пользователя, чтобы найти его в базе данных '
)

# Add tutor
ADD_TUTOR = 0
ASK_ID_TUTOR_TO_ADD = (
    'Введите ID пользователя, которого хотите назначить куратором. '
    'Для поиска ID пользователя по фамилии нажмите кнопку "Отменить", чтобы прервать текущий контекст '
    'и воспользуйтесь командой /search_user'
)
ADD_TUTOR_SUCCESS = 'Пользователю переданы права куратора'

# Add task
TASK_TYPE, TASK_TEXT, TASK_DEADLINE, SENDING_TASK_TIME, GETTING_ANSWERS_TIME = range(5)
INDIVIDUAL_TYPE, GROUP_TYPE = 'individual', 'group'  # Task types
ADD_TASK_TYPE_MESSAGE = 'Выберите тип задания'
ADD_TASK_TEXT_MESSAGE = 'Введите текст задания'
TASK_ALREADY_EXISTS = (
    'Дедлайн ранее выложенного задания еще не наступил. Следующее задание может '
    'быть выложено только после завершения существующего задания командой /finish_test.'
)
ADD_DEADLINE_MESSAGE = 'Введите дедлайн сдачи задания в формате день.месяц.год часы:минуты'
ADD_SENDING_TASK_TIME_MESSAGE = 'Укажите время отправки нового задания ученикам в формате день.месяц.год часы:минуты'
ADD_GETTING_ANSWERS_TIME_MESSAGE = (
    'Укажите время, с которого начинают приниматься ответы в формате день.месяц.год часы:минуты'
)
INVALID_DATE_MESSAGE = (
    'Некорректный формат даты. Пожалуйста, введите дату в формате "дд.мм.гггг чч:мм" или нажмите "Отменить".'
)
ADD_TASK_CANCEL_MESSAGE = 'Создание задания отменено.'
ADD_TASK_SUCCESS_MESSAGE = (
    'Задание сформировано и будет опубликовано в {date_time}'
)

# Finish task
TASK_FINISHED_USERS_MESSAGE = 'Срок для выполнения задания подошел к концу'
TASK_FINISHED_ADMIN_MESSAGE = 'Прохождение задания завершено'

# Add task answer
TASK_ANSWER_TEXT = range(1)

# Add team task answer
TEAM_TASK_ANSWER_TEXT = range(1)

# Feedback
FEEDBACK_TYPE, CHOOSE_FEEDBACK, GIVE_FEEDBACK, NEXT_ACTION = range(4)
ALLOWED_FEEDBACK = ('5', '4', '3', '2')
CHOOSE_TASK_TYPE_MESSAGE = 'Выберите, какие задания вы хотите оценить: групповые или индивидуальные'
INDIVIDUAL_ANSWER = 'Индивидуальные'
GROUP_ANSWER = 'Групповые'
ANSWER_TYPES_BUTTONS = [
    [KeyboardButton(INDIVIDUAL_ANSWER)],
    [KeyboardButton(GROUP_ANSWER)],
    [KeyboardButton(CANCEL_ACTION)]
]
CHOOSE_SCHOOL_NUMBER_MESSAGE = 'Напишите номер школы'
CHOOSE_CLASS_NUMBER_MESSAGE = 'Напишите номер класса'
NO_ANSWERS_TO_ESTIMATE = 'Нет неоцененных {type} заданий.'
ESTIMATED_ALL_ANSWERS_MESSAGE = 'Все задания оценены.'
STOPPED_ESTIMATING = 'Сессия оценивания завершена.'
CHOOSE_ACTION_MESSAGE = 'Выберите действие:'
INCORRECT_ACTION_CHOSEN = 'Пожалуйста, выберите "{next_answer}" или "{stop}".'
NOT_ALLOWED_FEEDBACK_MESSAGE = 'Пожалуйста, выберите оценку из предложенных вариантов ({allowed_feedback}).'
USER_FEEDBACK_NOTIFICATION_MESSAGE = 'Ваш ответ на {task_type} задание оценен.'

# Reports
REPORTS_PATH = 'tmp'

# Individual Report
START_DATE, END_DATE = range(2)


# Permissions
ADMIN_ACCESS_FAILURE = 'Доступ к команде имеет только администратор'
NOT_CURATOR_ATTEMPT = 'Только куратор имеет доступ к этой команде'
