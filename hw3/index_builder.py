import re
import json
from collections import defaultdict
import os

class IndexBuilder:
    """Класс для построения инвертированного индекса"""

    def __init__(self, lemmas_dir='../hw2/lemmas', pages_dir='../hw1/pages'):
        self.lemmas_dir = lemmas_dir
        self.pages_dir = pages_dir
        self.inverted_index = defaultdict(set)
        self.doc_ids = {}
        self.id_to_file = {}
        self.id_to_title = {}

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

    def extract_page_number(self, filename):
        match = re.search(r'page_(\d+)\.txt', filename)
        if match:
            return int(match.group(1))
        return None

    def load_lemmas_file(self, filepath, doc_id):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                lemma = parts[0]
                self.inverted_index[lemma].add(doc_id)

    def build(self):
        print("Построение индекса...")
        lemma_files = [f for f in os.listdir(self.lemmas_dir) if f.endswith('.txt')]
        lemma_files.sort()

        for filename in lemma_files:
            page_num = self.extract_page_number(filename)
            if page_num is None:
                print(f"Пропущен файл: {filename}")
                continue

            filepath = os.path.join(self.lemmas_dir, filename)
            doc_id = page_num
            self.doc_ids[filename] = doc_id
            self.id_to_file[doc_id] = filename

            html_filename = filename.replace('.txt', '.html')
            html_filepath = os.path.join(self.pages_dir, html_filename)
            self.id_to_title[doc_id] = self.extract_title_from_html(html_filepath)

            self.load_lemmas_file(filepath, doc_id)

        print(f"Индекс построен. Документов: {len(self.doc_ids)}, лемм: {len(self.inverted_index)}")
        return self.inverted_index, self.doc_ids, self.id_to_file, self.id_to_title

    def save(self, index_file='inverted_index.json'):
        index_to_save = {}
        for lemma, doc_set in self.inverted_index.items():
            index_to_save[lemma] = list(doc_set)

        data = {
            'index': index_to_save,
            'doc_ids': self.doc_ids,
            'id_to_file': self.id_to_file,
            'id_to_title': self.id_to_title
        }

        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Индекс сохранен в {index_file}")
        return index_file