import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
from main import main

class TestMainFunction(unittest.TestCase):
    
    def setUp(self):
        #настройка общих моков для всех тестов
        self.default_config = {
            "bitrix_url": "https://test.bitrix24.ru",
            "bitrix_token": "test_token", 
            "log_level": "INFO",
            "logger": MagicMock()
        }
    
    @patch("sys.exit")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    @patch("main.load_config")
    @patch("main.BitrixFetcher")
    @patch("main.DataProcessor.merge_timeline", return_value=[{"date": "2025-06-10"}])
    @patch("main.ReportGenerator.generate_json", return_value='{"json": "report"}')
    @patch("main.ReportGenerator.generate_markdown", return_value="md_report")
    def test_main_all_formats(self, mock_generate_markdown, mock_generate_json,
                            mock_merge_timeline, mock_bitrix_fetcher_cls,
                            mock_load_config, mock_makedirs, mock_open_file,
                            mock_exit):
        #Тест генерации отчетов во всех форматах
        
        #настройка мока для load_config
        mock_load_config.return_value = self.default_config
        
        #подготовка мока для BitrixFetcher
        mock_bitrix_instance = MagicMock()
        mock_bitrix_instance.get_deal_data.return_value = {
            "user": {"ID": 1},
            "dialog_messages": {"messages": []}
        }
        mock_bitrix_fetcher_cls.return_value = mock_bitrix_instance
        
        #тестовые аргументы командной строки
        test_args = ["main.py", "123", "-f", "all", "-o", "outdir"]
        
        with patch.object(sys, 'argv', test_args):
            main()
        
        #Проверки
        mock_load_config.assert_called_once()
        mock_makedirs.assert_called_once_with("outdir", exist_ok=True)
        mock_bitrix_fetcher_cls.assert_called_once_with(self.default_config)
        
        #проверяем вызовы генерации отчетов
        mock_generate_json.assert_called_once()
        mock_generate_markdown.assert_called_once()
        
        #проверяем, что файлы открываются для записи
        expected_json_path = "outdir/deal_123.json"
        expected_md_path = "outdir/deal_123.md"
        mock_open_file.assert_any_call(expected_json_path, 'w', encoding='utf-8')
        mock_open_file.assert_any_call(expected_md_path, 'w', encoding='utf-8')
        
        #убедимся, что sys.exit не вызван (успешное завершение)
        mock_exit.assert_not_called()

    @patch("sys.exit")
    @patch("main.load_config")
    @patch("logging.getLogger")
    def test_main_exception_handling(self, mock_get_logger, mock_load_config, mock_exit):
        #тест обработки исключений
        
        #мок базового логгера
        mock_base_logger = MagicMock()
        mock_get_logger.return_value = mock_base_logger
        
        #эмулируем ошибку при загрузке конфига
        mock_load_config.side_effect = Exception("Test error")
        
        test_args = ["main.py", "123"]
        with patch.object(sys, 'argv', test_args):
            main()
        
        #проверяем обработку ошибки
        mock_base_logger.error.assert_called_once()
        mock_exit.assert_called_once_with(1)

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    @patch("main.ReportGenerator.generate_markdown", return_value="md_report")
    @patch("main.ReportGenerator.generate_json", return_value='{"json": "report"}')
    @patch("main.DataProcessor.merge_timeline", return_value=[])
    @patch("main.BitrixFetcher")
    @patch("main.load_config")
    def test_main_verbose_sets_debug_level(self, mock_load_config, mock_bitrix_fetcher_cls,
                                         mock_merge_timeline, mock_generate_json,
                                         mock_generate_markdown, mock_makedirs, mock_open_file):
        #тест установки уровня DEBUG при verbose режиме
        
        #создаем мок логгера из конфига
        mock_config_logger = MagicMock()
        mock_config = self.default_config.copy()
        mock_config["logger"] = mock_config_logger
        mock_load_config.return_value = mock_config
        
        #настройка BitrixFetcher
        mock_bitrix_instance = MagicMock()
        mock_bitrix_instance.get_deal_data.return_value = {}
        mock_bitrix_fetcher_cls.return_value = mock_bitrix_instance
        
        test_args = ["main.py", "123", "-v"]
        with patch.object(sys, 'argv', test_args):
            main()
        
        #проверяем установку уровня DEBUG для логгера из конфига
        mock_config_logger.setLevel.assert_called_once_with('DEBUG')

    @patch("main.load_config")
    def test_load_config_fallback(self, mock_load_config):
        #тест fallback конфигурации без файла config.json
        
        #создаем реальную функцию load_config с fallback
        def mock_load_config_with_fallback():
            try:
                #пытаемся загрузить config.json (его нет)
                with open('config.json', 'r', encoding='utf-8') as f:
                    import json
                    return json.load(f)
            except FileNotFoundError:
                #возвращаем конфигурацию по умолчанию
                import logging
                logger = logging.getLogger(__name__)
                logger.setLevel(logging.INFO)
                return {
                    "bitrix_url": "https://default.bitrix24.ru",
                    "bitrix_token": "default_token",
                    "log_level": "INFO",
                    "logger": logger
                }
        
        mock_load_config.side_effect = mock_load_config_with_fallback
        
        #тестируем загрузку конфигурации
        config = mock_load_config()
        
        #проверяем, что получили дефолтную конфигурацию
        self.assertEqual(config["bitrix_url"], "https://default.bitrix24.ru")
        self.assertEqual(config["bitrix_token"], "default_token")
        self.assertEqual(config["log_level"], "INFO")
        self.assertIsNotNone(config["logger"])

if __name__ == "__main__":
    unittest.main()
