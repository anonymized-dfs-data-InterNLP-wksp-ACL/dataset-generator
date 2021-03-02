import benchmark_evaluator.search.url_comparator as url_comparator
from benchmark_evaluator.util.data_structure import StopConditionThresholds
from benchmark_evaluator.util.file_util import FileUtil


def __is_stop_condition_met(query_outcome, total_candidate_facets_after_last_search,
                            stop_condition=StopConditionThresholds()):
    """

    :param query_outcome:
    :param total_candidate_facets_after_last_search:
    :param stop_condition:
    :return:
    """
    # if number of facets selected (iterations) is greater than the pre-defined threshold
    if query_outcome.number_of_facets_selected >= stop_condition.max_iteration_threshold:
        return True
    # if relevance_rank of dynamic faceted search tip is greater than the pre-defined threshold
    # if query_outcome.dfs_tip_rank and query_outcome.dfs_tip_rank > stop_condition.max_rank_threshold:
    #  return True
    # if there are no more facets to be selected
    if total_candidate_facets_after_last_search == 0:
        return True
    return False


def __run_dfs_for_single_query(query_engine, oracle_obj, current_query_with_results, dfs_outcome, conn):
    """
    Run DFS until the stop condition is met. Throws exception if communication to DFS component fails

    :param query_engine:
    :param oracle_obj:
    :param current_query_with_results:
    :param dfs_outcome:
    :param conn:
    :return:
    """
    # for each query and a selected facet, get facets and search results from DFS component, until stop condition met
    while True:
        new_facet, tmp_results = oracle_obj.select_facet(current_query_with_results, dfs_outcome.selected_facets)
        if new_facet:  # there is a facet that improves the ranking?
            dfs_outcome.selected_facets.append(new_facet)
            if not tmp_results:
                tmp_results = query_engine.get_search_results_with_facets(
                                current_query_with_results.query, current_query_with_results.query_id,
                                conn, selected_facet_list=dfs_outcome.selected_facets)

            # update query results
            current_query_with_results.documents = tmp_results.documents
            current_query_with_results.facets = tmp_results.facets
            current_query_with_results.obtained_ans_url_ranks = url_comparator.get_ans_url_position_in_docs(
                                                                    tmp_results.documents,
                                                                    current_query_with_results.gold_ans_urls)
            # update dfs_outcome
            dfs_outcome.dfs_tip_rank = url_comparator.get_ans_url_position_in_docs(
                                        current_query_with_results.documents, current_query_with_results.gold_ans_urls)
            dfs_outcome.number_of_facets_selected = len(dfs_outcome.selected_facets)
            if dfs_outcome.baseline_tip_ranks:
                print("Baseline: {}".format("".join([str(item) for item in dfs_outcome.baseline_tip_ranks])))
            print("DFS outcome:\n\tTip rank: {}\n\tNum of facets: {}".format(
                        "\n\t".join([str(item) for item in dfs_outcome.dfs_tip_rank]),
                        dfs_outcome.number_of_facets_selected))
            # tracing relevance_rank changes after every facet selection
            dfs_outcome.dfs_rank_by_iter[len(dfs_outcome.selected_facets)] = dfs_outcome.dfs_tip_rank
            rank_by_iter = [[pos, ",".join([str(item) for item in dfs_outcome.dfs_rank_by_iter[pos]])]
                            for pos in dfs_outcome.dfs_rank_by_iter]
            print("Rank by iter:\n\t{}".format(rank_by_iter))
            if __is_stop_condition_met(dfs_outcome, len(current_query_with_results.facets)):
                break  # max tries reached
        else:
            break


def simulate_dfs(query_engine, baseline, use_saved_dfs_results, oracle, conn):
    """

    :param query_engine:
    :param baseline:
    :param use_saved_dfs_results:
    :param oracle:
    :param conn:
    :return:
    """
    dfs_outcome = baseline.to_dfs_outcome()
    if not dfs_outcome.baseline_tip_ranks:
        print('ignoring query "%s" (no baseline_tip_ranks)' % baseline.query_id)
        return None
    existing_dfs_outcome = None
    if use_saved_dfs_results is True:
        existing_dfs_outcome = FileUtil.load_dfs_results(baseline.query_id)  # cache
    if existing_dfs_outcome:
        print('using existing DFS results for query "%s"' % baseline.query_id)
        return existing_dfs_outcome
    elif 1 not in dfs_outcome.get_ranks_for_predicated_results(for_baseline=True):
        try:
            __run_dfs_for_single_query(query_engine, oracle, baseline, dfs_outcome, conn)
            FileUtil.persist_results(FileUtil.get_dfs_results_filename(baseline.query_id), dfs_outcome)
            print("DFS (ans url) relevance_rank: ", str(dfs_outcome.get_ranks_for_predicated_results()))
        except Exception as e:
            print('exception running DFS for query "%s": %s' % (baseline.query_id, str(e)))
    return dfs_outcome
