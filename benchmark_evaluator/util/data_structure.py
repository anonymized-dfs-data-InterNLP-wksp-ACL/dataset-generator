from abc import ABC
from json import JSONEncoder


class MyEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, (GoldAnsDoc, SearchResults, Doc, Facet, TypedFacet, DocRank, FacetedSearchOutcome)):
            return o.__dict__
        if isinstance(o, set):
            return list(o)
        return super().default(o)


class GoldAnsDoc:
    def __init__(self):
        self.ans_url = ""           # url of the document
        self.ans_page_title = ""    # title of the document
        self.relevance_rank = 0     # `1` means most preferred document, `2` means the next most preferred one, etc etc
        self.url_id = ""

    @classmethod
    def deserialize(cls, values):
        gad = GoldAnsDoc()
        gad.ans_url = values['ans_url']
        gad.ans_page_title = values['ans_page_title']
        gad.relevance_rank = values['relevance_rank']
        gad.url_id = values['url_id']
        return gad

    def __str__(self):
        return "Ans Doc:\n\ttitle: {}\n\turl: {}\n\trel rank: {}\n\turl id: {}".format(self.ans_page_title, self.ans_url
                                                                                       , self.relevance_rank,
                                                                                       self.url_id)


class InputQuery:
    def __init__(self):
        self.id = ""
        self.query = ""                     # the user query
        self.ans_docs = set()               # set of GoldAnsDoc objects; each of them is an acceptable answer document
        self.query_filename = ""            # forum file name
        self.query_url = ""                 # url
        self.first_para_in_filename = ""    # the first post
        self.query_context = ""             # this gives more textual description of the query, e.g., QUESTION_TEXT in techqa


class Benchmark(ABC):
    """
    Abstract class for benchmark

    Create a new sub-class for every new benchmark by inheriting this abstract class
    """

    def __init__(self):
        self.queries = list()

    # abstract method
    def read_ground_truth(self, data_file, max_queries=None):
        pass


class StopConditionThresholds:
    max_iteration_threshold = 3
    max_rank_threshold = 500


class SearchResults:
    def __init__(self, query_text, query_id):
        self.query = query_text
        self.query_id = query_id
        self.documents = []
        self.facets = []
        self.query_filename = ""  # thread/forum filename
        self.query_context = ""  # more textual description of the query
        self.gold_ans_urls = set()
        self.obtained_ans_url_ranks = set()

    def serialize(self):
        return MyEncoder().encode(self)

    @classmethod
    def deserialize(cls, search_results_dict):
        search_results = SearchResults(search_results_dict['query'], search_results_dict['query_id'])
        search_results.documents = [Doc.deserialize(x) for x in search_results_dict['documents']]
        search_results.facets = [TypedFacet.deserialize(x) for x in search_results_dict['facets']]
        search_results.query_filename = search_results_dict['query_filename']
        search_results.query_context = search_results_dict["query_context"]
        search_results.gold_ans_urls = set([GoldAnsDoc.deserialize(x) for x in search_results_dict['gold_ans_urls']])
        search_results.obtained_ans_url_ranks = set([DocRank.deserialize(x) for x in search_results_dict['obtained_ans_url_ranks']])
        return search_results

    def to_dfs_outcome(self):
        dfs_outcome = FacetedSearchOutcome.init_dfs_outcome(
            query_text=self.query, query_id=self.query_id, number_of_facets_returned=len(self.facets),
            number_of_results_returned=len(self.documents), baseline_rank=self.obtained_ans_url_ranks)
        print("Baseline (answer url) result_ranks: ",
              str(dfs_outcome.get_ranks_for_predicated_results(for_baseline=True)))
        return dfs_outcome


class Doc:
    def __init__(self):
        self.title = ""
        self.full_text = ""
        self.original_id = ""
        self.url = ""
        self.search_rank = 0
        self.search_score = 0

    @classmethod
    def deserialize(cls, values):
        doc = Doc()
        doc.title = values['title']
        doc.full_text = values['full_text']
        doc.original_id = values['original_id']
        doc.url = values['url']
        doc.search_rank = values['search_rank']
        doc.search_score = values['search_score']
        return doc


class Facet:
    def __init__(self):
        self.text = ""
        self.score = 0
        self.relevance_score = 0
        self.pervasive_score = 0
        self.mapped_doc_ranks = list()

    @classmethod
    def deserialize(cls, values):
        f = Facet()
        f.text = values['text']
        f.score = values['score']
        f.pervasive_score = values['pervasive_score']
        f.relevance_score = values['relevance_score']
        f.mapped_doc_ranks = list(values['mapped_doc_ranks'])
        return f


class TypedFacet:
    def __init__(self):
        self.facet_type = ''
        self.facet_ind = list()

    @classmethod
    def deserialize(cls, values):
        tf = TypedFacet()
        tf.facet_type = values['facet_type']
        tf.facet_ind = [Facet.deserialize(x) for x in values['facet_ind']]
        return tf


class DocRank:
    def __init__(self, predicted_rank, gold_relevance_rank):
        self.predicted_rank = predicted_rank
        self.gold_relevance_rank = gold_relevance_rank

    @classmethod
    def deserialize(cls, values):
        return DocRank(values['predicted_rank'], values['gold_relevance_rank'])

    def __str__(self):
        return "(DocRank) Predicted Rank: {}, Gold relevance rank: {}".format(
                self.predicted_rank, self.gold_relevance_rank)


class FacetedSearchOutcome:
    def __init__(self):
        self.query = ""
        self.query_id = -1
        self.baseline_tip_ranks = set()
        self.dfs_tip_rank = None
        self.number_of_facets_selected = 0
        self.number_of_facets_returned = 0
        self.number_of_results_returned = 0
        self.dfs_rank_by_iter = dict()
        self.selected_facets = list()

    def get_ranks_for_predicated_results(self, for_baseline=False):
        if for_baseline:
            return [] if not self.baseline_tip_ranks else [r.predicted_rank for r in self.baseline_tip_ranks]
        else:
            return [] if not self.dfs_tip_rank else [r.predicted_rank for r in self.dfs_tip_rank]

    @staticmethod
    def init_dfs_outcome(query_text, query_id, number_of_facets_returned=0, baseline_rank=set(),
                         number_of_results_returned=0, dfs_rank=set(), number_of_facets_selected=0):
        """

        :param query_text:
        :param query_id:
        :param number_of_facets_returned:
        :param baseline_rank:
        :param number_of_results_returned:
        :param dfs_rank:
        :param number_of_facets_selected:
        :return:
        """
        _new_dfs_outcome = FacetedSearchOutcome()
        _new_dfs_outcome.query = query_text
        _new_dfs_outcome.query_id = query_id
        _new_dfs_outcome.number_of_facets_returned = number_of_facets_returned
        _new_dfs_outcome.number_of_facets_selected = number_of_facets_selected
        if not baseline_rank:
            baseline_rank = set()
        _new_dfs_outcome.baseline_tip_ranks = []
        for p in baseline_rank:
            if type(p) is int:
                _ndr = DocRank(p, 1)
                _new_dfs_outcome.baseline_tip_ranks.append(_ndr)
            else:
                _new_dfs_outcome.baseline_tip_ranks.append(p)
        _new_dfs_outcome.number_of_results_returned = number_of_results_returned
        if dfs_rank:
            _new_dfs_outcome.dfs_tip_rank = []
            for p in dfs_rank:
                if type(p) is int:
                    _ndr = DocRank(p, 1)
                    _new_dfs_outcome.dfs_tip_rank.append(_ndr)
                else:
                    _new_dfs_outcome.dfs_tip_rank.append(p)
        return _new_dfs_outcome

    def serialize(self):
        return MyEncoder().encode(self)

    @classmethod
    def deserialize(cls, dfs_results_dict):
        dfs_results = FacetedSearchOutcome()
        dfs_results.query = dfs_results_dict['query']
        dfs_results.query_id = dfs_results_dict['query_id']
        dfs_results.baseline_tip_ranks = set([DocRank.deserialize(x) for x in dfs_results_dict['baseline_tip_ranks']]
                                             if dfs_results_dict['baseline_tip_ranks'] else [])
        dfs_results.dfs_tip_rank = set([DocRank.deserialize(x) for x in dfs_results_dict['dfs_tip_rank']]
                                       if dfs_results_dict['dfs_tip_rank'] else [])
        dfs_results.number_of_facets_selected = dfs_results_dict['number_of_facets_selected']
        dfs_results.number_of_facets_returned = dfs_results_dict['number_of_facets_returned']
        dfs_results.number_of_results_returned = dfs_results_dict['number_of_results_returned']
        dfs_results.dfs_rank_by_iter = dfs_results_dict['dfs_rank_by_iter']
        dfs_results.selected_facets = dfs_results_dict['selected_facets']
        return dfs_results
