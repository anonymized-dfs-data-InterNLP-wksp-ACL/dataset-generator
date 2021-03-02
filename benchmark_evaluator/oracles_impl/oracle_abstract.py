from abc import ABC
from benchmark_evaluator.configurations.config import *
import json
from pyjarowinkler import distance
import benchmark_evaluator.util.misc_util as misc_util


class Oracle(ABC):
    """
    Abstract class for Oracle

    Create a new sub-class for every new Oracle by inheriting this abstract class
    """

    def __init__(self):
        self.queries = list()

    # abstract method
    def select_facet(self, query_results, already_selected_facets, max_candidate=10, **kwargs):
        pass

    @staticmethod
    def flatten_facets(query_results, max_candidate, already_selected_facets):
        facets = []
        for typed_f in query_results.facets:
            for f in typed_f.facet_ind:
                if f.text.lower() not in already_selected_facets:
                    facets.append((f.text, f.score))
        facets = [(f.text, f.score) for typed_f in query_results.facets
                  for f in typed_f.facet_ind if f.text.lower() not in already_selected_facets]
        if len(facets) == 0:
            return list()
        facets.sort(key=lambda x: x[1], reverse=True)
        if len(facets) > max_candidate:
            facets = facets[:max_candidate]
        return facets

    @staticmethod
    def fuzzy_match_facet(text, facet):
        score = distance.get_jaro_distance(text.lower(), facet.lower(), winkler=True, scaling=0.1)
        print(facet, score)
        return score