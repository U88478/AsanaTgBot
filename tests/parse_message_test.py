import unittest

from utils.parse_message import parse_message, parse_command


class TestHandlers(unittest.TestCase):

    def test_parse_message_with_date_and_assignees(self):
        text = "Назва @f до 10.11.2024 @quasarex @q\nОпис"
        expected_output = {
            "task_name": "Назва",
            "description": "Опис",
            "date": "10.11.2024",
            "assignees": ["f", "quasarex", "q"]
        }
        self.assertEqual(parse_message(text), expected_output)

    def test_parse_message_with_date_only(self):
        text = "Назва до 10.11.2024\nОпис"
        expected_output = {
            "task_name": "Назва",
            "description": "Опис",
            "date": "10.11.2024",
            "assignees": []
        }
        self.assertEqual(parse_message(text), expected_output)

    def test_parse_message_with_assignees_only(self):
        text = "Назва @f @quasarex @q\nОпис"
        expected_output = {
            "task_name": "Назва",
            "description": "Опис",
            "date": None,
            "assignees": ["f", "quasarex", "q"]
        }
        self.assertEqual(parse_message(text), expected_output)

    def test_parse_message_with_task_name_only(self):
        text = "Назва\nОпис"
        expected_output = {
            "task_name": "Назва",
            "description": "Опис",
            "date": None,
            "assignees": []
        }
        self.assertEqual(parse_message(text), expected_output)

    def test_parse_message_with_task_name_and_no_description(self):
        text = "Назва"
        expected_output = {
            "task_name": "Назва",
            "description": "",
            "date": None,
            "assignees": []
        }
        self.assertEqual(parse_message(text), expected_output)

    def test_parse_command_complete(self):
        text = "complete"
        self.assertEqual(parse_command(text), "complete")

    def test_parse_command_duetoday(self):
        text = "duetoday"
        self.assertEqual(parse_command(text), "duetoday")

    def test_parse_command_none(self):
        text = "Назва @f до 10.11.2024 @quasarex @q\nОпис"
        self.assertIsNone(parse_command(text))


if __name__ == "__main__":
    unittest.main()
