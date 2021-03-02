import benchmark_evaluator.search.query_engine_impl as query_engine
import benchmark_evaluator.search.url_comparator as url_comparator
from benchmark_evaluator.util.file_util import FileUtil
from benchmark_evaluator.util.data_structure import SearchResults


def __get_baseline_for_single_query(input_query, conn):
    """

    :param input_query:
    :param conn:
    :return:
    """
    print("\nQuery id: {}\nQuery: {}".format(input_query.id, input_query.query))
    # get facets and search results
    current_search_results = query_engine.get_search_results_with_facets(
        input_query.query, input_query.id, conn, selected_facet_list=None)
    if current_search_results is None:
        return SearchResults(query_text=input_query.query, query_id=input_query.id)
    current_search_results.gold_ans_urls = input_query.ans_docs
    for gold_anw_doc in current_search_results.gold_ans_urls:
        print("Gold Answer: {}".format(gold_anw_doc))
    current_search_results.obtained_ans_url_ranks =\
        url_comparator.get_ans_url_position_in_docs(current_search_results.documents, input_query.ans_docs)
    if current_search_results.obtained_ans_url_ranks:
        for doc_rank in current_search_results.obtained_ans_url_ranks:
            print("Baseline Rank: ", doc_rank.predicted_rank)
    else:
        print("Baseline Rank: NONE")
    current_search_results.query_filename = input_query.query_filename  # the filename of the forum file
    current_search_results.query_context = input_query.query_context
    return current_search_results


def get_baseline_results_from_search_engine(br, data_file, conn, baseline_results_dir):
    """

    :param br:
    :param data_file:
    :param conn:
    :param baseline_results_dir:
    :return:
    """
    # read all the ground truth queries
    br.read_ground_truth(data_file)
    baseline_results = dict()
    for input_query in br.queries:
        query_results = FileUtil.load_baseline_results(input_query.id, baseline_results_dir)
        if query_results:
            print('using existing baseline results for query "%s"' % input_query.id)
        else:
            try:
                query_results = __get_baseline_for_single_query(input_query, conn)
                FileUtil.persist_results(FileUtil.get_baseline_results_filename(
                    input_query.id, baseline_results_dir), query_results)
            except Exception as e:
                print("error getting baseline:", str(e))
                query_results = SearchResults(query_text=input_query.query, query_id=input_query.id)
        baseline_results[input_query.id] = query_results
    return baseline_results
