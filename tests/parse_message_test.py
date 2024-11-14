import datetime
import unittest

from utils.parse_message import parse_message_complete


class TestHandlers(unittest.TestCase):

    def test_parse_message_no_prefix_with_date_and_assignees(self):
        text = "Назва @f до 10.11.2024 @quasarex @q\nОпис"
        expected_output = {
            "task_name": "Назва",
            "description": "Опис",
            "date": datetime.date(2024, 11, 10),
            "assignees": ["f", "quasarex", "q"],
            "command": None
        }
        self.assertEqual(parse_message_complete(text), expected_output)

    def test_parse_message_no_prefix_command_link(self):
        text = "link"
        expected_output = {
            "task_name": "Untitled Task",
            "description": "",
            "date": None,
            "assignees": [],
            "command": "link"
        }
        self.assertEqual(parse_message_complete(text), expected_output)

    def test_parse_message_with_date_and_assignees(self):
        text = "/asana Назва @f до 10.11.2024 @quasarex @q\nОпис"
        expected_output = {
            "task_name": "Назва",
            "description": "Опис",
            "date": datetime.date(2024, 11, 10),
            "assignees": ["f", "quasarex", "q"],
            "command": None
        }
        self.assertEqual(parse_message_complete(text), expected_output)

    def test_parse_message_with_date_only(self):
        text = "/asana Назва до 10.11.2024\nОпис"
        expected_output = {
            "task_name": "Назва",
            "description": "Опис",
            "date": datetime.date(2024, 11, 10),
            "assignees": [],
            "command": None
        }
        self.assertEqual(parse_message_complete(text), expected_output)

    def test_parse_message_with_assignees_only(self):
        text = "/asana Назва @f @quasarex @q\nОпис"
        expected_output = {
            "task_name": "Назва",
            "description": "Опис",
            "date": None,
            "assignees": ["f", "quasarex", "q"],
            "command": None
        }
        self.assertEqual(parse_message_complete(text), expected_output)

    def test_parse_message_with_task_name_only(self):
        text = "/asana Назва\nОпис"
        expected_output = {
            "task_name": "Назва",
            "description": "Опис",
            "date": None,
            "assignees": [],
            "command": None
        }
        self.assertEqual(parse_message_complete(text), expected_output)

    def test_parse_message_with_task_name_and_no_description(self):
        text = "/asana Назва"
        expected_output = {
            "task_name": "Назва",
            "description": "",
            "date": None,
            "assignees": [],
            "command": None
        }
        self.assertEqual(parse_message_complete(text), expected_output)

    def test_parse_message_empty(self):
        text = "/asana "
        expected_output = {
            "task_name": "Untitled Task",
            "description": "",
            "date": None,
            "assignees": [],
            "command": None
        }
        self.assertEqual(parse_message_complete(text), expected_output)

    def test_parse_message_invalid_date(self):
        text = "/asana Назва до 32.13.2024\nОпис"
        expected_output = {
            "task_name": "Назва до 32.13.2024",
            "description": "Опис",
            "date": None,
            "assignees": [],
            "command": None
        }
        self.assertEqual(parse_message_complete(text), expected_output)

    def test_parse_message_special_characters(self):
        text = "/asana Назва! @f# до 10.11.2024 @quasarex @q\nОпис*&^%"
        expected_output = {
            "task_name": "Назва! #",
            "description": "Опис*&^%",
            "date": datetime.date(2024, 11, 10),
            "assignees": ["f", "quasarex", "q"],
            "command": None
        }
        self.assertEqual(parse_message_complete(text), expected_output)

    def test_parse_message_no_task_name(self):
        text = "/asana @f до 10.11.2024 @quasarex @q\nОпис"
        expected_output = {
            "task_name": "Untitled Task",
            "description": "Опис",
            "date": datetime.date(2024, 11, 10),
            "assignees": ["f", "quasarex", "q"],
            "command": None
        }
        self.assertEqual(parse_message_complete(text), expected_output)

    def test_parse_message_due_in_days(self):
        text = "Назва через 5 днів @f\nОпис"
        expected_output = {
            "task_name": "Назва",
            "description": "Опис",
            "date": datetime.date.today() + datetime.timedelta(days=5),
            "assignees": ["f"],
            "command": None
        }
        self.assertEqual(parse_message_complete(text), expected_output)

    def test_parse_message_due_in_negative_days(self):
        text = "Назва через -3 дні @f\nОпис"
        expected_output = {
            "task_name": "Назва",
            "description": "Опис",
            "date": datetime.date.today() - datetime.timedelta(days=3),
            "assignees": ["f"],
            "command": None
        }
        self.assertEqual(parse_message_complete(text), expected_output)

    def test_parse_message_due_by_end_of_day(self):
        text = "Назва до кінця дня\nОпис"
        expected_output = {
            "task_name": "Назва",
            "description": "Опис",
            "date": datetime.date.today(),
            "assignees": [],
            "command": None
        }
        self.assertEqual(parse_message_complete(text), expected_output)

    def test_parse_message_due_by_end_of_month(self):
        text = "Назва до кінця місяця @f\nОпис"
        last_day_of_month = (datetime.date.today().replace(day=28) + datetime.timedelta(days=4)).replace(
            day=1) - datetime.timedelta(days=1)
        expected_output = {
            "task_name": "Назва",
            "description": "Опис",
            "date": last_day_of_month,
            "assignees": ["f"],
            "command": None
        }
        self.assertEqual(parse_message_complete(text), expected_output)

    def test_parse_message_due_by_specific_weekday(self):
        text = "Назва до понеділка @quasarex\nОпис"
        target_day = 0  # Monday
        today = datetime.date.today()
        days_until_monday = (target_day - today.weekday()) % 7
        due_date = today + datetime.timedelta(days=days_until_monday)
        expected_output = {
            "task_name": "Назва",
            "description": "Опис",
            "date": due_date,
            "assignees": ["quasarex"],
            "command": None
        }
        self.assertEqual(parse_message_complete(text), expected_output)

    def test_parse_message_due_by_specific_day_of_month(self):
        text = "Назва до 15-го\nОпис"
        today = datetime.date.today()
        due_date = today.replace(day=15) if today.day <= 15 else today.replace(day=15) + datetime.timedelta(days=30)
        expected_output = {
            "task_name": "Назва",
            "description": "Опис",
            "date": due_date,
            "assignees": [],
            "command": None
        }
        self.assertEqual(parse_message_complete(text), expected_output)

    # Command-related test cases
    def test_parse_command_complete(self):
        text = "/asana complete"
        expected_output = {
            "task_name": "Untitled Task",
            "description": "",
            "date": None,
            "assignees": [],
            "command": "complete"
        }
        self.assertEqual(parse_message_complete(text), expected_output)

    def test_parse_command_duetoday(self):
        text = "/asana duetoday"
        expected_output = {
            "task_name": "Untitled Task",
            "description": "",
            "date": None,
            "assignees": [],
            "command": "duetoday"
        }
        self.assertEqual(parse_message_complete(text), expected_output)

    def test_parse_command_link(self):
        text = "/asana link"
        expected_output = {
            "task_name": "Untitled Task",
            "description": "",
            "date": None,
            "assignees": [],
            "command": "link"
        }
        self.assertEqual(parse_message_complete(text), expected_output)

    def test_due_in_days(self):
        text = "Назва через 7 днів"
        expected_output = {
            "task_name": "Назва",
            "description": "",
            "date": datetime.date.today() + datetime.timedelta(days=7),
            "assignees": [],
            "command": None
        }
        self.assertEqual(parse_message_complete(text), expected_output)

    def test_due_in_negative_days(self):
        text = "Назва через -5 днів"
        expected_output = {
            "task_name": "Назва",
            "description": "",
            "date": datetime.date.today() - datetime.timedelta(days=5),
            "assignees": [],
            "command": None
        }
        self.assertEqual(parse_message_complete(text), expected_output)

    def test_due_by_end_of_day(self):
        text = "Назва до кінця дня"
        expected_output = {
            "task_name": "Назва",
            "description": "",
            "date": datetime.date.today(),
            "assignees": [],
            "command": None
        }
        self.assertEqual(parse_message_complete(text), expected_output)

    def test_due_by_end_of_month(self):
        text = "Назва до кінця місяця"
        last_day_of_month = (datetime.date.today().replace(day=28) + datetime.timedelta(days=4)).replace(
            day=1) - datetime.timedelta(days=1)
        expected_output = {
            "task_name": "Назва",
            "description": "",
            "date": last_day_of_month,
            "assignees": [],
            "command": None
        }
        self.assertEqual(parse_message_complete(text), expected_output)

    def test_due_by_specific_weekday(self):
        text = "Назва до Понеділка"
        target_day = 0
        today = datetime.date.today()
        days_until_target = (target_day - today.weekday()) % 7
        due_date = today + datetime.timedelta(days=days_until_target)
        expected_output = {
            "task_name": "Назва",
            "description": "",
            "date": due_date,
            "assignees": [],
            "command": None
        }
        self.assertEqual(parse_message_complete(text), expected_output)

    def test_due_by_specific_day_of_month(self):
        text = "Назва до 15-го"
        today = datetime.date.today()
        if today.day <= 15:
            due_date = today.replace(day=15)
        else:
            # If today's date is past the 15th, set due date to the next month 15th
            due_date = (today.replace(day=1) + datetime.timedelta(days=32)).replace(day=15)
        expected_output = {
            "task_name": "Назва",
            "description": "",
            "date": due_date,
            "assignees": [],
            "command": None
        }
        self.assertEqual(parse_message_complete(text), expected_output)


if __name__ == "__main__":
    unittest.main()
