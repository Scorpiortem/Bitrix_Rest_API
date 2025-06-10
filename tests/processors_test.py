import unittest
from processors import DataProcessor

class TestDataProcessor(unittest.TestCase):

    def test_merge_timeline_empty_input(self):
        data = {}
        result = DataProcessor.merge_timeline(data)
        self.assertEqual(result, [])

    def test_merge_timeline_with_activities(self):
        data = {
            "activities": [
                {"CREATED": "2025-06-10T10:00:00", "id": 1, "subject": "Call"},
                {"CREATED": "2025-06-09T09:30:00", "id": 2, "subject": "Email"},
                {"CREATED": "2025-06-10T12:00:00", "id": 3, "subject": "Meeting"},
            ]
        }
        result = DataProcessor.merge_timeline(data)

        #Проверяем, что события отсортированы по дате
        dates = [event['date'] for event in result]
        self.assertEqual(dates, sorted(dates))

        #Проверяем, что тип события установлен правильно
        for event in result:
            self.assertEqual(event['type'], 'activity')

        #Проверяем, что исходные данные сохранены
        self.assertEqual(result[0]['data']['id'], 2)  #Самое раннее событие
        self.assertEqual(result[-1]['data']['id'], 3)  #Самое позднее событие

    def test_merge_timeline_invalid_date_format(self):
        data = {
            "activities": [
                {"CREATED": "invalid-date", "id": 1}
            ]
        }
        with self.assertRaises(ValueError):
            DataProcessor.merge_timeline(data)

    def test_merge_timeline_missing_created_key(self):
        data = {
            "activities": [
                {"id": 1}
            ]
        }
        with self.assertRaises(KeyError):
            DataProcessor.merge_timeline(data)

if __name__ == "__main__":
    unittest.main()
