from datetime import datetime
from typing import Dict, List

class DataProcessor:
    @staticmethod
    def merge_timeline(data: Dict) -> List[Dict]:
        #Объединяет данные из разных источников (активности, комментарии, звонки) в единую хронологическую ленту событий.
        timeline = []
        #Обработка активностей (задачи, письма, звонки)
        for event in data.get('activities', []):
            timeline.append({
                'type': 'activity', #Тип события для последующей фильтрации
                'date': datetime.fromisoformat(event['CREATED']), #Парсинг даты
                'data': event #Сохранение исходных данных
            })
        #Аналогично для других источников
        return sorted(timeline, key=lambda x: x['date']) #Критерий сортировки - дата события