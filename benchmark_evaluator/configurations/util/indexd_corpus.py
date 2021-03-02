import json


class Corpus:

    def __init__(self, path):
        self.__all_docs = dict()
        self.load_corpus(path)

    def load_corpus(self, path):
        with open(path) as json_file:
            corpus = json.load(json_file)
        for id in corpus:
            self.__all_docs[corpus[id]["URL"].lower().strip()] = corpus[id]["TEXT"]

    def get_doc_text(self, url):
        url = url.lower().strip()
        if url in self.__all_docs:
            return self.__all_docs[url]

        return ""

    def get_full_text_for_selected_docs(self, documents_from_search_results):
        for d in documents_from_search_results:
            doc_text = self.get_doc_text(d.url)
            if doc_text:
                d.full_text = doc_text.lower()
            else:
                print(" ".join(["Missing doc ::", d.url]))

