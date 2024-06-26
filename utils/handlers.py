import datetime
import logging

from aiogram import Router
from aiogram.enums.chat_type import ChatType
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, \
    InlineKeyboardMarkup

from bot.bot_instance import bot
from utils.asana_functions import *
from utils.config import *
from utils.help_command import process_help_command
from utils.parse_message import parse_message_complete
from utils.refresh_token_wrap import refresh_token
from utils.settings_decorator import check_settings
from utils.states.authorization import Authorization
from utils.states.default_settings import DefaultSettings
from utils.states.default_settings_private import DefaultSettingsPrivate
from utils.states.report_task import ReportTask
from utils.token_encryption import *

router = Router()


def is_private(message: Message):
    if message.chat.type != ChatType.PRIVATE:
        message.answer("Ця команда доступна лише в приватних повідомленнях")
    return message.chat.type == ChatType.PRIVATE


@router.message(CommandStart(), is_private)
async def start(message: Message, state: FSMContext) -> None:
    user = get_user(message.from_user.id)
    if user is not None and user.asana_token is not None:
        await message.answer("Ви вже авторизовані!")
        return
    reply_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Скасувавти")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Підключитися", url=auth_url)
            ]
        ]
    )

    await state.set_state(Authorization.token)
    await message.reply("Вітаю вас! Я - ProfITsoft Asana Bot, я забезпечую швидкий доступ до ваших Asana задач, "
                        "та допомогаю ефективно керувати персональними задачами та задачами команди, "
                        "не залишаючи вашого улюбленого месенджера",
                        reply_markup=reply_keyboard
                        )

    await message.reply(
        "Ви поки що не авторизовані в Асані. \n\nЧас підключатися! Перейдіть на сторінку авторизації Asana "
        "за наданим посиланням та скопіюйте отриманий там токен в чат.", reply_markup=inline_kb)


@router.message(Authorization.token)
async def process_token(message: Message, state: FSMContext) -> None:
    new_user = False
    print(message.text)
    if message.text == "Скасувати":
        await state.clear()
        await message.answer("Авторизація скасована.", reply_markup=ReplyKeyboardRemove())
        return
    elif is_valid_token_format(message.text):
        token, refresh_token = decrypt_tokens(key, message.text)
        asana_client = get_asana_client(message.from_user.id)
        users_api_instance = asana.UsersApi(asana_client)

        # Check if the token is valid by calling users/me endpoint
        try:
            user_info = users_api_instance.get_user("me", {})
        except asana.error.InvalidRequestError:
            await message.reply("Неправильний токен, спробуйте ще раз.")
            return

        asana_id = user_info['gid']
        user = get_user(message.from_user.id)
        if not user:
            new_user = True
        create_user(message.from_user.id, message.from_user.first_name, message.from_user.username, token,
                    refresh_token, asana_id)
        await message.answer(f"Ви успішно авторизувалися!", reply_markup=ReplyKeyboardRemove())

        await state.clear()
        workspaces_generator = asana.WorkspacesApi(asana_client).get_workspaces({'opt_fields': 'name'})
        workspaces = {workspace['gid']: workspace['name'] for workspace in workspaces_generator}

        if len(workspaces) == 1:
            workspace_gid, workspace_name = next(iter(workspaces.items()))
            settings = create_default_settings_private(message.chat.id, workspace_gid, workspace_name,
                                                       message.from_user.id)
            if settings:
                await message.answer(
                    f"За замовченням для Ваших задач в цьому чаті буде використовуватися робочий простір “{workspace_name}”")
                if new_user:
                    await message.answer(f"Вітаю, {message.from_user.first_name}! Тепер Ви можете створювати "
                                         f"та закривати задачі з розділу “Мої задачі“ прямо з цього чату або "
                                         f"додати бота у чат команди та керувати задачами спільного проекту.")
                return

        await state.set_state(DefaultSettingsPrivate.workspace)
        await state.update_data(new_user=new_user)

        workspace_buttons = [KeyboardButton(text=workspace) for workspace in workspaces.values()]
        workspace_buttons.append(KeyboardButton(text="Скасувати"))
        keyboard = ReplyKeyboardMarkup(
            keyboard=[workspace_buttons],
            resize_keyboard=True,
            one_time_keyboard=True
        )

        await message.answer("Будь ласка оберіть робочий простір за замовченням для Ваших задач в цьому чаті:",
                             reply_markup=keyboard)
    else:
        await message.reply("Трясця! Щось пішло не так.\n\nЦе не схоже на токен, спробуйте ще раз")


@router.message(StateFilter(DefaultSettingsPrivate.workspace))
async def select_workspace_private(message: Message, state: FSMContext):
    workspace_name = message.text
    if workspace_name == "Скасувати":
        await state.clear()
        await message.answer("Дія скасована.", reply_markup=ReplyKeyboardRemove())
        return

    asana_client = get_asana_client(message.from_user.id)
    workspaces = asana.WorkspacesApi(asana_client).get_workspaces({'opt_fields': 'name'})
    workspace_id = next((workspace['gid'] for workspace in workspaces if workspace['name'] == workspace_name), None)

    settings = create_default_settings_private(message.chat.id, workspace_id, workspace_name, message.from_user.id)

    if settings:
        await message.answer(f"Ваш воркспейс за замовченням - “{workspace_name}”.")

        data = await state.get_data()
        new_user = data['new_user']

        if new_user:
            await message.answer(f"Вітаю, {message.from_user.first_name}! Тепер Ви можете створювати "
                                 f"та закривати задачі з розділу “Мої задачі“ прямо з цього чату або "
                                 f"додати бота у чат команди та керувати задачами спільного проекту.")

    await state.clear()


@router.message(Command("stop"), is_private)
async def revoke_asana_token(message: Message):
    user = get_user(message.from_user.id)
    settings = get_default_settings(message.chat.id)
    if not user or not user.asana_token or not user.asana_refresh_token:
        await message.reply("Ви і без цього не були зареєстровані.")
        if settings.toggle_stickers:
            await message.answer_sticker("CAACAgIAAxkBAAELD7ZljiPT4kdgBgABT8XJDtHCqm9YynEAAtoIAAJcAmUD7sMu8F-uEy80BA")
        return
    url = "https://app.asana.com/-/oauth_revoke"
    payload = {
        'client_id': asana_client_id,
        'client_secret': asana_client_secret,
        'token': user.asana_refresh_token
    }

    response = requests.post(url, data=payload)

    if response.status_code == 200:
        print("Token successfully revoked.")
        create_user(message.from_user.id, message.from_user.first_name, message.from_user.username, None, None,
                    user.asana_id)
        await message.answer("Ваш токен успішно видалено.")
        if settings.toggle_stickers:
            await message.answer_sticker("CAACAgIAAxkBAAELD7ZljiPT4kdgBgABT8XJDtHCqm9YynEAAtoIAAJcAmUD7sMu8F-uEy80BA")
    else:
        print("Failed to revoke token:", response.text)


@router.message(Command("delete"), is_private)
async def delete_command(message: Message):
    user = get_user(message.from_user.id)
    delete_result = False
    if user:
        delete_result = delete_user(message.from_user.id)
    if delete_result or not user:
        await message.reply("Вас було успішно видалено з бази даних.")
        settings = get_default_settings(message.chat.id)
        if settings.toggle_stickers:
            await message.answer_sticker("CAACAgIAAxkBAAELD7ZljiPT4kdgBgABT8XJDtHCqm9YynEAAtoIAAJcAmUD7sMu8F-uEy80BA")


async def process_stickers_command(message: Message):
    settings = get_default_settings(message.chat.id)
    if settings:
        toggle_stickers(message.chat.id)
        if settings.toggle_stickers:
            await message.answer_sticker("CAACAgIAAxkBAAELD7ZljiPT4kdgBgABT8XJDtHCqm9YynEAAtoIAAJcAmUD7sMu8F-uEy80BA")
        else:
            await message.answer("Наліпки вимкнеко.")
    else:
        await message.answer("Спочатку оберіть налаштування за умовчанням за допомогою команди /link в цьому чаті")


async def process_link_command(message: Message, state: FSMContext) -> None:
    asana_client = get_asana_client(message.from_user.id)
    workspaces = asana.WorkspacesApi(asana_client).get_workspaces({'opt_fields': 'name'})
    workspace_buttons = [KeyboardButton(text=workspace['name']) for workspace in workspaces]
    workspace_buttons.append(KeyboardButton(text="Скасувати"))
    keyboard = ReplyKeyboardMarkup(
        keyboard=[workspace_buttons],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await state.set_state(DefaultSettings.workspace)
    await message.answer('Оберіть робочий простір за замовчуванням:', reply_markup=keyboard)


@router.message(StateFilter(DefaultSettings.workspace))
async def select_project(message: Message, state: FSMContext) -> None:
    if message.text == "Скасувати":
        await state.clear()
        await message.answer("Дія скасована. Попередні налаштування збережено.", reply_markup=ReplyKeyboardRemove())
        return

    workspace_name = message.text
    asana_client = get_asana_client(message.from_user.id)

    workspaces = asana.WorkspacesApi(asana_client).get_workspaces({'opt_fields': 'name'})
    workspace_id = next((workspace['gid'] for workspace in workspaces if workspace['name'] == workspace_name), None)
    await state.update_data(workspace_name=workspace_name)
    await state.update_data(workspace_id=workspace_id)

    projects = asana.ProjectsApi(asana_client).get_projects({'workspace': workspace_id, 'opt_fields': 'name'})
    project_buttons = [[KeyboardButton(text=project['name'])] for project in projects]
    project_buttons.append([KeyboardButton(text="Скасувати")])
    keyboard = ReplyKeyboardMarkup(
        keyboard=project_buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await state.set_state(DefaultSettings.project)
    await message.answer('Оберіть проект:', reply_markup=keyboard)


@router.message(StateFilter(DefaultSettings.project))
async def select_section(message: Message, state: FSMContext) -> None:
    if message.text == "Скасувати":
        await state.clear()
        await message.answer("Дія скасована. Попередні налаштування збережено.", reply_markup=ReplyKeyboardRemove())
        return

    project_name = message.text
    data = await state.get_data()
    workspace_id = data['workspace_id']
    asana_client = get_asana_client(message.from_user.id)

    projects = asana.ProjectsApi(asana_client).get_projects({'workspace': workspace_id, 'opt_fields': 'name'})
    project_id = next((project['gid'] for project in projects if project['name'] == project_name), None)

    await state.update_data(project_name=project_name)
    await state.update_data(project_id=project_id)

    sections = asana.SectionsApi(asana_client).get_sections_for_project(project_id, {'opt_fields': 'name'})
    section_buttons = [[KeyboardButton(text=section['name'])] for section in sections]
    section_buttons.append([KeyboardButton(text="Скасувати")])
    keyboard = ReplyKeyboardMarkup(
        keyboard=section_buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await state.set_state(DefaultSettings.section)
    await message.answer('Оберіть дошку:', reply_markup=keyboard)


@router.message(StateFilter(DefaultSettings.section))
async def save_settings(message: Message, state: FSMContext) -> None:
    if message.text == "Скасувати":
        await state.clear()
        await message.answer("Дія скасована. Попередні налаштування збережено.", reply_markup=ReplyKeyboardRemove())
        return

    data = await state.get_data()
    workspace_name = data['workspace_name']
    workspace_id = data['workspace_id']
    project_name = data['project_name']
    project_id = data['project_id']
    section_name = message.text

    asana_client = get_asana_client(message.from_user.id)
    sections = asana.SectionsApi(asana_client).get_sections_for_project(project_id, {'opt_fields': 'name'})
    section_id = next((section['gid'] for section in sections if section['name'] == section_name), None)

    # save settings
    await state.update_data(
        settings={'workspace_id': workspace_id, 'workspace_name': workspace_name, 'project_name': project_name,
                  'project_id': project_id, 'section_name': section_name, 'section_id': section_id})

    # send settings
    settings = await state.get_data()

    create_default_settings(message.chat.id, settings["workspace_id"], settings["workspace_name"],
                            settings["project_id"], settings["project_name"], section_id, section_name,
                            message.from_user.id)
    await message.answer("Налаштування успішно змінено!", reply_markup=ReplyKeyboardRemove())
    settings = get_default_settings(message.chat.id)
    if settings.toggle_stickers:
        await message.answer_sticker("CAACAgIAAxkBAAELD7ZljiPT4kdgBgABT8XJDtHCqm9YynEAAtoIAAJcAmUD7sMu8F-uEy80BA")
    await state.clear()


async def process_duetoday_command(message: Message, user_id: int, project_id: str):
    user_tasks_dict = get_todays_tasks_for_user_in_workspace(user_id, project_id)
    if not user_tasks_dict:
        await message.answer("На сьогодні задач немає.")
        return

    answer_text = "Завдання на сьогодні:\n" + "\n".join(
        [f"🔸 {task['name']}" for task in user_tasks_dict.values()])
    await message.answer(answer_text)


async def process_complete_command(message: Message, state: FSMContext, user_id: int, project_id: str):
    user_tasks_dict = get_all_tasks_for_user_in_workspace(user_id, project_id)
    if not user_tasks_dict:
        await message.answer("На сьогодні задач немає.")
        return

    task_buttons = [[KeyboardButton(text=task['name'])] for task in user_tasks_dict.values()]
    task_buttons.append([KeyboardButton(text="Скасувати")])
    keyboard = ReplyKeyboardMarkup(
        keyboard=task_buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    )

    if task_buttons:
        await message.answer("Оберіть задачу, яку бажаєте здати:", reply_markup=keyboard)
        await state.set_state(ReportTask.TaskName)
        await state.update_data(user_tasks_dict=user_tasks_dict)
    else:
        await message.answer("Наразі немає доступних задач.")


@router.message(Command("asana"))
@refresh_token
@check_settings
async def asana_command(message: Message, state: FSMContext):
    text = message.text
    print(f"Received message: {text}")  # Debugging print
    settings = get_default_settings(message.chat.id)

    parsed_data = parse_message_complete(text)
    command = parsed_data.get("command")

    if command:
        print(f"Command detected: {command}")  # Debugging print

        if command == "complete":
            await process_complete_command(message, state, message.from_user.id, settings.project_id)

        if command == "duetoday":
            await process_duetoday_command(message, message.from_user.id, settings.project_id)

        if command == "help":
            await process_help_command(message)

        if command == "stickers":
            await process_stickers_command(message)

        if command == "link":
            await process_link_command(message, state)

        return

    if not parsed_data:
        await message.answer("Неправильний формат повідомлення.")
        return

    task_name = parsed_data["task_name"]
    description = parsed_data["description"]
    date = parsed_data["date"]
    assignees = parsed_data["assignees"]

    asana_client = get_asana_client(message.from_user.id)
    settings = get_default_settings(message.chat.id)

    due_date = date

    assignee_asana_id = get_asana_id_by_username(assignees[0]) if assignees else get_asana_id_by_tg_id(
        message.from_user.id)

    body = {
        "data": {
            "name": task_name,
            "notes": description,
            "workspace": settings.workspace_id,
            "assignee": assignee_asana_id
        }
    }

    if due_date:
        body["data"]["due_on"] = due_date.isoformat()

    opts = {}

    try:
        tasks_api_instance = asana.TasksApi(asana_client)
        response = tasks_api_instance.create_task(body, opts)
        task_permalink = response.get('permalink_url', 'No permalink available')
        await message.answer(f"Задача створена: [Task Link]({task_permalink})", parse_mode='Markdown')
    except Exception as e:
        await message.answer(f"Помилка при створенні задачі: {e}")


# отримує ввсі задачі, незалежно від дати або її відсутності
def get_all_tasks_for_user_in_workspace(user_id, project_id):
    user = get_user(user_id)
    asana_client = get_asana_client(user_id)
    tasks_api_instance = asana.TasksApi(asana_client)
    user_gid = get_asana_id_by_username(user.tg_username)
    user_tasks_dict = {}

    try:
        opts = {
            'completed_since': "now",
            'opt_fields': "name, assignee"
        }
        tasks = tasks_api_instance.get_tasks_for_project(project_id, opts)
        for task in tasks:
            if task['assignee'] and task['assignee']['gid'] == user_gid:
                user_tasks_dict[task['gid']] = {
                    'name': task['name'],
                    'assignee_gid': task['assignee']['gid'],
                }
    except ApiException as e:
        logging.error(f"Error getting tasks for user {user_id}: {e}")

    return user_tasks_dict


# Функція для отримання задач на сьогодні
def get_todays_tasks_for_user_in_workspace(user_id, project_id):
    user = get_user(user_id)
    asana_client = get_asana_client(user_id)
    tasks_api_instance = asana.TasksApi(asana_client)
    user_gid = get_asana_id_by_username(user.tg_username)
    user_tasks_dict = {}

    try:
        today = datetime.date.today().isoformat()
        opts = {
            'completed_since': "now",
            'opt_fields': "name, assignee, due_on"
        }
        tasks = tasks_api_instance.get_tasks_for_project(project_id, opts)
        for task in tasks:
            if 'due_on' in task and task['due_on'] == today and task['assignee'] and task['assignee'][
                'gid'] == user_gid:
                user_tasks_dict[task['gid']] = {
                    'name': task['name'],
                    'assignee_gid': task['assignee']['gid'],
                }
    except ApiException as e:
        logging.error(f"Error getting tasks for user {user_id}: {e}")

    return user_tasks_dict


@router.message(StateFilter(ReportTask.TaskName))
async def handle_task_selection(message: Message, state: FSMContext):
    selected_task_name = message.text
    data = await state.get_data()

    if selected_task_name == "Скасувати":
        await state.clear()
        await message.answer("Дія скасована.", reply_markup=ReplyKeyboardRemove())
        return

    user_tasks_dict = data['user_tasks_dict']

    # Перевіряємо, чи вибрана задача є в списку задач
    task_found = False
    for task_gid, task_info in user_tasks_dict.items():
        if task_info['name'] == selected_task_name:
            task_found = True
            await message.answer("Будь ласка, надайте звіт:")
            await state.update_data(task_gid=task_gid)
            await state.set_state(ReportTask.Report)
            break

    if not task_found:
        await message.answer("Задача не знайдена. Будь ласка, виберіть задачу зі списку.")


@router.message(StateFilter(ReportTask.Report))
async def handle_task_report(message: Message, state: FSMContext):
    if message.text == "Скасувати":
        await state.clear()
        await message.answer("Дія скасована.", reply_markup=ReplyKeyboardRemove())
        return

    report_text = message.text
    data = await state.get_data()
    task_gid = data['task_gid']
    asana_client = get_asana_client(message.from_user.id)
    tasks_api_instance = asana.TasksApi(asana_client)

    # Get the existing task details
    task = tasks_api_instance.get_task(task_gid, {"opt_fields": "notes"})
    existing_notes = task['notes'] if 'notes' in task else ""

    # Append the new report to the existing notes
    new_notes = f"{existing_notes}\n\n\n\n@{message.from_user.username} здав задачу {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:\n{report_text}"

    body = {
        "data": {
            "notes": new_notes,
            "completed": True
        }
    }

    try:
        tasks_api_instance.update_task(body, task_gid, {})
        await message.answer("Звіт здано", reply_markup=ReplyKeyboardRemove())
        settings = get_default_settings(message.chat.id)
        if settings.toggle_stickers:
            await message.answer_sticker('CAACAgIAAxkBAAELD7ZljiPT4kdgBgABT8XJDtHCqm9YynEAAtoIAAJcAmUD7sMu8F-uEy80BA')
        await state.clear()
    except Exception as e:
        await message.answer(f"Помилка: {e}", reply_markup=ReplyKeyboardRemove())


async def daily_notification():
    chats_to_notify = get_default_settings_for_notification()
    today = datetime.date.today()

    for chat in chats_to_notify:
        project_id = chat.project_id
        notification_user_id = chat.notification_user_id
        all_users = session.query(Users).all()
        all_user_ids = set([user.tg_id for user in all_users])

        asana_client = get_asana_client(notification_user_id)
        tasks_api_instance = asana.TasksApi(asana_client)

        user = get_user(notification_user_id)
        users_api_instance = asana.UsersApi(asana_client)
        opts = {

        }
        try:
            users_api_instance.get_user("me", opts)
        except ApiException:
            new_access_token, new_refresh_token = refresh_access_token(user.asana_refresh_token)
            create_user(user.tg_id, user.tg_first_name,
                        user.tg_username, new_access_token,
                        new_refresh_token, user.asana_id)

        try:
            opts = {
                'completed_since': "now",
                'opt_fields': "name,assignee,due_on"
            }
            tasks = tasks_api_instance.get_tasks_for_project(project_id, opts)
            user_tasks = {}
            for task in tasks:
                task_detail = tasks_api_instance.get_task(task['gid'], opts)
                if 'due_on' in task_detail and task_detail['due_on']:
                    due_date = datetime.datetime.strptime(task_detail['due_on'], '%Y-%m-%d').date()
                    if due_date == today and 'assignee' in task_detail and task_detail['assignee']:
                        assignee_gid = task_detail['assignee']['gid']
                        telegram_id = session.query(Users).filter(Users.asana_id == assignee_gid).first().tg_id
                        if telegram_id:
                            if telegram_id not in user_tasks:
                                user_tasks[telegram_id] = []
                            user_tasks[telegram_id].append(task_detail['name'])

            # Відправка повідомлень користувачам з задачами
            for telegram_id, tasks in user_tasks.items():
                message = "У вас є завдання на сьогодні:\n" + "\n".join([f"🔸 {task}" for task in tasks])
                await bot.send_message(telegram_id, message)
                # Видаляємо ID зі списку
                all_user_ids.discard(telegram_id)

            # Відправка повідомлень користувачам без задач
            for user_id in all_user_ids:
                await bot.send_message(user_id, "На сьогодні задач немає.")

        except Exception as e:
            logging.error(f"Error fetching tasks for project {project_id}: {e}")


def get_user_task_list(user_gid, access_token):
    url = f"https://app.asana.com/api/1.0/users/{user_gid}/user_task_list"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error fetching user task list: {response.text}")


@router.message(Command("dk"))
async def dk_command(message: Message):
    user = get_user(message.from_user.id)
    user_task_list = get_user_task_list(user.asana_id, user.asana_token)
    await message.answer(user_task_list)


# * should be at the very end
@router.message(is_private)
@refresh_token
async def private_message(message: Message, state: FSMContext):
    text = message.text
    print(f"Received message: {text}")  # Debugging print

    settings = get_default_settings(message.chat.id)
    parsed_data = parse_message_complete(text)
    command = parsed_data.get("command")

    if command:
        print(f"Command detected: {command}")  # Debugging print

        if command == "complete":
            await process_complete_command(message, state, message.from_user.id, settings.project_id)

        if command == "duetoday":
            await process_duetoday_command(message, message.from_user.id, settings.project_id)

        if command == "help":
            await process_help_command(message)

        if command == "stickers":
            await process_stickers_command(message)

        if command == "link":
            await process_link_command(message, state)

        return

    if not parsed_data:
        await message.answer("Неправильний формат повідомлення.")
        return

    task_name = parsed_data["task_name"]
    description = parsed_data["description"]
    date = parsed_data["date"]
    assignees = parsed_data["assignees"]

    asana_client = get_asana_client(message.from_user.id)
    if asana_client is None:
        await message.answer("Спочатку ви маєте зареєструватися.")
        return

    settings = get_default_settings(message.chat.id)
    if not settings:
        await message.answer("Будь ласка, спочатку налаштуйте інтеграцію з Asana.")
        return

    due_date = date

    assignee_asana_id = get_asana_id_by_username(assignees[0]) if assignees else get_asana_id_by_tg_id(
        message.from_user.id)

    body = {
        "data": {
            "name": task_name,
            "notes": description,
            "workspace": settings.workspace_id,
            "assignee": assignee_asana_id
        }
    }

    if due_date:
        body["data"]["due_on"] = due_date.isoformat()

    opts = {}

    try:
        tasks_api_instance = asana.TasksApi(asana_client)
        response = tasks_api_instance.create_task(body, opts)
        task_permalink = response.get('permalink_url', 'No permalink available')
        await message.answer(f"Задача створена: [Task Link]({task_permalink})", parse_mode='Markdown')
    except Exception as e:
        await message.answer(f"Помилка при створенні задачі: {e}")
