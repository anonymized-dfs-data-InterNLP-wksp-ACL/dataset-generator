import argparse
import benchmark_evaluator.experiment.orchestrator as orchestrator
import benchmark_evaluator.configurations.config as config
import benchmark_evaluator.configurations.connection_settings as connection_settings
import os
import shutil
from benchmark_evaluator.oracles_impl.oracle import OracleSimulator as OracleSimulator
from benchmark_evaluator.search.query_engine_impl import ExampleQueryEngine as ExampleQueryEngine
from benchmark_evaluator.data.benchmark_reader import CommonFormatBenchmark


def __fetch_boolean_value(param_value):
    if param_value.lower() == "true":
        return True
    else:
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline_results_dir", default="", type=str,
                        help="Pre-generated search results for baseline")
    parser.add_argument("--out_dir", default="", type=str, help="Output folder name")
    parser.add_argument("--coll", default="", type=str, help="Search Engine Collection name")
    parser.add_argument("--test_data", default="", type=str,
                        help="File containing test queries with desired document IDs/URLs")
    args = parser.parse_args()
    test_data = args.test_data

    if len(args.coll.strip()) > 0:
        connection_settings.Connection.COLL = args.coll.strip()
    if len(args.out_dir.strip()) > 0:
        config.temp_path = args.out_dir.strip()
    else:
        config.temp_path += "_" + args.oracle.lower()
    if not os.path.exists(config.temp_path):
        os.makedirs(config.temp_path)

    baseline_results_dir = args.baseline_results_dir

    if baseline_results_dir and not os.path.exists(baseline_results_dir):
        os.makedirs(baseline_results_dir)
        # if baseline is new, delete old dfs results
        if os.path.exists(config.temp_path + "/" + config.Results_DIR_Name):
            shutil.rmtree(config.temp_path + "/" + config.Results_DIR_Name)

    if not os.path.exists(config.temp_path + "/" + config.Results_DIR_Name):
        os.makedirs(config.temp_path + "/" + config.Results_DIR_Name)

    orchestrator.run_experiment(test_data,
                                benchmark=CommonFormatBenchmark(),
                                query_engine=ExampleQueryEngine(),
                                oracle=OracleSimulator(),
                                baseline_results_dir=baseline_results_dir)


if __name__ == "__main__":
    main()


