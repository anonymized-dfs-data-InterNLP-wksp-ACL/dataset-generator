from benchmark_evaluator.oracles_impl.oracle_abstract import Oracle
from benchmark_evaluator.configurations.connection_settings import Connection
import benchmark_evaluator.search.query_engine_impl as query_engine
import benchmark_evaluator.search.url_comparator as url_comparator
import time


class OracleSimulator(Oracle):
    def __init__(self):
        super(OracleSimulator, self).__init__()
        self.conn = Connection()

    def select_facet(self, query_results, already_selected_facets, max_candidate=5, **kwargs):
        """
        Oracle strategy: first select top-K (k=max_candidate=5) most relevant facets based scores,
        then find the facet which achieves the best relevance_rank for the expected tip.

        :param query_results:
        :param already_selected_facets:
        :param max_candidate:
        :param kwargs:
        :return:
        """
        start = time.time()
        new_facet, final_results = None, None

        ans_tip_docs = query_results.gold_ans_urls
        print('Oracle -- Last DFS relevance_rank: {}'.
              format(",".join([str(item) for item in query_results.obtained_ans_url_ranks])))
        facets = Oracle.flatten_facets(
            query_results=query_results, max_candidate=max_candidate, already_selected_facets=already_selected_facets)
        if len(facets) > 0:
            new_facets = list()
            results_with_new_facets = dict()
            for f in facets:  # consider the top K most relevant facets based on facet scores
                selected_facets = already_selected_facets.copy()
                selected_facets.append(f[0])
                tmp_results = query_engine.get_search_results_with_facets(
                    query_results.query, query_results.query_id, self.conn,
                    selected_facet_list=selected_facets)
                if tmp_results is not None:
                    tip_ranks = url_comparator.get_ans_url_position_in_docs(tmp_results.documents, ans_tip_docs)
                    if tip_ranks:
                        tip_ranks = [r.predicted_rank for r in tip_ranks]
                        if query_results.obtained_ans_url_ranks and \
                                min(tip_ranks) < min([r.predicted_rank for r in query_results.obtained_ans_url_ranks]):
                            new_f = (f[0], tip_ranks)
                            new_facets.append(new_f)
                            results_with_new_facets[f[0]] = tmp_results
            if new_facets:
                new_facets.sort(key=lambda x: x[1], reverse=False)
                print('oracle -- new Facet: ', new_facets[0][0])
                print('Oracle -- tip relevance_rank: ', str(new_facets[0][1]))
                new_facet, final_results = new_facets[0][0], results_with_new_facets[new_facets[0][0]]

        print('select_optimal_facet_for_best_possible_result took %d seconds' % (time.time() - start))
        return new_facet, final_results
