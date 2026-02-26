import os
import json
from collections import defaultdict
import pymorphy3
from index_builder import IndexBuilder

class BooleanSearch:
    """Класс для поиска по индексу"""

    def __init__(self, index_file='inverted_index.json'):
        self.index_file = index_file
        self.inverted_index = defaultdict(set)
        self.doc_ids = {}
        self.id_to_file = {}
        self.id_to_title = {}
        self.morph = pymorphy3.MorphAnalyzer()

    def load_index(self):
        if not os.path.exists(self.index_file):
            return False

        with open(self.index_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for lemma, doc_list in data['index'].items():
            self.inverted_index[lemma] = set(doc_list)

        self.doc_ids = data['doc_ids']
        self.id_to_file = {int(k): v for k, v in data['id_to_file'].items()}
        self.id_to_title = {int(k): v for k, v in data['id_to_title'].items()}

        print(f"Индекс загружен. Документов: {len(self.doc_ids)}, лемм: {len(self.inverted_index)}")
        return True

    def build_index_from_scratch(self):
        """Автоматически строит индекс если файл не найден"""
        print("Файл индекса не найден. Строим индекс...")
        builder = IndexBuilder()
        builder.build()
        builder.save(self.index_file)
        return self.load_index()

    def lemmatize_query_term(self, term):
        term = term.lower().strip()
        return self.morph.parse(term)[0].normal_form

    def tokenize_query(self, query):
        query = query.replace('(', ' ( ').replace(')', ' ) ')
        return query.split()

    def apply_operator(self, operator, value_stack):
        if operator == 'NOT':
            if len(value_stack) >= 1:
                set1 = value_stack.pop()
                all_docs = set(self.id_to_file.keys())
                value_stack.append(all_docs - set1)
        else:
            if len(value_stack) >= 2:
                set2 = value_stack.pop()
                set1 = value_stack.pop()
                if operator == 'AND':
                    value_stack.append(set1 & set2)
                elif operator == 'OR':
                    value_stack.append(set1 | set2)

    def parse_query(self, query):
        query = query.strip()
        if ' ' not in query and '(' not in query:
            lemma = self.lemmatize_query_term(query)
            return self.inverted_index.get(lemma, set())

        tokens = self.tokenize_query(query)
        value_stack = []
        op_stack = []
        precedence = {'NOT': 3, 'AND': 2, 'OR': 1}

        i = 0
        while i < len(tokens):
            token = tokens[i].upper()
            if token == '(':
                op_stack.append(token)
            elif token == ')':
                while op_stack and op_stack[-1] != '(':
                    self.apply_operator(op_stack.pop(), value_stack)
                op_stack.pop()
            elif token in precedence:
                while (op_stack and op_stack[-1] != '(' and
                       precedence.get(op_stack[-1], 0) >= precedence[token]):
                    self.apply_operator(op_stack.pop(), value_stack)
                op_stack.append(token)
            else:
                lemma = self.lemmatize_query_term(token)
                doc_set = self.inverted_index.get(lemma, set())
                value_stack.append(doc_set)
            i += 1

        while op_stack:
            self.apply_operator(op_stack.pop(), value_stack)

        return value_stack[0] if value_stack else set()

    def search(self, query):
        print(f"\nЗапрос: {query}")
        doc_ids = self.parse_query(query)

        if not doc_ids:
            print("Ничего не найдено")
            return []

        results = []
        for doc_id in sorted(doc_ids):
            results.append({
                'title': self.id_to_title[doc_id],
                'file': self.id_to_file[doc_id]
            })

        print(f"Найдено: {len(results)}")
        return results

    def interactive_mode(self):
        print("\nБулев поиск. Операторы: AND, OR, NOT, скобки")
        print("Для выхода: exit\n")

        while True:
            query = input(">> ").strip()
            if query.lower() == 'exit':
                break
            if not query:
                continue

            results = self.search(query)
            if results:
                for i, r in enumerate(results, 1):
                    print(f"{i}. {r['title']} ({r['file']})")


def main():
    search = BooleanSearch()

    # Пытаемся загрузить индекс, если нет - строим автоматически
    if not search.load_index():
        if not search.build_index_from_scratch():
            print("Не удалось построить индекс")
            return

    search.interactive_mode()

if __name__ == "__main__":
    main()