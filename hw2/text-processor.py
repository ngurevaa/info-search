import os
import re
from bs4 import BeautifulSoup
import pymorphy3
from nltk.corpus import stopwords
import nltk

class TextProcessor:
    """Класс для обработки текста: токенизация и лемматизация"""
    def __init__(self, pages_dir='../hw1/pages', output_dir='.'):
        self.pages_dir = pages_dir
        self.output_dir = output_dir
        self.tokens_dir = os.path.join(output_dir, 'tokens')
        self.lemmas_dir = os.path.join(output_dir, 'lemmas')

        os.makedirs(self.tokens_dir, exist_ok=True)
        os.makedirs(self.lemmas_dir, exist_ok=True)

        # Загружаем стоп-слова (предлоги, союзы и т.д.)
        nltk.download('stopwords', quiet=True)
        self.stop_words = set(stopwords.words('russian'))

        # Инициализируем лемматизатор
        self.morph = pymorphy3.MorphAnalyzer()

    def extract_text_from_html(self, html_content):
        """Извлекает чистый текст из HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')

        # Удаляем скрипты, стили и другие ненужные элементы
        for script in soup(['script', 'style', 'meta', 'link']):
            script.decompose()

        # Получаем текст
        text = soup.get_text()

        # Очищаем от лишних пробелов и переносов
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        return text

    def tokenize(self, text):
        """Разбивает текст на токены и очищает от мусора"""
        # Регулярное выражение для поиска слов (только буквы, минимум 2 символа)
        words = re.findall(r'\b[а-яА-ЯёЁ]{2,}\b', text.lower())

        # Фильтрация
        clean_words = []
        for word in words:
            # Пропускаем стоп-слова (предлоги, союзы)
            if word in self.stop_words:
                continue
            # Пропускаем слишком короткие
            if len(word) < 2:
                continue
            clean_words.append(word)

        return clean_words

    def lemmatize_words(self, words):
        """Группирует слова по леммам"""
        lemma_dict = {}

        for word in words:
            # Получаем нормальную форму (лемму)
            lemma = self.morph.parse(word)[0].normal_form
            lemma_dict.setdefault(lemma, set()).add(word)

        # Преобразуем множества в списки для сортировки
        result = {}
        for lemma, tokens in lemma_dict.items():
            result[lemma] = sorted(list(tokens))

        return result

    def get_html_files(self):
        """Возвращает список всех HTML-файлов в папке ../hw1/pages"""
        html_files = []
        for file in os.listdir(self.pages_dir):
            if file.endswith('.html'):
                html_files.append(os.path.join(self.pages_dir, file))

        html_files.sort()
        return html_files

    def get_page_number(self, file_path):
        """Извлекает номер страницы из имени файла"""
        basename = os.path.basename(file_path)
        return os.path.splitext(basename)[0]

    def process_file(self, html_file_path):
        """Обрабатывает один HTML-файл: возвращает токены и леммы"""
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        text = self.extract_text_from_html(html_content)
        tokens = self.tokenize(text)

        # Убираем дубликаты
        unique_tokens = []
        seen = set()
        for token in tokens:
            if token not in seen:
                seen.add(token)
                unique_tokens.append(token)

        lemmas = self.lemmatize_words(tokens)

        return unique_tokens, lemmas

    def save_tokens(self, tokens, output_file):
        """Сохраняет токены в файл"""
        with open(output_file, 'w', encoding='utf-8') as f:
            for token in tokens:
                f.write(f"{token}\n")

    def save_lemmas(self, lemmas, output_file):
        """Сохраняет леммы в файл (лемма + токены через пробел)"""
        with open(output_file, 'w', encoding='utf-8') as f:
            # Сортируем леммы по алфавиту
            for lemma, words in sorted(lemmas.items()):
                f.write(f"{lemma} {' '.join(words)}\n")

    def process_all_pages(self):
        """Обрабатывает все HTML-файлы"""
        html_files = self.get_html_files()

        print(f"Найдено HTML-файлов: {len(html_files)}")
        print("Начинаем обработку...")

        total_tokens = 0

        for html_file in html_files:
            # Получаем номер страницы
            page_num = self.get_page_number(html_file)

            # Обрабатываем файл
            tokens, lemmas = self.process_file(html_file)

            # Сохраняем результаты
            tokens_file = os.path.join(self.tokens_dir, f"{page_num}.txt")
            lemmas_file = os.path.join(self.lemmas_dir, f"{page_num}.txt")

            self.save_tokens(tokens, tokens_file)
            self.save_lemmas(lemmas, lemmas_file)

            # Статистика
            total_tokens += len(tokens)

            print(f"✓ {page_num}: {len(tokens)} токенов, {len(lemmas)} лемм")

        print(f"\nОбработка завершена!")
        print(f"Всего уникальных токенов (по всем страницам): {total_tokens}")

def main():
    processor = TextProcessor()
    processor.process_all_pages()

if __name__ == "__main__":
    main()