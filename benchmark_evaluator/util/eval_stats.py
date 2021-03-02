import benchmark_evaluator.configurations.config as config
import os


def write_rows(rows, out_file_name):
    csv_str = "\n".join(rows)
    write(csv_str, out_file_name)


def write(text, out_file_name):
    x = out_file_name.rindex(os.path.sep)
    if x > -1:
        directory = out_file_name[:x]
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(out_file_name, "w") as f:
        f.write(text)
    print("Output written in " + out_file_name)


def headroom_analysis(dfs_activated_queries, es_hits_1, dfs_hits_1, failed_queries, total_queries):
    """

    :param dfs_activated_queries:
    :param es_hits_1:
    :param dfs_hits_1:
    :param failed_queries:
    :param total_queries:
    :return:
    """
    headroom_dfs = total_queries - failed_queries - dfs_activated_queries - es_hits_1
    headroom_hits_1 = total_queries - failed_queries - dfs_hits_1 - es_hits_1
    summary = "======================\nSummary of Analysis\n======================\n" \
              + "Queries with no gold document in returned results = " + str(failed_queries) \
              + "\nES Hits@1  = " + str(es_hits_1) \
              + "\nDFS activated queries = " + str(dfs_activated_queries) \
              + "\nAdditional Hits@1 by DFS = " + str(dfs_hits_1) \
              + "\n\nHeadroom for DFS activation = " \
              + "-".join([str(total_queries), str(failed_queries), str(dfs_activated_queries), str(es_hits_1)]) \
              + " = " + str(headroom_dfs) + "   (" + str(round((headroom_dfs*100)/total_queries)) + "%)" \
              + "\nHeadroom for Hits@1 for DFS = " \
              + "-".join([str(total_queries), str(failed_queries), str(dfs_hits_1), str(es_hits_1)])\
              + " = " + str(headroom_hits_1) + "   (" + str(round((headroom_hits_1 * 100) / total_queries)) + "%)"\
              + "\n========================\n"
    write(summary, config.temp_path + '/headroom_analysis.txt')


class HitsStats:
    def __init__(self):
        """
        Initialize
        """
        '''
            Hits@R
        '''
        self.hits_thresholds = [1, 5, 10, 20, 50]
        self.hit_at_k_baseline = dict()
        self.hit_at_k_dfs_iter_1 = dict()
        self.hit_at_k_dfs = dict()
        self.percentage_hit_at_k_baseline = dict()
        self.percentage_hit_at_k_dfs_iter_1 = dict()
        self.percentage_hit_at_k_dfs = dict()
        for ht in self.hits_thresholds:
            self.hit_at_k_baseline[ht] = 0
            self.hit_at_k_dfs[ht] = 0
            self.hit_at_k_dfs_iter_1[ht] = 0
            self.percentage_hit_at_k_baseline[ht] = 0
            self.percentage_hit_at_k_dfs[ht] = 0
            self.percentage_hit_at_k_dfs_iter_1[ht] = 0

        self.full_mrr_dfs = 0
        self.full_mrr_es = 0

        self.full_dcg_dfs = 0
        self.full_dcg_es = 0

    def print_summary(self):

        rows = [", ".join(["", "ES", "DFS+ES", "ES (%)", "DFS+ES (%)"])]

        for rank in self.hits_thresholds:
            rows.append(", ".join(["Hits@" + str(rank), str(self.hit_at_k_baseline[rank]),
                                  str(self.hit_at_k_dfs[rank]), str(round(self.percentage_hit_at_k_baseline[rank], 2)),
                                  str(round(self.percentage_hit_at_k_dfs[rank], 2))]))

        rows.append(", ".join(["MRR", str(round(self.full_mrr_es, 2)), str(round(self.full_mrr_dfs, 2))]))
        rows.append(", ".join(["DCG", str(round(self.full_dcg_es, 2)), str(round(self.full_dcg_dfs, 2))]))
        write_rows(rows, os.path.join(config.temp_path, "summary_hits.csv"))


class Stats:

    @staticmethod
    def get_key(rank):
        if rank:
            return rank
        else:
            return 0

    def __init__(self):
        """
        Initialize
        """

        self.hits_stats = HitsStats()

        self.baseline_thresholds = [None, 1, 5, 10, 20]  # keys for other dicts below
        self.queries_got_improved_results = dict()
        self.queries_got_hurt = dict()
        self.max_facet_selected = dict()
        self.avg_facet_selected = dict()
        self.baseline_dcg = dict()
        self.dfs_dcg = dict()
        self.baseline_mrr = dict()
        self.dfs_mrr = dict()
        self.retrieved_at_k_baseline = dict()
        self.retrieved_at_k_dfs = dict()

        for rank in self.baseline_thresholds:
            key = self.get_key(rank)

            self.queries_got_improved_results[key] = 0
            self.queries_got_hurt[key] = 0
            self.max_facet_selected[key] = 0
            self.avg_facet_selected[key] = 0
            self.baseline_dcg[key] = 0
            self.dfs_dcg[key] = 0
            self.baseline_mrr[key] = 0
            self.dfs_mrr[key] = 0

            for n in [1, 5, 10, 20]:
                self.retrieved_at_k_baseline[key] = dict()
                self.retrieved_at_k_dfs[key] = dict()
                self.retrieved_at_k_baseline[key][n] = 0
                self.retrieved_at_k_dfs[key][n] = 0, 0

        '''
           The following stats are calculated by restricting to those queries for which the relevance_rank for the desired TIP 
           (in the returned results) is k or lower for baseline.
        '''
        self.k_values = [5, 10, 20]
        self.dcg_at_k_baseline = dict()
        self.dcg_at_k_dfs = dict()
        self.mrr_at_k_baseline = dict()
        self.mrr_at_k_dfs = dict()

        for k in self.k_values:
            self.dcg_at_k_baseline[k] = 0
            self.dcg_at_k_dfs[k] = 0
            self.mrr_at_k_baseline[k] = 0
            self.mrr_at_k_dfs[k] = 0

        '''
            The following stats are calculated by restricting number of iterations, 
            i.e. number of max. facet selection by oracle.
        '''
        self.iter_values = [0, 1, 2, 3, 4, 5]
        self.dcg_at_iter_baseline = dict()
        self.dcg_at_iter_dfs = dict()
        self.mrr_at_iter_baseline = dict()
        self.mrr_at_iter_dfs = dict()

        for it in self.iter_values:
            self.dcg_at_iter_baseline[it] = 0
            self.dcg_at_iter_dfs[it] = 0
            self.mrr_at_iter_baseline[it] = 0
            self.mrr_at_iter_dfs[it] = 0

    def print_stats(self):
        if not os.path.exists(config.temp_path):
            os.mkdir(config.temp_path)

        self.hits_stats.print_summary()
        self.__print_details_stats()
        self.__print_stats_at_k()
        self.__print_stats_per_iteration()

    def __print_details_stats(self):

        # print("Results calculated for queries with baseline, i.e. ES, (desired document) "
        #      "relevance_rank greater than different values of \"threshold relevance_rank\"::\n=========================================="
        #      "===============================================\n")

        rows = [", ".join(["Baseline relevance_rank cutoff", "Queries with improved results by DFS",
                          "Queries hurt by DFS results", "Maximum facet selected", "Average facet selected",
                          "DCG for baseline", "DCG for DFS", "MRR for baseline", "MRR for DFS",
                          "Retrieved @ 1 - Baseline", "Retrieved @ 1 - DFS",
                          "Retrieved @ 5 - Baseline", "Retrieved @ 5 - DFS",
                          "Retrieved @ 10 - Baseline", "Retrieved @ 10 - DFS",
                          "Retrieved @ 20 - Baseline", "Retrieved @ 20 - DFS"])]

        for rank in self.baseline_thresholds:
            key = self.get_key(rank)
            rows.append(", ".join([
                str(rank), str(self.queries_got_improved_results[key]), str(self.queries_got_hurt[key]),
                str(self.max_facet_selected[key]), str(self.avg_facet_selected[key]),
                str(self.baseline_dcg[key]), str(self.dfs_dcg[key]),
                str(self.baseline_mrr[key]), str(self.dfs_mrr[key]),
                str(self.retrieved_at_k_baseline[key][1]), str(self.retrieved_at_k_dfs[key][1]),
                str(self.retrieved_at_k_baseline[key][5]), str(self.retrieved_at_k_dfs[key][5]),
                str(self.retrieved_at_k_baseline[key][10]), str(self.retrieved_at_k_dfs[key][10]),
                str(self.retrieved_at_k_baseline[key][20]), str(self.retrieved_at_k_dfs[key][20]),
            ]))

        write_rows(rows, os.path.join(config.temp_path, "bottom_queries_summary.csv"))

    def __print_stats_at_k(self):

        rows = [", ".join(["k = Baseline max relevance_rank threshold",
                          "DCG for baseline @ k",
                          "DCG for DFS @ k",
                          "MRR for baseline @ k",
                          "MRR for DFS @ k"
                          ])]

        for k in self.k_values:
            rows.append(", ".join([
                str(k), str(self.dcg_at_k_baseline[k]), str(self.dcg_at_k_dfs[k]),
                str(self.mrr_at_k_baseline[k]), str(self.mrr_at_k_dfs[k])
            ]))

        write_rows(rows, os.path.join(config.temp_path, "top_queries_summary.csv"))

    def __print_stats_per_iteration(self):

        rows = [", ".join(["iter = Iteration / Facets selected",
                          "DCG for baseline @ iter",
                          "DCG for DFS @ iter",
                          "MRR for baseline @ iter",
                          "MRR for DFS @ iter"
                          ])]

        for it in self.iter_values:
            rows.append(", ".join([
                str(it), str(self.dcg_at_iter_baseline[it]), str(self.dcg_at_iter_dfs[it]),
                str(self.mrr_at_iter_baseline[it]), str(self.mrr_at_iter_dfs[it])
            ]))

        write_rows(rows, os.path.join(config.temp_path, "summary_per_iteration.csv"))

