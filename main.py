import argparse
import os
import sys
import logging
from typing import Dict
from data_fetchers import BitrixFetcher
from processors import DataProcessor
from dossier_generator import ReportGenerator
from logger import setup_logger
from dotenv import load_dotenv
load_dotenv()  #загружаем переменные из .env

def load_config() -> Dict:
    return {
        "bitrix_url": os.getenv("BITRIX_URL"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "log_path": os.getenv("LOG_PATH"),
        "bitrix_token": os.getenv("BITRIX_TOKEN")  #Теперь только из .env
    }

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
        #Загрузка конфига и переопределение логгера
        config = load_config()
        logger = setup_logger(config)

        if args.verbose:
            logger.setLevel('DEBUG')

        logger.info(f"Обработка сделки ID={args.deal_id}")
        
        #Создание выходной директории при необходимости
        os.makedirs(args.output, exist_ok=True)

        logger.debug("Запрос данных из Битрикс24...")
        bitrix_data = BitrixFetcher(config).get_deal_data(args.deal_id)

        logger.debug("Формирование временной линии...")
        processed_data = {
            'deal_id': args.deal_id,
            'timeline': DataProcessor.merge_timeline(bitrix_data),
            'user': bitrix_data.get('user', {}),
            'dialog': bitrix_data.get('dialog_messages', {})
        }
        
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
