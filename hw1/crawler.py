import os
import requests
from urllib.parse import urlparse
import time

class TextPageCrawler:
    def __init__(self, output_dir="pages"):
        self.output_dir = output_dir
        self.index_file = "index.txt"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; MyBot/1.0; +https://example.com/bot-info)',
        })

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def is_valid_text_page(self, url):
        """Проверяет, что URL ведет на текстовую страницу, а не на файл"""
        excluded_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',
                               '.css', '.js', '.pdf', '.doc', '.docx', '.zip',
                               '.mp3', '.mp4', '.avi', '.exe']

        url_lower = url.lower()
        for ext in excluded_extensions:
            if ext in url_lower:
                return False

        parsed = urlparse(url)
        return parsed.scheme in ['http', 'https']

    def download_page(self, url, page_number):
        """Скачивает страницу и сохраняет в файл"""
        for attempt in range(10):
            response = self.session.get(url, timeout=10)

            if response.status_code == 403 or response.status_code == 429:
                print(f"Получен код {response.status_code}. Ожидание 60 секунд...")
                time.sleep(60)
                continue

            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type.lower():
                return None

            filename = f"page_{page_number:03d}.html"
            filepath = os.path.join(self.output_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)

            self.add_to_index(page_number, url)

            print(f"Загружена страница {page_number}: {filename}")
            time.sleep(10)
            return filepath
        return None

    def add_to_index(self, page_number, url):
        with open(self.index_file, 'a', encoding='utf-8') as f:
            f.write(f"page_{page_number:03d}.html | {url}\n")

    def crawl(self, urls):
        """Основной метод краулинга"""
        print(f"Начинаем краулинг.")

        with open(self.index_file, 'w', encoding='utf-8') as f:
            f.write("# имя_файла | URL\n")

        downloaded = 0
        processed_urls = set()

        for url in urls:
            url = url.strip()
            if not url or url in processed_urls:
                continue

            if not self.is_valid_text_page(url):
                print(f"Пропущен (не текстовая страница): {url}")
                continue

            print(f"Обработка URL {downloaded + 1}/{len(urls)}: {url}")
            processed_urls.add(url)

            result = self.download_page(url, downloaded + 1)
            if result:
                downloaded += 1

        print(f"\n Краулинг завершен. Скачано страниц: {downloaded}")
        print(f" Файлы сохранены в папке: {self.output_dir}")
        print(f" Индекс сохранен в: {self.index_file}")

        return downloaded


def get_url_list():
    """Возвращает список URL для краулинга (100+ страниц Википедии на русском)"""
    return [
        # ========== ТЕМА 1: ИСТОРИЧЕСКИЕ ЛИЧНОСТИ (20) ==========
        # Древняя Русь
        "https://ru.wikipedia.org/wiki/Александр_Невский",
        "https://ru.wikipedia.org/wiki/Олег_Вещий",
        "https://ru.wikipedia.org/wiki/Игорь_Рюрикович",
        "https://ru.wikipedia.org/wiki/Княгиня_Ольга",
        "https://ru.wikipedia.org/wiki/Святослав_Игоревич",
        "https://ru.wikipedia.org/wiki/Владимир_Святославич",
        "https://ru.wikipedia.org/wiki/Ярослав_Мудрый",
        "https://ru.wikipedia.org/wiki/Владимир_Мономах",
        "https://ru.wikipedia.org/wiki/Юрий_Долгорукий",
        "https://ru.wikipedia.org/wiki/Андрей_Боголюбский",
        "https://ru.wikipedia.org/wiki/Рюрик",
        "https://ru.wikipedia.org/wiki/Дмитрий_Донской",

        # Цари и императоры
        "https://ru.wikipedia.org/wiki/Иван_Грозный",
        "https://ru.wikipedia.org/wiki/Борис_Годунов",
        "https://ru.wikipedia.org/wiki/Михаил_Фёдорович",
        "https://ru.wikipedia.org/wiki/Алексей_Михайлович",
        "https://ru.wikipedia.org/wiki/Пётр_I",
        "https://ru.wikipedia.org/wiki/Екатерина_I",
        "https://ru.wikipedia.org/wiki/Анна_Иоанновна",
        "https://ru.wikipedia.org/wiki/Елизавета_Петровна",
        "https://ru.wikipedia.org/wiki/Екатерина_II",
        "https://ru.wikipedia.org/wiki/Павел_I",
        "https://ru.wikipedia.org/wiki/Александр_I",
        "https://ru.wikipedia.org/wiki/Николай_I",
        "https://ru.wikipedia.org/wiki/Александр_II",
        "https://ru.wikipedia.org/wiki/Александр_III",
        "https://ru.wikipedia.org/wiki/Николай_II",

        # ========== ТЕМА 2: ГОРОДА РОССИИ (25) ==========
        "https://ru.wikipedia.org/wiki/Москва",
        "https://ru.wikipedia.org/wiki/Санкт-Петербург",
        "https://ru.wikipedia.org/wiki/Великий_Новгород",
        "https://ru.wikipedia.org/wiki/Псков",
        "https://ru.wikipedia.org/wiki/Смоленск",
        "https://ru.wikipedia.org/wiki/Казань",
        "https://ru.wikipedia.org/wiki/Нижний_Новгород",
        "https://ru.wikipedia.org/wiki/Чебоксары",
        "https://ru.wikipedia.org/wiki/Суздаль",
        "https://ru.wikipedia.org/wiki/Ярославль",
        "https://ru.wikipedia.org/wiki/Кострома",
        "https://ru.wikipedia.org/wiki/Севастополь",
        "https://ru.wikipedia.org/wiki/Калининград",
        "https://ru.wikipedia.org/wiki/Екатеринбург",
        "https://ru.wikipedia.org/wiki/Новосибирск",
        "https://ru.wikipedia.org/wiki/Владивосток",
        "https://ru.wikipedia.org/wiki/Сергиев_Посад",
        "https://ru.wikipedia.org/wiki/Ростов_Великий",
        "https://ru.wikipedia.org/wiki/Переславль-Залесский",
        "https://ru.wikipedia.org/wiki/Муром",
        "https://ru.wikipedia.org/wiki/Коломна",
        "https://ru.wikipedia.org/wiki/Тула",
        "https://ru.wikipedia.org/wiki/Рязань",
        "https://ru.wikipedia.org/wiki/Воронеж",
        "https://ru.wikipedia.org/wiki/Красноярск",
        "https://ru.wikipedia.org/wiki/Иркутск",
        "https://ru.wikipedia.org/wiki/Тобольск",
        "https://ru.wikipedia.org/wiki/Архангельск",
        "https://ru.wikipedia.org/wiki/Мурманск",

        # ========== ТЕМА 3: ВОЙНЫ И СРАЖЕНИЯ (20) ==========
        "https://ru.wikipedia.org/wiki/Ледовое_побоище",
        "https://ru.wikipedia.org/wiki/Куликовская_битва",
        "https://ru.wikipedia.org/wiki/Полтавская_битва",
        "https://ru.wikipedia.org/wiki/Бородинское_сражение",
        "https://ru.wikipedia.org/wiki/Отечественная_война_1812_года",
        "https://ru.wikipedia.org/wiki/Крымская_война",
        "https://ru.wikipedia.org/wiki/Оборона_Севастополя_(1854—1855)",
        "https://ru.wikipedia.org/wiki/Русско-турецкая_война_1877—1878_годов",
        "https://ru.wikipedia.org/wiki/Русско-японская_война",
        "https://ru.wikipedia.org/wiki/Первая_мировая_война",
        "https://ru.wikipedia.org/wiki/Брусиловский_прорыв",
        "https://ru.wikipedia.org/wiki/Гражданская_война_в_России",
        "https://ru.wikipedia.org/wiki/Великая_Отечественная_война",
        "https://ru.wikipedia.org/wiki/Битва_за_Москву",
        "https://ru.wikipedia.org/wiki/Сталинградская_битва",
        "https://ru.wikipedia.org/wiki/Курская_битва",
        "https://ru.wikipedia.org/wiki/Блокада_Ленинграда",
        "https://ru.wikipedia.org/wiki/Битва_за_Берлин",
        "https://ru.wikipedia.org/wiki/Афганская_война_(1979—1989)",
        "https://ru.wikipedia.org/wiki/Чеченская_война",

        # ========== ТЕМА 4: КУЛЬТУРА И ИСКУССТВО (20) ==========
        # Писатели и поэты
        "https://ru.wikipedia.org/wiki/Александр_Пушкин",
        "https://ru.wikipedia.org/wiki/Михаил_Лермонтов",
        "https://ru.wikipedia.org/wiki/Николай_Гоголь",
        "https://ru.wikipedia.org/wiki/Фёдор_Достоевский",
        "https://ru.wikipedia.org/wiki/Лев_Толстой",
        "https://ru.wikipedia.org/wiki/Антон_Чехов",
        "https://ru.wikipedia.org/wiki/Иван_Тургенев",
        "https://ru.wikipedia.org/wiki/Михаил_Булгаков",
        "https://ru.wikipedia.org/wiki/Анна_Ахматова",
        "https://ru.wikipedia.org/wiki/Марина_Цветаева",
        "https://ru.wikipedia.org/wiki/Сергей_Есенин",
        "https://ru.wikipedia.org/wiki/Владимир_Маяковский",
        "https://ru.wikipedia.org/wiki/Борис_Пастернак",
        "https://ru.wikipedia.org/wiki/Иосиф_Бродский",
        "https://ru.wikipedia.org/wiki/Александр_Солженицын",

        # Композиторы
        "https://ru.wikipedia.org/wiki/Пётр_Чайковский",
        "https://ru.wikipedia.org/wiki/Михаил_Глинка",
        "https://ru.wikipedia.org/wiki/Сергей_Рахманинов",
        "https://ru.wikipedia.org/wiki/Игорь_Стравинский",
        "https://ru.wikipedia.org/wiki/Дмитрий_Шостакович",
        "https://ru.wikipedia.org/wiki/Сергей_Прокофьев",
        "https://ru.wikipedia.org/wiki/Николай_Римский-Корсаков",
        "https://ru.wikipedia.org/wiki/Модест_Мусоргский",
        "https://ru.wikipedia.org/wiki/Александр_Бородин",

        # Художники
        "https://ru.wikipedia.org/wiki/Андрей_Рублёв",
        "https://ru.wikipedia.org/wiki/Илья_Репин",
        "https://ru.wikipedia.org/wiki/Иван_Айвазовский",
        "https://ru.wikipedia.org/wiki/Виктор_Васнецов",
        "https://ru.wikipedia.org/wiki/Михаил_Врубель",
        "https://ru.wikipedia.org/wiki/Василий_Суриков",
        "https://ru.wikipedia.org/wiki/Валентин_Серов",
        "https://ru.wikipedia.org/wiki/Исаак_Левитан",
        "https://ru.wikipedia.org/wiki/Кузьма_Петров-Водкин",
        "https://ru.wikipedia.org/wiki/Казимир_Малевич",
        "https://ru.wikipedia.org/wiki/Василий_Кандинский",
        "https://ru.wikipedia.org/wiki/Марк_Шагал",

        # ========== ТЕМА 5: АРХИТЕКТУРА И ДОСТОПРИМЕЧАТЕЛЬНОСТИ (15) ==========
        "https://ru.wikipedia.org/wiki/Московский_Кремль",
        "https://ru.wikipedia.org/wiki/Эрмитаж",
        "https://ru.wikipedia.org/wiki/Третьяковская_галерея",
        "https://ru.wikipedia.org/wiki/Большой_театр",
        "https://ru.wikipedia.org/wiki/Мариинский_театр",
        "https://ru.wikipedia.org/wiki/Исаакиевский_собор",
        "https://ru.wikipedia.org/wiki/Храм_Василия_Блаженного",
        "https://ru.wikipedia.org/wiki/Храм_Христа_Спасителя",
        "https://ru.wikipedia.org/wiki/Кижи",
        "https://ru.wikipedia.org/wiki/Соловецкие_острова",
        "https://ru.wikipedia.org/wiki/Валаам",
        "https://ru.wikipedia.org/wiki/Троице-Сергиева_лавра",
        "https://ru.wikipedia.org/wiki/Петергоф",
        "https://ru.wikipedia.org/wiki/Царское_Село",
        "https://ru.wikipedia.org/wiki/Нижегородский_кремль",
        "https://ru.wikipedia.org/wiki/Казанский_кремль",
        "https://ru.wikipedia.org/wiki/Астраханский_кремль",
        "https://ru.wikipedia.org/wiki/Новодевичий_монастырь",
        "https://ru.wikipedia.org/wiki/Донской_монастырь",
        "https://ru.wikipedia.org/wiki/Золотые_ворота_(Владимир)",
        "https://ru.wikipedia.org/wiki/Софийский_собор_(Великий_Новгород)",
    ]


def main():
    urls = get_url_list()
    print(f"Подготовлено URL для краулинга: {len(urls)}")

    crawler = TextPageCrawler()
    downloaded = crawler.crawl(urls)

    print(f"\nСкачано {downloaded} страниц.")

if __name__ == "__main__":
    main()