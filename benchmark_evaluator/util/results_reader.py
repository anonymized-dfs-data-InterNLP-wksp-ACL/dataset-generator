import sys
import re
from benchmark_evaluator.util.data_structure import FacetedSearchOutcome
import benchmark_evaluator.util.evaluator as evaluator
from benchmark_evaluator.search.url_comparator import DocRank


def read_results(filename):
    _idx_query_id = 0
    _idx_query_text = 1
    _idx_baseline_results = 2
    _idx_dfs_results = 3
    _idx_selected_facets = 4

    dfs_outcome_by_query_id = list()
    _total_queries = 0

    if len(filename) > 0:
        with open(filename, "r") as fn:
            for line in fn.readlines():
                tmp = line.strip().split("\t")
                if len(tmp) < 4:
                    print("Invalid file content format")
                    return dfs_outcome_by_query_id

                ignore_line = False
                _total_queries += 1
                for _idx in [_idx_baseline_results, _idx_dfs_results]:
                    tmp[_idx] = tmp[_idx].replace("[", "").replace("]", "").strip()
                    if tmp[_idx] == "":
                        tmp[_idx] = "-1"

                    tmp[_idx] = \
                        re.split(r"\s+", tmp[_idx].replace(",", " ").replace("None", "-1"))

                    if not tmp[_idx][0].replace("-", "").isdigit():
                        print(tmp[_idx][0])
                        ignore_line = True
                        break
                    tmp[_idx] = [int(x) for x in tmp[_idx]]

                if ignore_line or tmp[_idx_baseline_results].count(-1) == len(tmp[_idx_baseline_results]):
                    continue

                _number_of_facets_selected = 0
                if len(tmp) >= 5 and 'None' not in tmp[_idx_selected_facets]:
                    _number_of_facets_selected = len(tmp[_idx_selected_facets].split(","))
                dfs_outcome = FacetedSearchOutcome.init_dfs_outcome(
                    query_text=tmp[_idx_query_text], query_id=tmp[_idx_query_id],
                    baseline_rank=tmp[_idx_baseline_results],
                    dfs_rank=tmp[_idx_dfs_results],
                    number_of_facets_selected=_number_of_facets_selected)

                current_baseline_rank = min([w.predicted_rank for w in dfs_outcome.baseline_tip_ranks])
                if current_baseline_rank == 1:
                    dfs_outcome.dfs_tip_rank = [DocRank(-1, 1)]
                    dfs_outcome.number_of_facets_selected = 0

                dfs_outcome_by_query_id.append(dfs_outcome)

    return dfs_outcome_by_query_id, _total_queries


if __name__ == "__main__":

    input_filename = ""

    for arg in sys.argv[1:]:
        input_filename = arg
        break

    all_queries_dfs_outcome, total_queries = read_results(input_filename)

    #  calculate evaluation results and print
    evaluator.print_details_eval_results(all_queries_dfs_outcome,
                                         total_failed_queries=total_queries-len(all_queries_dfs_outcome))
