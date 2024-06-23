import re

text = "/asana duetoday"

command_pattern = r"^/?asana\s*(complete|duetoday)"
command_match = re.match(command_pattern, text)
command = command_match.group(1) if command_match else None

print(command)
