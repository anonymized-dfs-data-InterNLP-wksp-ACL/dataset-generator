# Accompanying codes with the InterNLP 2021 submission

These codes are being provided as supplementary material with the following paper submitted in InterNLP 2021 -

`Dynamic Facet Selection by Maximizing Graded Relevance`

The codes will be released publicly and be hosted in github.com, if the paper gets accepted.
We will add more documentation later when the codes will be publicly released.

There are two sets of codes.
- `benchmark_generator` contains codes for benchmark data creation from Stackoverflow-Technotes, an IT domain specific IR benchmark data from Stackoverflow public forums and IBM Technotes corpus.
- `benchmark_evaluator` contains codes for simulating DFS experiments.

## Stackoverflow-Technotes benchmark creation (automatically)
First download the TechQA technote corpus (which contains `full_technote_collection.txt.bz2`) from https://leaderboard.techqa.us-east.containers.appdomain.cloud/
This requires a free registration.

This script will download the forum post histories from `archive.org`. The files downloaded are `stackoverflow.com-Posts.7z` (15.1GB) and `stackoverflow.com-PostHistory.7z` (26.5 GB).
Run it in the same directory that you downloaded `full_technote_collection.txt.bz2`. It will produce the dataset with a train and test split.
You must have 7z installed (`sudo apt-get install p7zip-full`).

```sh benchmark_generator/run_generator.sh```

## Automatic simulated evaluation of Dynamic Faceted Search Appraoches

Use the following script to run the experiments. Before running the script, set the correct parameter values for input/output file or directory paths.

```sh run_experiment.sh```

If you already have a `.tsv` file generated with the results, then run -

```python -m benchmark_evaluator.util.results_reader YOUR_TSV_FILE_PATH```

The format of each line in the `.tsv` file should be as following -

`Query ID`\t`Query`\t`BaseLine_TIP_RANK`\t`DFS_TIP_RANK`\t`Selected_Facets (in order)`


The following output files will be written inside `resources\tmp` folder.

### Results for all queries -

- `summary_hits.csv` : Contains summary results for all queries

- `result_ranks.tsv` : Contains results for each individual query

### Results for queries for which DFS was activated  -

- `summary_per_iteration.csv` : Stats are calculated by restricting number of iterations, i.e. number of max. facet selection by oracle

- `bottom_queries_summary.csv` : *(view at BOTTOM)* Stats calculated by restricting to those queries for which the baseline (ES) rank for the desired document (in the returned results) is greater than than a threshold rank

- `top_queries_summary.csv` : *(view at TOP)* Stats calculated by restricting to those queries for which the baseline (ES) rank for the desired document (in the returned results) is at k or lower
