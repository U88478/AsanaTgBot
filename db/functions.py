from sqlalchemy import and_
from .models import Users, DefaultSettings, session


def create_user(tg_id: int, tg_first_name: str, tg_username: str, asana_token: str, asana_refresh_token: str,
                asana_id: str):
    user = session.query(Users).filter(Users.tg_id == tg_id).first()
    if user:
        # Оновлення існуючого користувача
        user.asana_token = asana_token
        user.asana_refresh_token = asana_refresh_token
        user.asana_id = asana_id
    else:
        # Створення нового користувача
        user = Users(tg_id=tg_id, tg_first_name=tg_first_name, tg_username=tg_username, asana_token=asana_token,
                     asana_refresh_token=asana_refresh_token, asana_id=asana_id)
        session.add(user)
    session.commit()


def get_user(tg_id: int) -> Users:
    user = session.query(Users).filter(Users.tg_id == tg_id).first()
    return user

def get_all_user_ids():
    users = session.query(Users).all()
    user_ids = [user.tg_id for user in users]
    return user_ids

def get_asana_id_by_username(username: str) -> str:
    user = session.query(Users).filter(Users.tg_username == username).first()
    return user.asana_id

def delete_user(tg_id: int):
    session.query(Users).filter(Users.tg_id == tg_id).delete()
    session.commit()
    return True

def create_default_settings_private(chat_id: int, workspace_id: str, workspace_name: str, notification_user_id: int, stickers: bool = True):
    settings = session.query(DefaultSettings).filter(DefaultSettings.chat_id == chat_id).first()

    if settings:
        # Якщо запис існує, оновлюємо його значення
        settings.chat_id = chat_id
        settings.workspace_id = workspace_id
        settings.workspace_name = workspace_name
        settings.notification_user_id = notification_user_id
        settings.toggle_stickers = stickers
    else:
        # Якщо запис не існує, створюємо новий запис
        settings = DefaultSettings(
            chat_id=chat_id,
            workspace_id=workspace_id,
            workspace_name=workspace_name,
            notification_user_id=notification_user_id,
            toggle_stickers=stickers
        )

    session.add(settings)
    session.commit()
    return True

def create_default_settings(chat_id: int, workspace_id: str, workspace_name: str, project_id: str,
                            project_name: str, section_id: str, section_name: str, user_id: int, stickers: bool = True):
    settings = session.query(DefaultSettings).filter(DefaultSettings.chat_id == chat_id).first()

    print(chat_id)
    print(workspace_id)
    print(workspace_id)
    print(project_id)
    print(project_name)
    print(section_id)
    print(section_name)
    print(user_id)
    print(stickers)

    if settings:
        # Якщо запис існує, оновлюємо його значення
        settings.workspace_id = workspace_id
        settings.workspace_name = workspace_name
        settings.project_id = project_id
        settings.project_name = project_name
        settings.section_id = section_id
        settings.section_name = section_name
        settings.notification_user_id = user_id
        settings.toggle_stickers = stickers
    else:
        # Якщо запис не існує, створюємо новий запис
        settings = DefaultSettings(
            chat_id=chat_id,
            workspace_id=workspace_id,
            workspace_name=workspace_name,
            project_id=project_id,
            project_name=project_name,
            section_id=section_id,
            section_name=section_name,
            notification_user_id=user_id,
            toggle_stickers=stickers
        )

    session.add(settings)
    session.commit()
    return True

def get_default_settings_for_notification() -> DefaultSettings:
    settings = session.query(DefaultSettings).filter(and_(DefaultSettings.notification_user_id != None, DefaultSettings.chat_id < 0)).all()
    return settings

def get_default_settings(chat_id: int) -> DefaultSettings:
    settings = session.query(DefaultSettings).filter(DefaultSettings.chat_id == chat_id).first()
    return settings

def toggle_stickers(chat_id: int):
    chat_settings = get_default_settings(chat_id)
    if chat_settings:
        chat_settings.stickers = not chat_settings.stickers
        session.commit()

def delete_settings(chat_id: int):
    session.query(DefaultSettings).filter(DefaultSettings.chat_id == chat_id).delete()
    session.commit()
