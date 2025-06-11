import unittest
from unittest.mock import MagicMock, call, patch
from data_fetchers import BaseFetcher, BitrixFetcher

class TestBaseFetcherConfig(unittest.TestCase):
    def setUp(self):
        self.test_config = {
            "log_level": "DEBUG",
            "logger": MagicMock()
        }
        
        self.fetcher = BaseFetcher(self.test_config)
        self.fetcher.session = MagicMock()
        self.fetcher.session.headers = {}  #Инициализируем headers как обычный словарь
        self.fetcher.session.headers.update({"User-Agent": "DealDossier/1.0"})

    def test_config_initialization(self):
        #Проверка корректной инициализации конфигурации
        with self.assertRaises(KeyError):
            self.fetcher.config["bitrix_url"]

        self.assertIsInstance(self.fetcher.logger, MagicMock)
        self.assertEqual(self.fetcher.session.headers["User-Agent"], "DealDossier/1.0")

    def test_pagination_with_real_config(self):
        #тест пагинации, используем URL для теста
        mock_response = MagicMock()
        mock_response.json.side_effect = [
            {"result": [1,2], "total": 4},
            {"result": [3,4], "total": 4}
        ]
        self.fetcher.session.get.return_value = mock_response

        results = self.fetcher._handle_pagination(
            f"{self.bitrix_url}/rest/",  #Используем URL из setUp
            {"key": "value"}
        )
        
        self.assertEqual(results, [1,2,3,4])
        self.fetcher.logger.debug.assert_has_calls([
            call("Пагинация: start=0, получено 2 элементов"),
            call("Пагинация: start=2, получено 2 элементов")
        ])

class TestBitrixFetcherConfig(unittest.TestCase):
    def setUp(self):
        # Мокаем переменные окружения
        self.patcher = patch.dict('os.environ', {
            'BITRIX_URL': 'https://test.bitrix24.ru',
            'BITRIX_TOKEN': 'test_token'
        })
        self.patcher.start()
        
        self.fetcher = BitrixFetcher()
        self.fetcher.logger = MagicMock()
        self.fetcher.session = MagicMock()

    def tearDown(self):
        self.patcher.stop()

    def test_bitrix_url_construction(self):
        expected_url = "https://test.bitrix24.ru/rest/1/test_token/"
        self.assertEqual(self.fetcher.base_url, expected_url)

    def test_full_workflow_with_config(self):
        self.fetcher.session.get.side_effect = [
            self._mock_response({"ASSIGNED_BY_ID": 42}),
            self._mock_response({"PHONE": "123456"}),
            self._mock_response({"NAME": "John"}),
            self._mock_response([]),
            self._mock_response([{"id": 1}]),
            self._mock_response({"messages": []}),
            self._mock_response({"dialog": "info"})
        ]
        self.fetcher._get_dialog_id = MagicMock(return_value="123")

        data = self.fetcher.get_deal_data(123)

        self.assertEqual(data["deal"]["ASSIGNED_BY_ID"], 42)
        self.assertEqual(data["contact"]["PHONE"], "123456")
        self.assertEqual(data["user"]["NAME"], "John")

        expected_calls = [
            call(f"{self.fetcher.base_url}crm.deal.get", params={"id": 123}),
            call(f"{self.fetcher.base_url}crm.contact.get", params={"id": 123}),
            call(f"{self.fetcher.base_url}user.get", params={
                "id": 42,
                "select": ["ID", "NAME", "LAST_NAME", "EMAIL", "WORK_POSITION"]
            })
        ]
        self.fetcher.session.get.assert_has_calls(expected_calls[:3])

    def _mock_response(self, data):
        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"result": data}
        return response

    def test_logging_configuration(self):
        self.fetcher.logger.debug("Test debug")
        self.fetcher.logger.error("Test error")

        self.test_config["logger"].debug.assert_called_with("Test debug")
        self.test_config["logger"].error.assert_called_with("Test error")

if __name__ == "__main__":
    unittest.main()
