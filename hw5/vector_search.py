import os
import re
import math
import json
from collections import defaultdict
import pymorphy3
from index_builder import IndexBuilder

class VectorSearchEngine:
    """Класс для поиска по векторному индексу"""

    def __init__(self, index_file='vector_index.json'):
        self.index_file = index_file
        self.morph = pymorphy3.MorphAnalyzer()

        # Данные будут загружены из индекса
        self.doc_vectors = {}
        self.doc_norms = {}
        self.doc_titles = {}
        self.doc_files = {}
        self.all_terms = set()
        self.term_to_docs = defaultdict(set)

    def load_index(self):
        """Загружает индекс из файла"""
        if not os.path.exists(self.index_file):
            return False

        with open(self.index_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.doc_vectors = {int(k): v for k, v in data['doc_vectors'].items()}
        self.doc_norms = {int(k): v for k, v in data['doc_norms'].items()}
        self.doc_titles = {int(k): v for k, v in data['doc_titles'].items()}
        self.doc_files = {int(k): v for k, v in data['doc_files'].items()}
        self.all_terms = set(data['all_terms'])
        self.term_to_docs = {k: set(v) for k, v in data['term_to_docs'].items()}

        print(f"Индекс загружен. Документов: {len(self.doc_vectors)}")
        return True

    def preprocess_query(self, query):
        """Обрабатывает запрос: токенизация и лемматизация"""
        # Простая токенизация
        words = re.findall(r'\b[а-яА-ЯёЁa-zA-Z]+\b', query.lower())

        # Лемматизация
        lemmas = []
        for word in words:
            lemma = self.morph.parse(word)[0].normal_form
            lemmas.append(lemma)

        return lemmas

    def calculate_norm(self, vector):
        """Считает норму вектора"""
        return math.sqrt(sum(val ** 2 for val in vector.values()))

    def query_to_vector(self, query_terms):
        """Преобразует запрос в TF-IDF вектор"""
        # Считаем частоту терминов в запросе
        term_freq = {}
        for term in query_terms:
            term_freq[term] = term_freq.get(term, 0) + 1

        total_terms = len(query_terms)

        if total_terms == 0:
            return {}

        # Строим вектор запроса
        query_vector = {}
        for term, freq in term_freq.items():
            # TF для запроса
            tf = freq / total_terms

            # IDF берем из индекса (сглаживание)
            doc_count = len(self.term_to_docs.get(term, []))
            idf = math.log((len(self.doc_vectors) + 1) / (doc_count + 1)) + 1

            # TF-IDF для запроса
            query_vector[term] = tf * idf

        return query_vector

    def cosine_similarity(self, query_vector, doc_id):
        """Считает косинусное сходство между запросом и документом"""
        doc_vector = self.doc_vectors[doc_id]

        # Скалярное произведение
        dot_product = 0
        for term, q_val in query_vector.items():
            if term in doc_vector:
                dot_product += q_val * doc_vector[term]

        # Нормы
        query_norm = self.calculate_norm(query_vector)
        doc_norm = self.doc_norms[doc_id]

        if query_norm == 0 or doc_norm == 0:
            return 0

        return dot_product / (query_norm * doc_norm)

    def search(self, query, top_k=10):
        """Выполняет поиск по запросу"""
        print(f"\nЗапрос: {query}")

        query_terms = self.preprocess_query(query)
        if not query_terms:
            print("Пустой запрос")
            return []

        print(f"Термы запроса: {query_terms}")

        # Строим вектор запроса
        query_vector = self.query_to_vector(query_terms)

        # Считаем сходство со всеми документами
        similarities = []
        for doc_id in self.doc_vectors.keys():
            score = self.cosine_similarity(query_vector, doc_id)
            if score > 0:
                similarities.append((doc_id, score))

        # Сортируем по убыванию
        similarities.sort(key=lambda x: x[1], reverse=True)

        results = []
        for doc_id, score in similarities[:top_k]:
            results.append({
                'doc_id': doc_id,
                'title': self.doc_titles.get(doc_id, f"Документ {doc_id}"),
                'file': self.doc_files.get(doc_id, f"page_{doc_id:03d}.txt"),
                'score': score
            })

        print(f"Найдено результатов: {len(results)}")
        return results

    def interactive_mode(self):
        """Интерактивный режим поиска"""
        print("ВЕКТОРНЫЙ ПОИСК (TF-IDF + косинусное сходство)")
        print("Для выхода: exit\n")

        while True:
            query = input(">> ").strip()
            if query.lower() == 'exit':
                break
            if not query:
                continue

            results = self.search(query)
            if results:
                print("\nРезультаты:")
                for i, r in enumerate(results, 1):
                    print(f"{i:2d}. {r['title']} (score: {r['score']:.4f})")
            else:
                print("Ничего не найдено")

def main():
    searcher = VectorSearchEngine()

    if not searcher.load_index():
        print("Индекс не найден. Запускаем построение...")

        builder = IndexBuilder()
        if builder.build():
            searcher.load_index()
        else:
            print("Не удалось построить индекс")
            return

    searcher.interactive_mode()

if __name__ == "__main__":
    main()