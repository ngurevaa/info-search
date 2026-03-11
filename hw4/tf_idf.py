import os
import re
import math
from collections import defaultdict, Counter
import pymorphy3

class TfIdfCalculator:
    """Класс для подсчета TF-IDF"""

    def __init__(self,
                 tokens_dir='../hw2/tokens',
                 lemmas_dir='../hw2/lemmas',
                 output_dir='tfidf_results'):

        self.tokens_dir = tokens_dir
        self.lemmas_dir = lemmas_dir
        self.output_dir = output_dir

        self.terms_output = os.path.join(output_dir, 'terms')
        self.lemmas_output = os.path.join(output_dir, 'lemmas')
        os.makedirs(self.terms_output, exist_ok=True)
        os.makedirs(self.lemmas_output, exist_ok=True)

        self.morph = pymorphy3.MorphAnalyzer()

        # Данные для подсчета
        self.doc_id_to_name = {}
        self.term_freq = defaultdict(dict)
        self.lemma_freq = defaultdict(dict)
        self.doc_term_count = {}
        self.doc_lemma_count = {}

        # Глобальная статистика
        self.docs_with_term = defaultdict(int)
        self.docs_with_lemma = defaultdict(int)
        self.total_docs = 0

    def extract_page_number(self, filename):
        match = re.search(r'page_(\d+)', filename)
        if match:
            return int(match.group(1))
        return None

    def load_terms_file(self, filepath, doc_id):
        with open(filepath, 'r', encoding='utf-8') as f:
            terms = [line.strip() for line in f if line.strip()]

        term_counter = Counter(terms)
        self.term_freq[doc_id] = dict(term_counter)
        self.doc_term_count[doc_id] = len(terms)

        for term in set(terms):
            self.docs_with_term[term] += 1

    def load_lemmas_file(self, filepath, doc_id):
        lemmas_list = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                lemma = parts[0]
                lemmas_list.append(lemma)

        lemma_counter = Counter(lemmas_list)
        self.lemma_freq[doc_id] = dict(lemma_counter)
        self.doc_lemma_count[doc_id] = len(lemmas_list)

        for lemma in set(lemmas_list):
            self.docs_with_lemma[lemma] += 1

    def collect_documents(self):
        print("Сбор статистики по документам...")

        term_files = [f for f in os.listdir(self.tokens_dir) if f.endswith('.txt')]
        term_files.sort()

        for filename in term_files:
            page_num = self.extract_page_number(filename)
            if page_num is None:
                continue

            doc_id = page_num
            self.doc_id_to_name[doc_id] = filename

            term_path = os.path.join(self.tokens_dir, filename)
            self.load_terms_file(term_path, doc_id)

            lemma_path = os.path.join(self.lemmas_dir, filename)
            if os.path.exists(lemma_path):
                self.load_lemmas_file(lemma_path, doc_id)

        self.total_docs = len(self.doc_id_to_name)
        print(f"Найдено документов: {self.total_docs}")

    def calculate_idf(self, doc_count):
        if doc_count == 0:
            return 0
        return math.log((self.total_docs + 1) / (doc_count + 1)) + 1

    def calculate_tf(self, term_freq, total_terms):
        if total_terms == 0:
            return 0
        return term_freq / total_terms

    def process_terms(self):
        print("\nПодсчет TF-IDF для терминов...")

        for doc_id in self.doc_id_to_name.keys():
            filename = self.doc_id_to_name[doc_id]
            output_file = os.path.join(self.terms_output, filename)

            total_terms = self.doc_term_count.get(doc_id, 0)
            if total_terms == 0:
                continue

            with open(output_file, 'w', encoding='utf-8') as f:
                for term, freq in self.term_freq.get(doc_id, {}).items():
                    tf = self.calculate_tf(freq, total_terms)
                    doc_count = self.docs_with_term.get(term, 0)
                    idf = self.calculate_idf(doc_count)
                    tf_idf = tf * idf
                    f.write(f"{term} {idf:.6f} {tf_idf:.6f}\n")

            print(f"  ✓ {filename}")

    def process_lemmas(self):
        print("\nПодсчет TF-IDF для лемм...")

        for doc_id in self.doc_id_to_name.keys():
            filename = self.doc_id_to_name[doc_id]
            output_file = os.path.join(self.lemmas_output, filename)

            total_lemmas = self.doc_lemma_count.get(doc_id, 0)
            if total_lemmas == 0:
                continue

            with open(output_file, 'w', encoding='utf-8') as f:
                for lemma, freq in self.lemma_freq.get(doc_id, {}).items():
                    tf = self.calculate_tf(freq, total_lemmas)
                    doc_count = self.docs_with_lemma.get(lemma, 0)
                    idf = self.calculate_idf(doc_count)
                    tf_idf = tf * idf
                    f.write(f"{lemma} {idf:.6f} {tf_idf:.6f}\n")

            print(f"  ✓ {filename}")

    def run(self):
        self.collect_documents()
        self.process_terms()
        self.process_lemmas()
        print(f"\nГотово! Результаты в папке {self.output_dir}/")


def main():
    calculator = TfIdfCalculator()
    calculator.run()


if __name__ == "__main__":
    main()