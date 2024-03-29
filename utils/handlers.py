from asyncio import tasks
import datetime
import logging
import re
from tabnanny import check
from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.enums.chat_type import ChatType
from asana.rest import ApiException
from utils.asana_functions import *
from db.functions import session
from bot.bot_instance import bot
from utils.config import *
from utils.helpers import *
from utils.refresh_token_wrap import refresh_token
from utils.settings_decorator import check_settings
from utils.states.authorization import Authorization
from utils.states.default_settings import DefaultSettings
from utils.states.report_task import ReportTask
from utils.states.default_settings_private import DefaultSettingsPrivate

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
                KeyboardButton(text="Вийти")
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
    
    await message.reply("Ви поки що не авторизовані в Асані. \n\nЧас підключатися! Перейдіть на сторінку авторизації Asana "
                        "за наданим посиланням та скопіюйте отриманий там токен в чат.", reply_markup=inline_kb)


@router.message(Authorization.token)
async def process_token(message: Message, state: FSMContext) -> None:
    new_user = False
    if message.text == "Вийти":
        await state.clear()
        await message.answer("Авторизація скасована.", reply_markup=ReplyKeyboardRemove())
    elif is_valid_token_format(message.text):
        token, refresh_token = decrypt_tokens(key, message.text)
        asana_id = get_asana_id(token)
        user = get_user(message.from_user.id)
        if not user:
            new_user = True
        create_user(message.from_user.id, message.from_user.first_name, message.from_user.username, token,
                    refresh_token, asana_id)
        await message.answer(f"Ви успішно авторизувалися!", reply_markup=ReplyKeyboardRemove())
        
        await state.clear()
        asana_client = get_asana_client(message.from_user.id)
        workspaces_generator = asana.WorkspacesApi(asana_client).get_workspaces({'opt_fields': 'name'})
        workspaces = {workspace['gid']: workspace['name'] for workspace in workspaces_generator}

        if len(workspaces) == 1:
            workspace_gid, workspace_name = next(iter(workspaces.items()))
            settings = create_default_settings_private(message.chat.id, workspace_gid, workspace_name, message.from_user.id)
            if settings:
                await message.answer(f"За замовченням для Ваших задач в цьому чаті буде використовуватися робочий простір “{workspace_name}”")
                if new_user:
                    await message.answer(f"Вітаю, {message.from_user.first_name}! Тепер Ви можете створювати "
                                 f"та закривати задачі з розділу “Мої задачі“ прямо з цього чату або "
                                 f"додати бота у чат команди та керувати задачами спільного проекту.")
                return

        await state.set_state(DefaultSettingsPrivate.workspace)
        await state.update_data(new_user=new_user)

        workspace_buttons = [KeyboardButton(text=workspace['name']) for workspace in workspaces]
        keyboard = ReplyKeyboardMarkup(
            keyboard=[workspace_buttons],
            resize_keyboard=True,
            one_time_keyboard=True
        )

        await message.answer("Будь ласка оберіть робочий простір за замовченням для Ваших задач в цьому чаті:", reply_markup=keyboard)
    else:
        await message.reply("Трясця! Щось пішло не так.\n\nЦе не схоже на токен, спробуйте ще раз")


@router.message(DefaultSettingsPrivate.workspace)
async def select_workspace_private(message: Message, state: FSMContext):
    workspace_name = message.text
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
        create_user(message.from_user.id, message.from_user.first_name, message.from_user.username, None, None, user.asana_id)
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
       

@router.message(Command("stickers"))
async def stickers_command(message: Message):
    settings = get_default_settings(message.chat.id)
    if settings:
        toggle_stickers(message.chat.id)
        if settings.toggle_stickers:
            await message.answer_sticker("CAACAgIAAxkBAAELD7ZljiPT4kdgBgABT8XJDtHCqm9YynEAAtoIAAJcAmUD7sMu8F-uEy80BA")
        else:
            await message.answer("Наліпки вимкнеко.")
    else:
        await message.answer("Спочатку оберіть налаштування за умовчанням за допомогою команди /link в цьому чаті")


@router.message(Command("link"))
@refresh_token
async def process_link_command(message: Message, state: FSMContext) -> None:
    asana_client = get_asana_client(message.from_user.id)
    workspaces = asana.WorkspacesApi(asana_client).get_workspaces({'opt_fields': 'name'})
    workspace_buttons = [KeyboardButton(text=workspace['name']) for workspace in workspaces]
    keyboard = ReplyKeyboardMarkup(
        keyboard=[workspace_buttons],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await state.set_state(DefaultSettings.workspace)
    await message.answer('Оберіть робочий простір за замовчуванням:', reply_markup=keyboard)


@router.message(StateFilter(DefaultSettings.workspace))
async def select_project(message: Message, state: FSMContext) -> None:
    workspace_name = message.text
    asana_client = get_asana_client(message.from_user.id)

    workspaces = asana.WorkspacesApi(asana_client).get_workspaces({'opt_fields': 'name'})
    workspace_id = next((workspace['gid'] for workspace in workspaces if workspace['name'] == workspace_name), None)
    await state.update_data(workspace_name=workspace_name)
    await state.update_data(workspace_id=workspace_id)

    projects = asana.ProjectsApi(asana_client).get_projects({'workspace': workspace_id, 'opt_fields': 'name'})
    project_buttons = [[KeyboardButton(text=project['name'])] for project in projects]
    keyboard = ReplyKeyboardMarkup(
        keyboard=project_buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await state.set_state(DefaultSettings.project)
    await message.answer('Оберіть проект:', reply_markup=keyboard)


@router.message(StateFilter(DefaultSettings.project))
async def select_section(message: Message, state: FSMContext) -> None:
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
    keyboard = ReplyKeyboardMarkup(
        keyboard=section_buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await state.set_state(DefaultSettings.section)
    await message.answer('Оберіть дошку:', reply_markup=keyboard)

@router.message(StateFilter(DefaultSettings.section))
async def save_settings(message: Message, state: FSMContext) -> None:
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
    await state.update_data(settings={'workspace_id': workspace_id, 'workspace_name': workspace_name, 'project_name': project_name, 'project_id': project_id, 'section_name': section_name, 'section_id': section_id})

    # send settings
    settings = await state.get_data()
    
    
    create_default_settings(message.chat.id, settings["workspace_id"], settings["workspace_name"], settings["project_id"], settings["project_name"], section_id, section_name, message.from_user.id )
    await message.answer("Налаштування успішно змінено!", reply_markup=ReplyKeyboardRemove())
    settings = get_default_settings(message.chat.id)
    if settings.toggle_stickers:
        await message.answer_sticker("CAACAgIAAxkBAAELD7ZljiPT4kdgBgABT8XJDtHCqm9YynEAAtoIAAJcAmUD7sMu8F-uEy80BA")
    await state.clear()

@router.message(Command("asana"))
@refresh_token
@check_settings
async def asana_command(message: Message, state: FSMContext):
    text = message.text
    asana_client = get_asana_client(message.from_user.id)
    settings = get_default_settings(message.chat.id)


    pattern = r"/asana\s+(.*?)(?:\s+@(\w+))?(?:\s+до\s+(\d{1,2}\.\d{1,2}\.\d{2}(?:\d{2})?))?(?:\n(.*))?$"
    match = re.match(pattern, text)

    if match:
        command = match.group(1).strip()

        if command == "complete":
            # Логіка для команди "complete"
            user_tasks_dict = get_todays_tasks_for_user_in_workspace(message.from_user.id, settings.project_id)
            if not user_tasks_dict:
                await message.answer("На сьогодні задач немає.")
                return

            task_buttons = [[KeyboardButton(text=task['name'])] for task in user_tasks_dict.values()]
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

        elif command == "duetoday":
            # Логіка для команди "duetoday"
            user_tasks_dict = get_todays_tasks_for_user_in_workspace(message.from_user.id, settings.project_id)
            if not user_tasks_dict:
                await message.answer("На сьогодні задач немає.")
                return

            answer_text = "Завдання на сьогодні:\n" + "\n".join([f"🔸 {task['name']}" for task in user_tasks_dict.values()])
            await message.answer(answer_text)

        else:
            # Створення задачі
            assignee_username = match.group(2)
            due_date_str = match.group(3)
            description = match.group(4).strip() if match.group(4) else ""

            due_date = None

            assignee_asana_id = None
            if assignee_username:
                assignee_asana_id = get_asana_id_by_username(assignee_username)

            tasks_api_instance = asana.TasksApi(asana_client)
            body = {
                "data": {
                    "name": command,
                    "notes": description,
                    "workspace": settings.workspace_id,
                }
            }
            if due_date_str:
                due_date = parse_date(due_date_str)
            if due_date:
                body["data"]["due_on"] = due_date.isoformat()
            if assignee_asana_id:
                body["data"]["assignee"] = assignee_asana_id
            if settings.project_id:
                body["data"]["projects"] = [settings.project_id]

            try:
                opts = {}
                tasks_api_instance.create_task(body, opts)
                await message.answer("Задача створена")
                if settings.toggle_stickers:
                    await message.answer_sticker('CAACAgIAAxkBAAELD7ZljiPT4kdgBgABT8XJDtHCqm9YynEAAtoIAAJcAmUD7sMu8F-uEy80BA')
            except Exception as e:
                await message.answer(f"Помилка при створенні задачі: {e}")

    else:
        await message.answer("Неправильний формат команди.")


def parse_date(due_date_str):
    for date_format in ("%d.%m.%Y", "%d.%m.%y"):
        try:
            return datetime.datetime.strptime(due_date_str, date_format).date()
        except ValueError:
            continue
    # Якщо жоден з форматів не підходить, поверніть None або викличте помилку
    return None


# Функція для отримання задач на сьогодні
def get_todays_tasks_for_user_in_workspace(user_id, project_id):
    user = get_user(user_id)
    asana_client = get_asana_client(user_id)
    tasks_api_instance = asana.TasksApi(asana_client)
    user_gid = get_asana_id_by_username(user.tg_username)

    try:
        opts = {
        'completed_since': "now",
        'opt_fields' : "assignee" 
        }
        tasks = tasks_api_instance.get_tasks_for_project(project_id, opts)
        tasks_dict = {}
        opts = {
            'opt_fields': "name, assignee"
        }
        for task in tasks:
            task = tasks_api_instance.get_task(task['gid'], opts)
            task_info = {
                'name': task['name'],
                'assignee_gid': task['assignee']['gid'] if task['assignee'] else None,
            }
            tasks_dict[task['gid']] = task_info
        user_tasks_dict = {}
        for task in tasks_dict:
            if tasks_dict[task]['assignee_gid'] == user_gid:
                user_tasks_dict[task] = tasks_dict[task]

                
    except ApiException as e:
        logging.error(f"Error getting tasks for user {user_id}: {e}")

    return user_tasks_dict


@router.message(StateFilter(ReportTask.TaskName))
async def handle_task_selection(message: Message, state: FSMContext):
    selected_task_name = message.text
    data = await state.get_data() 
    user_tasks_dict = data['user_tasks_dict']

    # Перевіряємо, чи вибрана задача є в списку задач
    task_found = False
    for task_gid, task_info in user_tasks_dict.items():
        if task_info['name'] == selected_task_name:
            task_found = True
            await message.answer(f"Report: ")
            await state.update_data(task_gid=task_gid)
            await state.set_state(ReportTask.Report)
            break

    if not task_found:
        await message.answer("Задача не знайдена. Будь ласка, виберіть задачу зі списку.")


@router.message(StateFilter(ReportTask.Report))
async def handle_task_selection(message: Message, state: FSMContext):
    report_text = message.text
    data = await state.get_data() 
    task_gid = data['task_gid']
    asana_client = get_asana_client(message.from_user.id)
    tasks_api_instance = asana.TasksApi(asana_client)

    body = {
        "data": {
            "completed": True, 
            "notes": report_text
        }
    }
    
    opts = {

    }


    try:
        tasks_api_instance.update_task(body, task_gid, opts)
        await message.answer(f"Звіт здано", reply_markup=ReplyKeyboardRemove())
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


#* should be at the very end
@router.message(is_private)
@refresh_token
async def private_message(message: Message, state: FSMContext):
    text = message.text
    asana_client = get_asana_client(message.from_user.id)
    if asana_client == None:
        await message.answer("Спочатку ви маєте зареєструватися.")
        await start()

    settings = get_default_settings(message.chat.id)

    # Перевірка налаштувань користувача
    if not settings:
        await message.answer("Будь ласка, спочатку налаштуйте інтеграцію з Asana.")
        return

    pattern = r"^(.+?)(?:\s+до\s+(\d{1,2}\.\d{1,2}\.\d{2}(?:\d{2})?))?(?:\n(.*))?$"
    match = re.match(pattern, text)

    if match:
        task_name = match.group(1).strip()
        due_date_str = match.group(2)
        description = match.group(3).strip() if match.group(3) else ""

        due_date = None
        if due_date_str:
            try:
                due_date = datetime.datetime.strptime(due_date_str, "%d.%m.%Y").date()
            except ValueError:
                await message.answer("Неправильний формат дати. Використовуйте формат ДД.ММ.РРРР.")
                return

        # Виконавець - автор повідомлення
        assignee_asana_id = get_asana_id_by_tg_id(message.from_user.id)

        tasks_api_instance = asana.TasksApi(asana_client)
        body = {
            "data": {
                "name": task_name,
                "notes": description,
                "workspace": settings.workspace_id,
                "assignee": assignee_asana_id
            }
        }
        if settings.project_id:
            body["data"]["projects"] = [settings.project_id]
        if due_date:
            body["data"]["due_on"] = due_date.isoformat()

        opts = {}

        try:
            tasks_api_instance.create_task(body, opts)
            await message.answer("Задача створена")
            if settings.toggle_stickers:
                await message.answer_sticker('CAACAgIAAxkBAAELD7ZljiPT4kdgBgABT8XJDtHCqm9YynEAAtoIAAJcAmUD7sMu8F-uEy80BA')
        except Exception as e:
            await message.answer(f"Помилка при створенні задачі: {e}")
    else:
        await message.answer("Будь ласка, вкажіть назву задачі.")