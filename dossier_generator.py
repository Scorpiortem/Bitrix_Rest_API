import json
from typing import Dict

class ReportGenerator:
    @staticmethod
    #Создание JSON-отчёта
    def generate_json(data: Dict) -> str:
        #Функция преобразует входные данные в формат JSON
        return json.dumps(data, indent=2, ensure_ascii=False, default=str)

    @staticmethod
    def generate_markdown(data: Dict) -> str:
        #Функция создаёт Markdown-отчёты по сделке
        md = f"# Отчёт по сделке {data['deal_id']}\n\n" #Создание заголовка отчёта
        #Добавляется информация о событиях в хронологическом порядке
        for event in data['timeline']:
            md += f"## {event['date'].strftime('%Y-%m-%d %H:%M')}\n"
            md += f"- Тип: {event['type']}\n"
            md += f"- Детали: {event['data'].get('SUBJECT', '')}\n\n"
        
        #Вывод информации об ответственном
        user_data = data.get("user", {})
        if isinstance(user_data, dict):
            if user_data.get("ID"):
                md += "## Ответственный\n"
                md += f"- Имя: {user_data.get('NAME', 'Не указано')}\n"
                md += f"- Фамилия: {user_data.get('LAST_NAME', 'Не указана')}\n"
                md += f"- Должность: {user_data.get('WORK_POSITION', 'Не указана')}\n"
                md += f"- Email: {user_data.get('EMAIL', 'Не указан')}\n\n"
            elif user_data.get("error"):
                md += f"## Ответственный: {user_data['error']}\n\n"
            else:
                md += "## Ответственный: Данные отсутствуют\n\n"
        else:
            md += "## Ответственный: Некорректный формат данных\n\n"
            
       #Вывод истории диалогов
        dialog = data.get('dialog_messages', {})
        if isinstance(dialog, dict):
            if 'info' in dialog:
                md += f"## Переписка: {dialog['info']}\n\n"
            elif 'messages' in dialog:
                md += "## История переписки\n"
                for msg in dialog['messages']:
                    md += (
                        f"**{msg.get('DATE', 'Дата неизвестна')} "
                        f"{msg.get('AUTHOR', 'Неизвестный автор')}**: "
                        f"{msg.get('MESSAGE', 'Текст отсутствует')}\n"
                    )
                md += "\n"

        return md