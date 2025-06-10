import unittest
import logging
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path
import os
from logger import setup_logger

class TestSetupLogger(unittest.TestCase):

    @patch("logger_test.logging.getLogger")
    @patch("logger_test.Path.mkdir")
    @patch("logger_test.logging.StreamHandler")
    @patch("logger_test.logging.FileHandler")
    def test_logger_with_log_path(self, mock_file_handler_cls, mock_stream_handler_cls, mock_mkdir, mock_get_logger):
        #моки для логгера и хендлеров
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_stream_handler = MagicMock()
        mock_file_handler = MagicMock()
        mock_stream_handler_cls.return_value = mock_stream_handler
        mock_file_handler_cls.return_value = mock_file_handler

        config = {
            "log_level": "DEBUG",
            "log_path": "./logs"
        }

        logger = setup_logger(config)

        #проверяем, что getLogger вызван с правильным именем
        mock_get_logger.assert_called_once_with("deal_dossier")

        #проверяем установку уровня логирования
        self.assertEqual(mock_logger.setLevel.call_args[0][0], "DEBUG")

        #проверяем создание директории для логов
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

        #проверяем создание и добавление StreamHandler
        mock_stream_handler_cls.assert_called_once_with(sys.stdout)
        mock_logger.addHandler.assert_any_call(mock_stream_handler)

        #проверяем создание и добавление FileHandler
        mock_file_handler_cls.assert_called_once_with(Path(config["log_path"]) / "app.log")
        mock_logger.addHandler.assert_any_call(mock_file_handler)

        #проверяем, что возвращается объект логгера
        self.assertEqual(logger, mock_logger)

    @patch("logger_test.logging.getLogger")
    @patch("logger_test.logging.StreamHandler")
    def test_logger_without_log_path(self, mock_stream_handler_cls, mock_get_logger):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_stream_handler = MagicMock()
        mock_stream_handler_cls.return_value = mock_stream_handler

        config = {
            "log_level": "WARNING"
            #log_path отсутствует
        }

        logger = setup_logger(config)

        mock_get_logger.assert_called_once_with("deal_dossier")
        self.assertEqual(mock_logger.setLevel.call_args[0][0], "WARNING")

        mock_stream_handler_cls.assert_called_once_with(sys.stdout)
        mock_logger.addHandler.assert_called_once_with(mock_stream_handler)

        #убедимся, что mkdir и FileHandler не вызываются
        self.assertEqual(mock_logger.addHandler.call_count, 1)

        self.assertEqual(logger, mock_logger)

    def test_logger_default_log_level(self):
        #проверка, что по умолчанию уровень INFO
        config = {}
        logger = setup_logger(config)
        self.assertEqual(logger.level, logging.INFO)

    def test_logger_creates_log_directory(self):
        test_dir = "test_logs_dir"
        if os.path.exists(test_dir):
            import shutil
            shutil.rmtree(test_dir, ignore_errors=True)  #игнорировать ошибки при удалении

        config = {"log_path": test_dir}
        logger = setup_logger(config)

        self.assertTrue(os.path.isdir(test_dir))

        #закрываем все хендлеры логгера
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

        #очистка после теста
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)  #игнорировать ошибки

if __name__ == "__main__":
    unittest.main()
