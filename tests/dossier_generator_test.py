import unittest
from datetime import datetime
from dossier_generator import ReportGenerator

class TestReportGenerator(unittest.TestCase):

    def test_generate_json_simple_dict(self):
        data = {"key": "value", "number": 123}
        json_str = ReportGenerator.generate_json(data)
        self.assertIn('"key": "value"', json_str)
        self.assertIn('"number": 123', json_str)
        #проверяем, что json_str — корректная строка JSON
        import json
        parsed = json.loads(json_str)
        self.assertEqual(parsed, data)

    def test_generate_json_with_non_serializable(self):
        #Проверяем, что default=str корректно обрабатывает нестандартные типы
        data = {"date": datetime(2025, 6, 10, 15, 0)}
        json_str = ReportGenerator.generate_json(data)
        self.assertIn("2025-06-10 15:00:00", json_str)

    def test_generate_markdown_basic(self):
        data = {
            "deal_id": 101,
            "timeline": [
                {
                    "date": datetime(2025, 6, 10, 12, 30),
                    "type": "call",
                    "data": {"SUBJECT": "Первый звонок"}
                },
                {
                    "date": datetime(2025, 6, 11, 9, 0),
                    "type": "email",
                    "data": {"SUBJECT": "Отправлено письмо"}
                }
            ],
            "user": {
                "ID": 1,
                "NAME": "Иван",
                "LAST_NAME": "Иванов",
                "WORK_POSITION": "Менеджер",
                "EMAIL": "ivan@example.com"
            },
            "dialog_messages": {
                "messages": [
                    {
                        "DATE": "2025-06-10 12:31",
                        "AUTHOR": "Иван",
                        "MESSAGE": "Здравствуйте!"
                    },
                    {
                        "DATE": "2025-06-10 12:32",
                        "AUTHOR": "Клиент",
                        "MESSAGE": "Добрый день!"
                    }
                ]
            }
        }

        md = ReportGenerator.generate_markdown(data)

        #Проверяем основные части отчёта
        self.assertIn("# Отчёт по сделке 101", md)
        self.assertIn("## 2025-06-10 12:30", md)
        self.assertIn("- Тип: call", md)
        self.assertIn("- Детали: Первый звонок", md)
        self.assertIn("## Ответственный", md)
        self.assertIn("- Имя: Иван", md)
        self.assertIn("## История переписки", md)
        self.assertIn("**2025-06-10 12:31 Иван**: Здравствуйте!", md)
        self.assertIn("**2025-06-10 12:32 Клиент**: Добрый день!", md)

    def test_generate_markdown_user_error(self):
        data = {
            "deal_id": 102,
            "timeline": [],
            "user": {"error": "Ответственный не найден"},
            "dialog_messages": {}
        }
        md = ReportGenerator.generate_markdown(data)
        self.assertIn("## Ответственный: Ответственный не найден", md)

    def test_generate_markdown_user_missing(self):
        data = {
            "deal_id": 103,
            "timeline": [],
            "user": {},
            "dialog_messages": {}
        }
        md = ReportGenerator.generate_markdown(data)
        self.assertIn("## Ответственный: Данные отсутствуют", md)

    def test_generate_markdown_user_invalid_format(self):
        data = {
            "deal_id": 104,
            "timeline": [],
            "user": "invalid_string",
            "dialog_messages": {}
        }
        md = ReportGenerator.generate_markdown(data)
        self.assertIn("## Ответственный: Некорректный формат данных", md)

    def test_generate_markdown_dialog_info(self):
        data = {
            "deal_id": 105,
            "timeline": [],
            "user": {},
            "dialog_messages": {"info": "Диалог отсутствует"}
        }
        md = ReportGenerator.generate_markdown(data)
        self.assertIn("## Переписка: Диалог отсутствует", md)

    def test_generate_markdown_dialog_no_messages(self):
        data = {
            "deal_id": 106,
            "timeline": [],
            "user": {},
            "dialog_messages": {"messages": []}
        }
        md = ReportGenerator.generate_markdown(data)
        #в этом случае блок "История переписки" будет, но без сообщений
        self.assertIn("## История переписки", md)

    def test_generate_markdown_dialog_messages_missing_fields(self):
        data = {
            "deal_id": 107,
            "timeline": [],
            "user": {},
            "dialog_messages": {
                "messages": [
                    {},  #пустое сообщение
                    {"DATE": "2025-06-10", "AUTHOR": "Автор"}  #без MESSAGE
                ]
            }
        }
        md = ReportGenerator.generate_markdown(data)
        self.assertIn("Дата неизвестна", md)
        self.assertIn("Текст отсутствует", md)
        self.assertIn("Автор", md)

if __name__ == "__main__":
    unittest.main()
