import logging
import re
from datetime import datetime, timedelta


def parse_date(due_date_str):
    for date_format in ("%d.%m.%Y", "%d.%m.%y"):
        try:
            return datetime.strptime(due_date_str, date_format).date()
        except ValueError:
            continue
    return None


def date_for_day_in_current_week(target_day_name, allow_past=True):
    week_days = {
        'понеділка': 0,
        'вівторка': 1,
        'середи': 2,
        'четверга': 3,
        'п\'ятниці': 4,
        'суботи': 5,
        'неділі': 6
    }

    today = datetime.today().date()
    target_day_index = week_days.get(target_day_name.lower())

    if target_day_index is not None:
        days_difference = target_day_index - today.weekday()
        if days_difference < 0:
            days_difference += 7 if allow_past else 0
        elif days_difference > 0 and not allow_past:
            days_difference -= 7
        return today + timedelta(days=days_difference)
    else:
        return None


def calculate_due_date(marker):
    today = datetime.today().date()

    # Handle "через X днів" cases
    if marker.startswith("через"):
        days_str = re.sub(r"\bд(ні|нів|ня|ей|ень)\b", "", marker.split()[1]).strip()
        try:
            days = int(days_str)
            return today + timedelta(days=days)
        except ValueError:
            return None

    # Handle specific weekday markers
    week_days = ['понеділка', 'вівторка', 'середи', 'четверга', 'п\'ятниці', 'суботи', 'неділі']
    for day_name in week_days:
        if day_name in marker:
            return date_for_day_in_current_week(day_name, allow_past=True)

    # Handle specific date formats
    date_match = re.search(r"до\s+(\d{1,2}\.\d{1,2}\.\d{2,4})", marker)
    if date_match:
        date_str = date_match.group(1)
        return parse_date(date_str)

    # Handle "до кінця дня"
    if "до кінця дня" in marker:
        return today

    # Handle "до кінця місяця"
    elif "до кінця місяця" in marker:
        next_month = today.replace(day=28) + timedelta(days=4)
        last_day_of_month = next_month - timedelta(days=next_month.day)
        return last_day_of_month

    # Handle specific day of the month
    elif re.match(r"до \d{1,2}-го", marker):
        day = int(marker.split()[1].replace("-го", ""))
        try:
            return today.replace(day=day)
        except ValueError:
            return None  # In case the day is invalid for the month

    else:
        return None


def parse_message(text):
    try:
        # Split the message into the first row and description
        if "\n" in text:
            fr, desc = text.split("\n", maxsplit=1)
        else:
            fr, desc = text, ""

        # Check for different time markers
        date_marker_match = re.search(
            r'через\s+[-+]?\d+\s*\bд(ні|нів|ня|ей|ень)\b|'  # "через X днів"
            r'до\s+понеділка|до\s+вівторка|до\s+середи|до\s+четверга|до\s+п\'ятниці|до\s+суботи|до\s+неділі|'  # Weekday markers
            r'до\s+кінця\s+дня|до\s+кінця\s+місяця|'  # End of day/month
            r'до\s+\d{1,2}-го|'  # Day of month (e.g., до 25-го)
            r'до\s+\d{1,2}\.\d{1,2}\.\d{2,4}',  # Date format (e.g., до 25.12.2024)
            fr.lower()
        )

        date = None
        if date_marker_match:
            date_marker = date_marker_match.group(0)
            # Calculate date only if marker is valid and recognized
            date = calculate_due_date(date_marker)
            if date:
                # Remove marker from the task name
                fr = re.sub(re.escape(date_marker), '', fr, flags=re.IGNORECASE).strip()

        # Extract assignees
        assignees = re.findall(r'@(\w+)', fr)

        # Remove all occurrences of @assignee to get the task name
        fr_cleaned = re.sub(r'@\w+', '', fr).strip()
        task_name = fr_cleaned or "Untitled Task"

        return {
            "task_name": task_name,
            "description": desc.strip(),
            "date": date,
            "assignees": assignees,
            "command": None
        }
    except Exception as e:
        logging.debug(f"Error during parsing: {e}")
        return None


def parse_command(text):
    command_pattern = r"^(complete|duetoday|link|stickers|comment|help)"
    command_match = re.match(command_pattern, text.strip())
    return command_match.group(1) if command_match else None


def parse_message_complete(text: str):
    try:
        text = text.replace("/", "", 1).replace("asana ", "").strip()
        command = parse_command(text)
        if command:
            text = text.replace(command, "", 1).strip()
        data = parse_message(text)
        if not data["task_name"]:
            data["task_name"] = "Untitled Task"
        data["command"] = command
        return data
    except AttributeError:
        logging.debug('Not a text')
