import re

msg = "Назва #ff @f #10.11.2024 ттттт @quasarex @a #ььььььь @q qqqqqq\n Опис"

# Split the message into the first line and description
fr, desc = msg.split("\n", maxsplit=1)

# Remove all occurrences of @assignee and #date
fr_cleaned = re.sub(r'@\w+', '', fr)  # Remove @assignee
fr_cleaned = re.sub(r'#\S+', '', fr_cleaned)  # Remove #date

# The task name is the remaining part of the first line
task_name = fr_cleaned.strip()

# Extract date
date = re.search(r'#(\d{1,2}\.\d{1,2}\.\d{4})', fr).group(1)

# Extract assignees
assignee = [str(x.split(maxsplit=2)[0]) for x in str(fr).split("@")[1:]]

print("Task Name:", task_name)
print("Date:", date)
print("Assignees:", assignee)
print("Description:", desc.strip())
