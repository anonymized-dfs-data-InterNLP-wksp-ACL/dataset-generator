import json
import os
import benchmark_evaluator.configurations.config as config

from benchmark_evaluator.util.data_structure import SearchResults
from benchmark_evaluator.util.data_structure import FacetedSearchOutcome


class FileUtil:

    @staticmethod
    def load_json_data(filename):
        with open(filename, 'r', encoding='utf-8') as fn:
            return json.load(fn)

    @staticmethod
    def write_json_data(json_data, output_file):
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=4)

    @staticmethod
    def get_baseline_results_filename(query_id, baseline_results_dir):
        if not baseline_results_dir:
            baseline_results_dir = config.temp_path + "/" + config.Results_DIR_Name
        return os.path.join(baseline_results_dir, '%s_baseline_results.json' % query_id)

    @staticmethod
    def get_dfs_results_filename(query_id):
        return os.path.join(config.temp_path + "/" + config.Results_DIR_Name, '%s_dfs_results.json' % query_id)

    @staticmethod
    def load_baseline_results(query_id, baseline_results_dir):
        return FileUtil.__load_search_results(
            FileUtil.get_baseline_results_filename(query_id, baseline_results_dir), SearchResults)

    @staticmethod
    def load_dfs_results(query_id):
        return FileUtil.__load_search_results(FileUtil.get_dfs_results_filename(query_id), FacetedSearchOutcome)

    @staticmethod
    def __load_search_results(query_results_filename, results_class):
        if os.path.isfile(query_results_filename):
            with open(query_results_filename) as query_results_file:
                return results_class.deserialize(json.loads(query_results_file.read()))
        return None

    @staticmethod
    def persist_results(query_results_filename, baseline_results):
        """
        works for both SearchResults and FacetedSearchOutcome

        :param query_results_filename:
        :param baseline_results:
        :return:
        """
        serialized_results = baseline_results.serialize()
        if serialized_results:
            with open(query_results_filename, 'w') as query_results_file:
                query_results_file.write(serialized_results)
