import os
import re
import json
from collections import defaultdict
import pymorphy3

class BooleanSearchEngine:
    def __init__(self, lemmas_dir='../hw2/lemmas', pages_dir='../hw1/pages', index_file='inverted_index.json'):
        self.lemmas_dir = lemmas_dir
        self.pages_dir = pages_dir
        self.index_file = index_file
        self.inverted_index = defaultdict(set)
        self.doc_ids = {}
        self.id_to_file = {}
        self.id_to_title = {}
        self.morph = pymorphy3.MorphAnalyzer()

    def extract_title_from_html(self, html_file):
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

    def load_lemmas_file(self, filepath, doc_id):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                lemma = parts[0]
                self.inverted_index[lemma].add(doc_id)

    def save_index_to_file(self):
        """Сохраняет индекс в JSON файл"""
        index_to_save = {}
        for lemma, doc_set in self.inverted_index.items():
            index_to_save[lemma] = list(doc_set)

        data = {
            'index': index_to_save,
            'doc_ids': self.doc_ids,
            'id_to_file': self.id_to_file,
            'id_to_title': self.id_to_title
        }

        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Индекс сохранен в {self.index_file}")

    def load_index_from_file(self):
        """Загружает индекс из JSON файла"""
        if not os.path.exists(self.index_file):
            return False

        with open(self.index_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for lemma, doc_list in data['index'].items():
            self.inverted_index[lemma] = set(doc_list)

        self.doc_ids = data['doc_ids']
        self.id_to_file = {int(k): v for k, v in data['id_to_file'].items()}
        self.id_to_title = {int(k): v for k, v in data['id_to_title'].items()}

        print(f"Индекс загружен из {self.index_file}")
        return True

    def build_index(self):
        print("Построение индекса...")
        lemma_files = [f for f in os.listdir(self.lemmas_dir) if f.endswith('.txt')]
        lemma_files.sort()

        for doc_id, filename in enumerate(lemma_files):
            filepath = os.path.join(self.lemmas_dir, filename)
            self.doc_ids[filename] = doc_id
            self.id_to_file[doc_id] = filename

            html_filename = filename.replace('.txt', '.html')
            html_filepath = os.path.join(self.pages_dir, html_filename)
            self.id_to_title[doc_id] = self.extract_title_from_html(html_filepath)

            self.load_lemmas_file(filepath, doc_id)

        print(f"Индекс построен. Документов: {len(self.doc_ids)}, лемм: {len(self.inverted_index)}")

        # Сохраняем индекс в файл
        self.save_index_to_file()

    def lemmatize_query_term(self, term):
        term = term.lower().strip()
        return self.morph.parse(term)[0].normal_form

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

    def tokenize_query(self, query):
        query = query.replace('(', ' ( ').replace(')', ' ) ')
        return query.split()

    def apply_operator(self, operator, value_stack):
        if operator == 'NOT':
            if len(value_stack) >= 1:
                set1 = value_stack.pop()
                all_docs = set(range(len(self.id_to_file)))
                value_stack.append(all_docs - set1)
        else:
            if len(value_stack) >= 2:
                set2 = value_stack.pop()
                set1 = value_stack.pop()
                if operator == 'AND':
                    value_stack.append(set1 & set2)
                elif operator == 'OR':
                    value_stack.append(set1 | set2)

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
    engine = BooleanSearchEngine()
    index_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'inverted_index.json')

    # Если индекс уже существует, загружаем его
    if os.path.exists(index_file):
        load = input("Найден сохраненный индекс. Загрузить? (y/n): ")
        if load.lower() == 'y':
            if not engine.load_index_from_file():
                print("Не удалось загрузить, строим заново")
                engine.build_index()
        else:
            engine.build_index()
    else:
        engine.build_index()

    engine.interactive_mode()


if __name__ == "__main__":
    main()