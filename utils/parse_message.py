import re


def parse_message(text):
    try:
        # Split the message into the first line and description
        if "\n" in text:
            fr, desc = text.split("\n", maxsplit=1)
        else:
            fr, desc = text, ""

        # Extract the date
        date_match = re.search(r'до\s+(\d{1,2}\.\d{1,2}\.\d{4})', fr)
        date = date_match.group(1) if date_match else None

        # Extract the assignees
        assignees = re.findall(r'@(\w+)', fr)

        # Remove all occurrences of @assignee and 'до' date to get the task name
        fr_cleaned = re.sub(r'@\w+', '', fr)  # Remove @assignee
        fr_cleaned = re.sub(r'до\s+\S+', '', fr_cleaned)  # Remove 'до' date
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
    command_pattern = r"^(complete|duetoday)"
    command_match = re.match(command_pattern, text)
    return command_match.group(1) if command_match else None
