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


def date_for_day_in_current_week(target_day_name):
    # Define the day names with indices including weekends
    week_days = {
        'понеділка': 0,
        'вівторка': 1,
        'середи': 2,
        'четверга': 3,
        'п\'ятниці': 4,
        'суботи': 5,
        'неділі': 6
    }

    # Get today's date and the current week's Monday
    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday())

    # Find the target day index and calculate the date for that day in this week
    target_day_index = week_days.get(target_day_name.lower())
    if target_day_index is not None:
        target_date = start_of_week + timedelta(days=target_day_index)
        return target_date.date()  # Returning just the date part
    else:
        return None  # If the day name isn't recognized


def calculate_due_date(marker):
    today = datetime.today()

    # Check for markers like 'через X днів'
    if marker.startswith("через"):
        days_str = marker.split()[1].replace("днів", "").replace("день", "").strip()
        try:
            days = int(days_str)
            return today + timedelta(days=days)
        except ValueError:
            return None

    # Check for specific weekday markers
    week_days = ['понеділка', 'вівторка', 'середи', 'четверга', 'п\'ятниці', 'суботи', 'неділі']
    for day_name in week_days:
        if day_name in marker:
            return date_for_day_in_current_week(day_name)

    # Other markers like 'до кінця дня'
    if "до кінця дня" in marker:
        return datetime.combine(today, datetime.max.time())

    elif "до кінця місяця" in marker:
        # Get the last day of the current month
        next_month = today.replace(day=28) + timedelta(days=4)
        last_day_of_month = next_month - timedelta(days=next_month.day)
        return datetime.combine(last_day_of_month, datetime.max.time())

    elif re.match(r"до \d{1,2}-го", marker):
        # Match day in the current month, e.g., "до 12-го"
        day = int(marker.split()[1].replace("-го", ""))
        return today.replace(day=day)

    else:
        return None


def parse_message(text):
    try:
        # Split the message into the first line and description
        if "\n" in text:
            fr, desc = text.split("\n", maxsplit=1)
        else:
            fr, desc = text, ""

        # Check for different time markers
        date_marker_match = re.search(
            r'через\s+\d+\s+дн(і|ів)|до\s+понеділка|до\s+вівторка|до\s+середи|до\s+четверга|до\s+п\'ятниці|до\s+суботи|до\s+неділі|до\s+кінця\s+дня|до\s+кінця\s+місяця|до\s+\d{1,2}-го',
            fr
        )
        date = None
        if date_marker_match:
            date_marker = date_marker_match.group(0)
            date = calculate_due_date(date_marker)
            if date:
                fr = re.sub(re.escape(date_marker), '', fr).strip()  # Remove the marker from the task name

        # Extract assignees
        assignees = re.findall(r'@(\w+)', fr)

        # Remove all occurrences of @assignee to get the task name
        fr_cleaned = re.sub(r'@\w+', '', fr)
        task_name = fr_cleaned.strip()

        return {
            "task_name": task_name,
            "description": desc.strip(),
            "date": date,
            "assignees": assignees
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
