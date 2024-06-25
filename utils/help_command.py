from aiogram.types import Message

commands_list = """
📋 **Available Commands:**

🔹 **/start** - Start the bot and get initial instructions. Works only in private messages with the bot.
   *Usage:* `/start`
   *Explanation:* This command initiates interaction with the bot and provides initial setup instructions.

🔹 **/asana** - Main command to interact with Asana tasks.
   *Usage:* `/asana [task details]`
   *Explanation:* This command creates a task in Asana with the provided details.
   **Possible information: Task Name, Date, Assignees, Description**
   *Formats:*
     - **Task Name** - The first part of the message, excluding date and assignees, is treated as the task name.
     - **до dd.mm.yyyy** - Specify a due date.
     - **@`assignee_telegram_username`** - Assign the task to a user.
     - **Description** - Anything after a newline character (\n) is considered the task description.
   *General Example:* 
     - `Task Name до 25.12.2024 @user1 @user2\nTask description.`
     - `Buy groceries до 15.07.2024 @john_doe\nRemember to buy milk and bread.`

🔹 **/asana complete** - Report that a task is completed.
   *Usage:* `/asana complete`
   *Explanation:* This command lists all your tasks due today or overdue. Select a task to report it as completed.

🔹 **/asana duetoday** - List tasks due today.
   *Usage:* `/asana duetoday`
   *Explanation:* This command lists all your tasks that are due today.

🔹 **/asana link** - Set default workspace.
   *Usage:* `/asana link`
   *Explanation:* This command guides you through setting the default workspace where new tasks are created.

🔹 **/asana help** - Show this help message.
   *Usage:* `/asana help`
   *Explanation:* This command displays the help message with all available commands and their explanations.

🔹 **/asana stickers** - Toggle stickers on and off.
   *Usage:* `/asana stickers`
   *Explanation:* This command toggles the use of stickers on or off.

📝 **Private Message Specific Commands:**

🔹 **stop** - Revoke Asana token and stop integration.
   *Usage:* `stop`
   *Explanation:* This command revokes your Asana token and stops the integration with Asana.

🔹 **delete** - Delete your account from the bot.
   *Usage:* `delete`
   *Explanation:* This command deletes your account information from the bot's database.

📌 **Note:** In group chats, you must use the /asana prefix before commands to ensure the bot recognizes them. In private messages, you can use the commands directly without the /asana prefix. All commands from the group section work in private messages without the /asana prefix.
"""


async def process_help_command(message: Message):
    await message.answer(commands_list, parse_mode="Markdown")
