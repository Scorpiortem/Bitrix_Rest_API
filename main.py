import argparse
import json
import os
import sys
import logging
from typing import Dict
from data_fetchers import BitrixFetcher
from processors import DataProcessor
from dossier_generator import ReportGenerator
from logger import setup_logger

def load_config(config_path: str) -> Dict:
    # Подгрузка конфига с проверкой на ошибки
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Конфигурационный файл {config_path} не найден")
    
    with open(config_path) as f:
        config = json.load(f)
    
    # Проверка обязательных переменных
    config['bitrix_token'] = os.getenv('BITRIX_TOKEN')
    if not config['bitrix_token']:
        raise ValueError("Переменная окружения BITRIX_TOKEN не установлена")
    
    # Инициализируем логгер
    config['logger'] = setup_logger(config)
    return config

def main():
    # Инициализируем базовый логгер для обработки ошибок до загрузки конфига
    logger = logging.getLogger("deal_dossier")
    logger.setLevel(logging.INFO)
    if not logger.hasHandlers():
        # Добавим консольный обработчик, если ещё нет
        ch = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    parser = argparse.ArgumentParser(
        description="Генератор отчетов по сделкам из Битрикс24",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'deal_id', 
        type=int,
        help="ID сделки в Битрикс24"
    )
    parser.add_argument(
        '-c', '--config',
        default='config.json',
        help="Путь к конфигурационному файлу (по умолчанию: config.json)"
    )
    parser.add_argument(
        '-o', '--output',
        default='reports',
        help="Директория для сохранения отчетов (по умолчанию: reports)"
    )
    parser.add_argument(
        '-f', '--format',
        choices=['json', 'md', 'all'],
        default='all',
        help="Формат отчетов: json, md или all (по умолчанию: all)"
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Подробный вывод логов"
    )
    args = parser.parse_args()

    try:
        # Загрузка конфига и переопределение логгера
        config = load_config(args.config)
        logger = config['logger']

        if args.verbose:
            logger.setLevel('DEBUG')

        logger.info(f"Обработка сделки ID={args.deal_id}")

        logger.debug("Запрос данных из Битрикс24...")
        bitrix_data = BitrixFetcher(config).get_deal_data(args.deal_id)

        logger.debug("Формирование временной линии...")
        processed_data = {
            'deal_id': args.deal_id,
            'timeline': DataProcessor.merge_timeline(bitrix_data),
            'user': bitrix_data.get('user', {}),
            'dialog': bitrix_data.get('dialog_messages', {})
        }

        os.makedirs(args.output, exist_ok=True)
        base_path = f"{args.output}/deal_{args.deal_id}"

        if args.format in ['json', 'all']:
            with open(f"{base_path}.json", 'w', encoding='utf-8') as f:
                f.write(ReportGenerator.generate_json(processed_data))
            logger.info(f"JSON-отчет сохранен: {base_path}.json")

        if args.format in ['md', 'all']:
            with open(f"{base_path}.md", 'w', encoding='utf-8') as f:
                f.write(ReportGenerator.generate_markdown(processed_data))
            logger.info(f"Markdown-отчет сохранен: {base_path}.md")

        logger.info("Обработка завершена успешно")

    except Exception as e:
        logger.error(f"Ошибка: {str(e)}", exc_info=args.verbose)
        sys.exit(1)

if __name__ == "__main__":
    main()
