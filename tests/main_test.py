import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
from main import load_config, main

class TestLoadConfig(unittest.TestCase):
    @patch("main.setup_logger")
    @patch("os.getenv", return_value="test_token")
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data='{"bitrix_url": "https://test"}')
    def test_load_config_success(self, mock_file, mock_exists, mock_getenv, mock_setup_logger):
        mock_logger = MagicMock()
        mock_setup_logger.return_value = mock_logger

        config = load_config("config.json")

        mock_exists.assert_called_once_with("config.json")
        mock_file.assert_called_once_with("config.json")
        mock_getenv.assert_called_once_with("BITRIX_TOKEN")
        mock_setup_logger.assert_called_once()
        self.assertEqual(config["bitrix_token"], "test_token")
        self.assertEqual(config["logger"], mock_logger)
        self.assertEqual(config["bitrix_url"], "https://test")

    @patch("os.path.exists", return_value=False)
    def test_load_config_file_not_found(self, mock_exists):
        with self.assertRaises(FileNotFoundError):
            load_config("missing.json")
        mock_exists.assert_called_once_with("missing.json")

    @patch("os.getenv", return_value=None)
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data='{}')
    def test_load_config_missing_env_token(self, _mock_file, _mock_exists, mock_getenv):
        with self.assertRaises(ValueError):
            load_config("config.json")
        mock_getenv.assert_called_once_with("BITRIX_TOKEN")

class TestMainFunction(unittest.TestCase):
    @patch("sys.exit")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    @patch("main.load_config")
    @patch("main.BitrixFetcher")
    @patch("main.DataProcessor.merge_timeline", return_value=[{"date": "2025-06-10"}])
    @patch("main.ReportGenerator.generate_json", return_value='{"json": "report"}')
    @patch("main.ReportGenerator.generate_markdown", return_value="md_report")
    def test_main_all_formats(self, mock_generate_markdown, mock_generate_json, _mock_merge_timeline,
                              mock_bitrix_fetcher_cls, mock_load_config, mock_makedirs,
                              mock_open_file, mock_exit):
        #Подготовка мока для BitrixFetcher().get_deal_data()
        mock_bitrix_instance = MagicMock()
        mock_bitrix_instance.get_deal_data.return_value = {
            "user": {"ID": 1},
            "dialog_messages": {"messages": []}
        }
        mock_bitrix_fetcher_cls.return_value = mock_bitrix_instance

        mock_logger = MagicMock()
        mock_load_config.return_value = {
            "logger": mock_logger
        }

        test_args = ["main.py", "123", "-f", "all", "-o", "outdir"]
        with patch.object(sys, 'argv', test_args):
            main()

        #проверяем, что создается директория для отчетов
        mock_makedirs.assert_called_once_with("outdir", exist_ok=True)

        #проверяем, что BitrixFetcher вызван с конфигом
        mock_bitrix_fetcher_cls.assert_called_once_with(mock_load_config.return_value)

        #проверяем вызовы генерации отчетов
        mock_generate_json.assert_called_once()
        mock_generate_markdown.assert_called_once()

        #проверяем, что файлы открываются для записи
        expected_json_path = "outdir/deal_123.json"
        expected_md_path = "outdir/deal_123.md"
        mock_open_file.assert_any_call(expected_json_path, 'w', encoding='utf-8')
        mock_open_file.assert_any_call(expected_md_path, 'w', encoding='utf-8')

        #проверяем, что логи пишутся
        mock_logger.info.assert_any_call("JSON-отчет сохранен: outdir/deal_123.json")
        mock_logger.info.assert_any_call("Markdown-отчет сохранен: outdir/deal_123.md")
        mock_logger.info.assert_any_call("Обработка завершена успешно")

        #убедимся, что sys.exit не вызван (успешное завершение)
        mock_exit.assert_not_called()

    @patch("sys.exit")
    @patch("main.load_config")
    @patch("logging.getLogger")
    def test_main_exception_handling(self, mock_get_logger, mock_load_config, mock_exit):
        #мок базового логгера, который используется при ошибках
        mock_base_logger = MagicMock()
        mock_get_logger.return_value = mock_base_logger
        
        #эмулируем ошибку при загрузке конфига
        mock_load_config.side_effect = Exception("Test error")

        test_args = ["main.py", "123"]
        with patch.object(sys, 'argv', test_args):
            main()

        #проверяем вызов error в БАЗОВОМ логгере
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
                                           _mock_merge_timeline, _mock_generate_json,
                                           _mock_generate_markdown, _mock_makedirs, _mock_open_file):
        #создаем мок логгера из конфига
        mock_config_logger = MagicMock()
        mock_load_config.return_value = {"logger": mock_config_logger}

        mock_bitrix_instance = MagicMock()
        mock_bitrix_instance.get_deal_data.return_value = {}
        mock_bitrix_fetcher_cls.return_value = mock_bitrix_instance

        test_args = ["main.py", "123", "-v"]
        with patch.object(sys, 'argv', test_args):
            main()

        #проверяем установку уровня для логгера из конфига
        mock_config_logger.setLevel.assert_called_once_with('DEBUG')

if __name__ == "__main__":
    unittest.main()
