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

    def test_parse_command_none(self):
        text = "/asana Назва @f до 10.11.2024 @quasarex @q\nОпис"
        expected_output = {
            "task_name": "Назва",
            "description": "Опис",
            "date": datetime.date(2024, 11, 10),
            "assignees": ["f", "quasarex", "q"],
            "command": None
        }
        self.assertEqual(parse_message_complete(text), expected_output)

    def test_parse_command_empty(self):
        text = "/asana "
        expected_output = {
            "task_name": "Untitled Task",
            "description": "",
            "date": None,
            "assignees": [],
            "command": None
        }
        self.assertEqual(parse_message_complete(text), expected_output)

    def test_parse_command_no_command(self):
        text = "/asana This is not a command"
        expected_output = {
            "task_name": "This is not a command",
            "description": "",
            "date": None,
            "assignees": [],
            "command": None
        }
        self.assertEqual(parse_message_complete(text), expected_output)


if __name__ == "__main__":
    unittest.main()
