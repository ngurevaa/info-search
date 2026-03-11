import os
import re
import math
import json
from collections import defaultdict, Counter
import pymorphy3

class IndexBuilder:
    """Класс для построения векторного индекса из TF-IDF файлов"""

    def __init__(self,
                 tfidf_terms_dir='../hw4/tfidf_results/terms',
                 tfidf_lemmas_dir='../hw4/tfidf_results/lemmas',
                 pages_dir='../hw1/pages',
                 index_file='vector_index.json'):

        self.tfidf_terms_dir = tfidf_terms_dir
        self.tfidf_lemmas_dir = tfidf_lemmas_dir
        self.pages_dir = pages_dir
        self.index_file = index_file

        self.morph = pymorphy3.MorphAnalyzer()

        # Данные для поиска
        self.doc_vectors = {}  # doc_id -> вектор (словарь терм->tfidf)
        self.doc_norms = {}  # doc_id -> норма вектора
        self.doc_titles = {}  # doc_id -> название страницы
        self.doc_files = {}  # doc_id -> имя файла
        self.all_terms = set()  # все термины в индексе

        # Для быстрого доступа
        self.term_to_docs = defaultdict(set)  # терм -> список doc_id

    def extract_page_number(self, filename):
        """Извлекает номер страницы из имени файла"""
        match = re.search(r'page_(\d+)', filename)
        if match:
            return int(match.group(1))
        return None

    def load_tfidf_file(self, filepath, doc_id):
        """Загружает TF-IDF файл и строит вектор документа"""
        vector = {}

        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 3:
                    term = parts[0]
                    tfidf = float(parts[2])

                    vector[term] = tfidf
                    self.all_terms.add(term)
                    self.term_to_docs[term].add(doc_id)

        return vector

    def extract_title_from_html(self, html_file):
        """Извлекает название страницы из HTML файла"""
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
            if title_match:
                title = title_match.group(1)
                title = re.sub(r'[-–—]\s*Википедия.*$', '', title).strip()
                return title
        except:
            pass
        return os.path.basename(html_file)

    def calculate_norm(self, vector):
        """Считает норму вектора"""
        return math.sqrt(sum(val ** 2 for val in vector.values()))

    def build(self):
        """Строит индекс из TF-IDF файлов"""
        print("Построение векторного индекса...")

        # Получаем все TF-IDF файлы для терминов
        term_files = [f for f in os.listdir(self.tfidf_terms_dir) if f.endswith('.txt')]
        term_files.sort()

        print(f"Найдено файлов: {len(term_files)}")

        for filename in term_files:
            page_num = self.extract_page_number(filename)
            if page_num is None:
                continue

            doc_id = page_num

            # Загружаем вектор для терминов
            term_path = os.path.join(self.tfidf_terms_dir, filename)
            term_vector = self.load_tfidf_file(term_path, doc_id)

            # Загружаем вектор для лемм (если есть)
            lemma_path = os.path.join(self.tfidf_lemmas_dir, filename)
            if os.path.exists(lemma_path):
                lemma_vector = self.load_tfidf_file(lemma_path, doc_id)
                # Объединяем векторы - берем сумму значений
                for lemma, val in lemma_vector.items():
                    if lemma in term_vector:
                        term_vector[lemma] = max(term_vector[lemma], val)
                    else:
                        term_vector[lemma] = val

            self.doc_vectors[doc_id] = term_vector

            # Сохраняем информацию о документе
            self.doc_files[doc_id] = filename

            # Пытаемся получить название из HTML
            html_filename = filename.replace('.txt', '.html')
            html_path = os.path.join(self.pages_dir, html_filename)
            self.doc_titles[doc_id] = self.extract_title_from_html(html_path)

            # Считаем норму вектора
            self.doc_norms[doc_id] = self.calculate_norm(self.doc_vectors[doc_id])

        print(f"Индекс построен. Документов: {len(self.doc_vectors)}")
        print(f"Уникальных терминов: {len(self.all_terms)}")

        # Сохраняем индекс
        self.save_index()
        return True

    def save_index(self):
        """Сохраняет индекс в файл"""
        # Преобразуем для JSON
        index_data = {
            'doc_vectors': {str(k): v for k, v in self.doc_vectors.items()},
            'doc_norms': {str(k): v for k, v in self.doc_norms.items()},
            'doc_titles': {str(k): v for k, v in self.doc_titles.items()},
            'doc_files': {str(k): v for k, v in self.doc_files.items()},
            'all_terms': list(self.all_terms),
            'term_to_docs': {k: list(v) for k, v in self.term_to_docs.items()}
        }

        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

        print(f"Индекс сохранен в {self.index_file}")


def main():
    builder = IndexBuilder()
    builder.build()


if __name__ == "__main__":
    main()