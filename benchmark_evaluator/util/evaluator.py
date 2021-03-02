import math
from benchmark_evaluator.util.eval_stats import Stats as Stats
import benchmark_evaluator.util.eval_stats as eval_stats
import benchmark_evaluator.configurations.config as config
from benchmark_evaluator.search.url_comparator import DocRank
import operator


def __query_results_to_list_of_tuples(query_results, only_dfs_activated_queries=False):
    """

    :param query_results:
    :param only_dfs_activated_queries:
    :return:
    """
    all_attempted_queries_ranks = list()
    for q_outcome in query_results:
        # Checking whether to ignore those queries when dfs was not activated,
        # since the relevance_rank of TIP will be unchanged
        if only_dfs_activated_queries and q_outcome.number_of_facets_selected == 0:
            continue
        es_ranks = q_outcome.baseline_tip_ranks
        if q_outcome.number_of_facets_selected == 0:
            # When dfs was not activated, the default dfs relevance_rank is the relevance_rank of ES
            dfs_r = q_outcome.baseline_tip_ranks
        else:
            dfs_r = q_outcome.dfs_tip_rank
        all_attempted_queries_ranks.append((es_ranks, dfs_r))
    return all_attempted_queries_ranks


def __norm_neg_rank(rank):
    """

    :param rank:
    :return:
    """
    if rank > 0:
        return rank
    else:
        return 0


def calculate_dcg(all_attempted_queries_ranks, additional_failed_queries=0):
    """
    Discounted cumulative gain

    :param all_attempted_queries_ranks:
    :param additional_failed_queries:
    :return:
    """
    if len(all_attempted_queries_ranks) == 0:
        return 0, 0
    baseline_dcg = 0
    dfs_dcg = 0
    for es_ranks, dfs_ranks in all_attempted_queries_ranks:
        if not es_ranks:
            es_ranks = list()
            es_ranks.append(DocRank(-1, 1))
        else:
            mr = min([d.predicted_rank for d in es_ranks])
            baseline_dcg += 1 / math.log2(__norm_neg_rank(mr) + 1)
        if not dfs_ranks:
            dfs_ranks = list()
            dfs_ranks.append(DocRank(-1, 1))
        else:
            mr = min([d.predicted_rank for d in dfs_ranks])
            dfs_dcg += 1 / math.log2(__norm_neg_rank(mr) + 1)

    total_queries = len(all_attempted_queries_ranks) + additional_failed_queries
    return baseline_dcg/total_queries, dfs_dcg/total_queries


def calculate_mrr(all_attempted_queries_ranks, additional_failed_queries=0):
    """
    Mean reciprocal relevance_rank

    :param all_attempted_queries_ranks:
    :param additional_failed_queries:
    :return:
    """
    if len(all_attempted_queries_ranks) == 0:
        return 0, 0
    baseline_mrr = 0
    dfs_mrr = 0
    for es_ranks, dfs_ranks in all_attempted_queries_ranks:
        if es_ranks:
            es_r = min([w.predicted_rank for w in es_ranks])
        else:
            es_r = -1
        baseline_mrr += 1.0 / __norm_neg_rank(es_r)
        if dfs_ranks:
            dfs_r = min([d.predicted_rank for d in dfs_ranks])
        else:
            dfs_r = -1
        dfs_mrr += 1.0 / __norm_neg_rank(dfs_r)

    total_queries = len(all_attempted_queries_ranks) + additional_failed_queries
    return baseline_mrr/total_queries, dfs_mrr/total_queries


def __retrieved_queries_at_k(query_results, k):
    """
    Retrieved queries @ <= k
    i.e. # of queries for which the desired TIP is @ <= k in the corresponding retrieved results

    :param query_results:
    :param k:
    :return:
    """
    baseline_at_k = len([q_outcome for q_outcome in query_results if q_outcome.dfs_tip_rank and
                         q_outcome.dfs_tip_rank and
                         compare_rank_with_threshold(q_outcome.baseline_tip_ranks, k, operator_func=operator.le)])
    dfs_at_k = len([q_outcome for q_outcome in query_results if q_outcome.dfs_tip_rank and
                    compare_rank_with_threshold(q_outcome.dfs_tip_rank, k, operator_func=operator.le)])
    return baseline_at_k, dfs_at_k


def print_summary_eval_results(orig_query_results, all_stats, total_failed_queries):
    """

    :param orig_query_results:
    :param all_stats:
    :param total_failed_queries:
    :return:
    """
    total_queries = len(orig_query_results) + total_failed_queries
    for k in all_stats.hits_stats.hits_thresholds:
        all_stats.hits_stats.hit_at_k_baseline[k] = \
            len([q_outcome for q_outcome in orig_query_results if q_outcome.baseline_tip_ranks
                 and compare_rank_with_threshold(q_outcome.baseline_tip_ranks, k, operator_func=operator.le)])
        all_stats.hits_stats.percentage_hit_at_k_baseline[k] \
            = (all_stats.hits_stats.hit_at_k_baseline[k]) / total_queries

        all_stats.hits_stats.hit_at_k_dfs[k] \
            = len([q_outcome for q_outcome in orig_query_results
                   if (q_outcome.dfs_tip_rank and
                       compare_rank_with_threshold(q_outcome.dfs_tip_rank, k, operator_func=operator.le))
                   or (q_outcome.number_of_facets_selected == 0
                       and compare_rank_with_threshold(q_outcome.baseline_tip_ranks, k, operator_func=operator.le))])
        all_stats.hits_stats.percentage_hit_at_k_dfs[k] \
            = (all_stats.hits_stats.hit_at_k_dfs[k]) / total_queries

        all_stats.hits_stats.hit_at_k_dfs_iter_1[k] \
            = len([q_outcome for q_outcome in orig_query_results
                   if (1 in q_outcome.dfs_rank_by_iter and q_outcome.dfs_rank_by_iter[1] is not None
                       and compare_rank_with_threshold(q_outcome.dfs_tip_rank, k, operator_func=operator.le))
                   or (q_outcome.number_of_facets_selected == 0
                       and compare_rank_with_threshold(q_outcome.baseline_tip_ranks, k, operator_func=operator.le))])
        all_stats.hits_stats.percentage_hit_at_k_dfs_iter_1[k] \
            = (all_stats.hits_stats.hit_at_k_dfs_iter_1[k]) / total_queries
    all_attempted_queries_ranks = __query_results_to_list_of_tuples(orig_query_results, False)

    all_stats.hits_stats.full_dcg_es, all_stats.hits_stats.full_dcg_dfs \
        = calculate_dcg(all_attempted_queries_ranks, total_failed_queries)
    all_stats.hits_stats.full_mrr_es, all_stats.hits_stats.full_mrr_dfs \
        = calculate_mrr(all_attempted_queries_ranks, total_failed_queries)

    dfs_activated_queries = len([1 for q_outcome in orig_query_results if q_outcome.number_of_facets_selected > 0])
    eval_stats.headroom_analysis(dfs_activated_queries=dfs_activated_queries,
                                 es_hits_1=all_stats.hits_stats.hit_at_k_baseline[1],
                                 dfs_hits_1=all_stats.hits_stats.hit_at_k_dfs[1]
                                            -all_stats.hits_stats.hit_at_k_baseline[1],
                                 failed_queries=total_failed_queries, total_queries=total_queries)


def compare_rank_with_threshold(result_ranks, threshold, operator_func):
    all_pred_ranks = [res.predicted_rank for res in result_ranks if res.predicted_rank > -1]
    if type(threshold) is set or type(threshold) is list:
        all_thresholds = [t.predicted_rank for t in threshold]
    else:
        all_thresholds = [threshold]
    if any([operator_func(pr, t) for pr in all_pred_ranks for t in all_thresholds]):
        return True
    return False


def print_details_eval_results(orig_query_results, total_failed_queries, only_dfs_activated_queries=False):
    if only_dfs_activated_queries:
        total_failed_queries = 0

    print('generating details eval results for %d queries' % len(orig_query_results))
    print_ranks(orig_query_results)
    all_stats = Stats()
    print_summary_eval_results(orig_query_results, all_stats, total_failed_queries)
    for rank_th in all_stats.baseline_thresholds:
        key = all_stats.get_key(rank_th)
        ''' After ignoring any query with ES (baseline) relevance_rank smaller (or equal to) than the threshold '''
        query_results = [q_outcome for q_outcome in orig_query_results if key == 0 or
                         compare_rank_with_threshold(q_outcome.baseline_tip_ranks, key, operator_func=operator.le)]
        # computes the number of queries where the rank_th of the expected tip is improved compared to the baseline
        all_stats.queries_got_improved_results[key] = \
            len([q_outcome.number_of_facets_selected for q_outcome in query_results
                 if q_outcome.dfs_tip_rank and
                 compare_rank_with_threshold(q_outcome.baseline_tip_ranks,
                                             q_outcome.dfs_tip_rank, operator_func=operator.lt)])
        all_stats.queries_got_hurt[key] = len(
            [q_outcome.number_of_facets_selected for q_outcome in query_results
             if q_outcome.dfs_tip_rank and q_outcome.number_of_facets_selected > 0 and
             compare_rank_with_threshold(q_outcome.baseline_tip_ranks,
                                         q_outcome.dfs_tip_rank, operator_func=operator.gt)])
        facet_clicks = [q_outcome.number_of_facets_selected
                        for q_outcome in query_results if q_outcome.number_of_facets_selected > 0]
        if len(facet_clicks) > 0:
            all_stats.max_facet_selected[key] = max(facet_clicks)
            all_stats.avg_facet_selected[key] = \
                sum(facet_clicks) / len(facet_clicks)
        all_attempted_queries_ranks = __query_results_to_list_of_tuples(query_results, only_dfs_activated_queries)
        all_stats.baseline_dcg[key], all_stats.dfs_dcg[key] = \
            calculate_dcg(all_attempted_queries_ranks, total_failed_queries)
        all_stats.baseline_mrr[key], all_stats.dfs_mrr[key] = \
            calculate_mrr(all_attempted_queries_ranks, total_failed_queries)
        for n in [1, 5, 10, 20]:
            all_stats.retrieved_at_k_baseline[key][n], all_stats.retrieved_at_k_dfs[key][n] \
                = __retrieved_queries_at_k(query_results, n)
        ''' After ignoring any query with ES (baseline) relevance_rank greater than k '''
        for k in all_stats.k_values:
            query_results = [q_outcome for q_outcome in orig_query_results if
                             compare_rank_with_threshold(q_outcome.baseline_tip_ranks, k, operator_func=operator.le)]
            all_attempted_queries_ranks = __query_results_to_list_of_tuples(query_results, only_dfs_activated_queries)
            all_stats.dcg_at_k_baseline[k], all_stats.dcg_at_k_dfs[k] = \
                calculate_dcg(all_attempted_queries_ranks, total_failed_queries)
            all_stats.mrr_at_k_baseline[k], all_stats.mrr_at_k_dfs[k] = \
                calculate_mrr(all_attempted_queries_ranks, total_failed_queries)
        ''' After ignoring any query where DFS was not activated '''
        if only_dfs_activated_queries:
            query_results = [q_outcome for q_outcome in orig_query_results
                             if q_outcome.dfs_tip_rank and q_outcome.number_of_facets_selected > 0]
        else:
            query_results = orig_query_results
        last_rank_by_query = dict()
        for it in all_stats.iter_values:
            if it == 0:
                all_stats.dcg_at_iter_baseline[it], all_stats.dcg_at_iter_dfs[it] \
                    = all_stats.baseline_dcg[0], all_stats.baseline_dcg[0]
                all_stats.mrr_at_iter_baseline[it], all_stats.mrr_at_iter_dfs[it] = \
                    all_stats.baseline_mrr[0], all_stats.baseline_mrr[0]
            else:
                all_attempted_queries_ranks = list()
                for q_outcome in query_results:
                    # overwrite dfs relevance_rank of the previous iteration
                    if it in q_outcome.dfs_rank_by_iter and q_outcome.dfs_rank_by_iter[it] != 0:
                        last_rank_by_query[q_outcome.query] = q_outcome.dfs_rank_by_iter[it]
                    if q_outcome.query in last_rank_by_query:
                        all_attempted_queries_ranks.append(
                                (q_outcome.baseline_tip_ranks, last_rank_by_query[q_outcome.query]))
                all_stats.dcg_at_iter_baseline[it], all_stats.dcg_at_iter_dfs[it] \
                    = calculate_dcg(all_attempted_queries_ranks, total_failed_queries)
                all_stats.mrr_at_iter_baseline[it], all_stats.mrr_at_iter_dfs[it] \
                    = calculate_mrr(all_attempted_queries_ranks, total_failed_queries)
    all_stats.print_stats()


def __list_to_str(inp_list):
    if inp_list:
        return ",".join(str(i) for i in inp_list)
    return str(None)


def print_ranks(list_of_dfs_outcome):
    tsv_writer = "\n".join(["\t".join([dfs_res.query_id, "\"" + str(dfs_res.query) + "\"",
                                       __list_to_str(dfs_res.get_ranks_for_predicated_results(for_baseline=True)),
                                       __list_to_str(dfs_res.get_ranks_for_predicated_results()),
                                       # str(dfs_res.number_of_facets_selected),
                                       # str(dfs_res.number_of_results_returned),
                                       ", ".join(dfs_res.selected_facets)])
                            for dfs_res in list_of_dfs_outcome])
    header = "\t".join(["Query ID", "Query", "BaseLine_TIP_RANK", "DFS_TIP_RANK",
                        # "Number_Of_Facets_Selected", "Number_Of_Results_Returned",
                        "Selected_Facets (in order)"]) + "\n"
    eval_stats.write(header + tsv_writer, config.temp_path + '/result_ranks.tsv')
