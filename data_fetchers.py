import requests
from typing import Dict, Any, List, Optional
import time

class BaseFetcher:
    def __init__(self, config: Dict[str, Any]):
        #Проходит инициализация базовых параметров для всех API-клиентов
        self.config = config
        self.logger = config.get("logger")  #Логгер из конфигурации
        self.session = requests.Session()  #Общая сессия для запросов
        self.session.headers.update({"User-Agent": "DealDossier/1.0"})  #Заголовок User-Agent

    def _handle_pagination(self, url: str, params: Dict, max_pages: int = 100) -> List[Dict]:
        """Обработка пагинации API с ограничением максимального числа страниц"""
        results = []
        start = 0  # Смещение для пагинации
        page_count = 0  #Счетчик обработанных страниц
        
        while True:
            # Защита от бесконечного цикла
            if page_count >= max_pages:
                self.logger.warning(f"Достигнут лимит пагинации ({max_pages} страниц)")
                break
            
            try:
                params["start"] = start
                response = self.session.get(url, params=params)
                response.raise_for_status()  #Проверка на HTTP-ошибки
                data = response.json()
                
                #Логирование для отладки
                self.logger.debug(f"Пагинация: start={start}, получено {len(data.get('result', []))} элементов")
                
                #Прерываем, если данных нет
                if not data.get("result"):
                    break
                
                #Сбор результатов
                results.extend(data["result"])
                start += len(data["result"])  #Увеличиваем смещение
                page_count += 1

                #Остановка, если достигнут общий объем данных
                if "total" in data and start >= data["total"]:
                    break

                #Задержка для соблюдения лимитов API
                time.sleep(0.3)
                
            except Exception as e:
                self.logger.error(f"Ошибка пагинации: {str(e)}")
                break
        
        return results
    

class BitrixFetcher(BaseFetcher):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        #Формирование базового URL для Битрикс 24 REST API
        self.base_url = f"{config['bitrix_url']}/rest/1/{config['bitrix_token']}/"
        self.session.params = {}  #Сброс параметров по умолчанию

    #Здесь представлен основной метод для получения данных о сделке
    def get_deal_data(self, deal_id: int) -> Dict:
        #Сначала вызываются базовые методы API, потом зависимые
        methods_order = [
            ("deal", "crm.deal.get"),         #Основные данные сделки
            ("contact", "crm.contact.get"),   #Данные контакта
            ("user", "user.get"),             #Информация об ответственном
            ("timeline", "crm.timeline.comment.list"),  #Комментарии
            ("activities", "crm.activity.list"),        #Активности
            ("dialog_messages", "im.dialog.messages.get"),  #Сообщения чата
            ("openline_dialog", "imopenlines.dialog.get")   #Данные диалога
        ]

        data = {}
        try:
            #Первый шаг. Получение базовых данных (сделка и контакт)
            for key, method in methods_order[:2]:
                url = f"{self.base_url}{method}"
                response = self.session.get(url, params={"id": deal_id})
                response.raise_for_status()
                data[key] = response.json().get("result", {})

            #Второй шаг. Получение зависимых данных
            for key, method in methods_order[2:]:
                url = f"{self.base_url}{method}"
                params = {}
                
                #Обработка данных пользователя(ответственное лицо)
                if method == "user.get":
                    user_id = data["deal"].get("ASSIGNED_BY_ID")
                    if not user_id:
                        data[key] = {"error": "Ответственный не указан"}
                        continue
                    #Выборка конкретных полей пользователя
                    params = {
                        "id": user_id,
                        "select": ["ID", "NAME", "LAST_NAME", "EMAIL", "WORK_POSITION"]
                    }

                #Обработка диалогов
                elif method in ["im.dialog.messages.get", "imopenlines.dialog.get"]:
                    dialog_id = self._get_dialog_id(deal_id)
                    
                    #Валидация ID диалога
                    if not dialog_id or dialog_id == "0":
                        data[key] = {"info": "Диалог отсутствует"}
                        continue
                    
                    params = {"DIALOG_ID": dialog_id}
                    if method == "im.dialog.messages.get":
                        params["LIMIT"] = 200  #Лимит поставил 200 для сообщений

                #Выполнение запроса
                response = self.session.get(url, params=params)
                response.raise_for_status()
                data[key] = response.json().get("result", {})

        except Exception as e:
            self.logger.error(f"Ошибка: {str(e)}")
            data["error"] = str(e)

        return data

    def _get_dialog_id(self, deal_id: int) -> Optional[str]:
        #Поиск ID диалога через активность 'Открытая линия'
        try:
            url = f"{self.base_url}crm.activity.list"
            #Фильтр для активности типа "Чат открытой линии"
            params = {
                "filter[OWNER_ID]": deal_id,
                "filter[PROVIDER_ID]": "IMOPENLINES_SESSION",
                "select": ["ASSOCIATED_ENTITY_ID"]
            }
            response = self.session.get(url, params=params)
            response.raise_for_status()
            activities = response.json().get("result", [])
            
            #Собственно, проверка на наличие активностей
            if not activities:
                return None
                
            #Извлечение и проверка ID диалога    
            dialog_id = str(activities[0].get("ASSOCIATED_ENTITY_ID", ""))
            return dialog_id if dialog_id and dialog_id != "0" else None
            
        except Exception as e:
            self.logger.error(f"Ошибка получения диалога: {str(e)}")
            return None