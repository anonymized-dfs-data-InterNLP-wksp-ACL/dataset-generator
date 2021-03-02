import time
from benchmark_evaluator.configurations.connection_settings import Connection
from benchmark_evaluator.util.data_structure import StopConditionThresholds
import benchmark_evaluator.util.evaluator as evaluator
import benchmark_evaluator.experiment.baseline_exp_helper as baseline_exp_helper
import benchmark_evaluator.experiment.dfs_exp_helper as dfs_exp_helper


def run_experiment(data_file, benchmark, query_engine, oracle, use_saved_dfs_results=False, baseline_results_dir=None):
    """

    :param data_file:
    :param benchmark:
    :param query_engine:
    :param oracle:
    :param use_saved_dfs_results:
    :param baseline_results_dir:
    :return:
    """
    print('running experiment with:\n\tdata file: {}\n\tmax results: {}'
          .format(data_file, oracle, Connection.MAX_RESULTS))
    # Step 1: initialize
    start = time.time()
    conn = Connection()
    all_queries_dfs_outcome = list()
    # Step 2: establish baseline
    baseline_results = baseline_exp_helper.get_baseline_results_from_search_engine(
        benchmark, data_file, conn, baseline_results_dir)
    print('there are %d queries in the ground truth' % len(benchmark.queries))
    print('there are %d queries in the baseline results' % len(baseline_results))
    # Step 3: simulate DFS
    for query_id in baseline_results:
        print('\n------------------------------------------\nRunning DFS algorithm for query "%s"' % query_id)
        baseline = baseline_results[query_id]
        dfs_outcome = dfs_exp_helper.simulate_dfs(query_engine, baseline, use_saved_dfs_results,
                                                  oracle, conn)
        if dfs_outcome:
            all_queries_dfs_outcome.append(dfs_outcome)
    # Step 4: collect statistics and generate findings for the evaluation
    total_failed_queries = len(baseline_results) - len(all_queries_dfs_outcome)
    evaluator.print_details_eval_results(all_queries_dfs_outcome, total_failed_queries=total_failed_queries)
    print('\nExperiment completed.\n\nTotal queries with NO DFS results = {}\n\n\n\tfiles:\n\t\tdata file: {}'
          '\n\tstop condition:\n\t\tmax results : {}'
          '\n\t\tmax iteration threshold: {}\n\telapsed time: {:.2f} seconds'
          .format(total_failed_queries, data_file,
                  Connection.MAX_RESULTS, StopConditionThresholds.max_iteration_threshold, time.time() - start))
