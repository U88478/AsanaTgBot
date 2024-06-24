import datetime
import re


def parse_date(due_date_str):
    for date_format in ("%d.%m.%Y", "%d.%m.%y"):
        try:
            return datetime.datetime.strptime(due_date_str, date_format).date()
        except ValueError:
            continue
    return None


def parse_message(text):
    try:
        # Split the message into the first line and description
        if "\n" in text:
            fr, desc = text.split("\n", maxsplit=1)
        else:
            fr, desc = text, ""

        # Extract the date and validate it
        date_match = re.search(r'до\s+(\d{1,2}\.\d{1,2}\.\d{4})', fr)
        date = None
        if date_match:
            date_str = date_match.group(1)
            date = parse_date(date_str)
            if date:
                fr = re.sub(r'до\s+' + re.escape(date_str), '', fr)  # Remove valid date from the task name

        # Extract the assignees
        assignees = re.findall(r'@(\w+)', fr)

        # Remove all occurrences of @assignee to get the task name
        fr_cleaned = re.sub(r'@\w+', '', fr)  # Remove @assignee
        task_name = fr_cleaned.strip()

        return {
            "task_name": task_name,
            "description": desc.strip(),
            "date": date,
            "assignees": assignees
        }
    except Exception as e:
        print(f"Error during parsing: {e}")
        return None


def parse_command(text):
    command_pattern = r"^(complete|duetoday|link|stickers)"
    command_match = re.match(command_pattern, text.strip())
    return command_match.group(1) if command_match else None


def parse_message_complete(text: str):
    text = text.replace("/", "", 1).replace("asana ", "").strip()
    command = parse_command(text)
    if command:
        text = text.replace(command, "", 1).strip()
    data = parse_message(text)
    if not data["task_name"]:
        data["task_name"] = "Untitled Task"
    data["command"] = command
    return data
