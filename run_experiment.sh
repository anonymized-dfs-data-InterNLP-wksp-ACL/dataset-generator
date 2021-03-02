#!/usr/bin/env bash

export PYTHONPATH="${PYTHONPATH}:$PWD"
out_dir="YOUR_RESULT_FILES_WILL_BE_STORED_HERE"
baseline_results_dir="YOUR_INITIAL_DOCUMENT_RANKING_SEARCH_RESULTS_WITHOUT_DFS_WILL_BE_STORED_HERE"
rm -rf $out_dir
rm -rf $baseline_results_dir
python3 -m benchmark_evaluator.experiment.main \
       --test_data YOUR_BENCHMARK_DATA_FILE_IN_JSONL_FORMAT \
       --baseline_results_dir $baseline_results_dir \
       --coll YOUR_INDEXED_COLLECTION_ID \
       --out_dir $out_dir