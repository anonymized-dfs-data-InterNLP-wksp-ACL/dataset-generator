import json
from benchmark_evaluator.util.data_structure import Benchmark, InputQuery, GoldAnsDoc

# =========== All sub-classes of Benchmark should be here below ======================================


class CommonFormatBenchmark(Benchmark):
    """
    Benchmark reader for common jsonl format
    """
    def read_ground_truth(self, data_file, max_queries=None):
        if data_file.find('.jsonl') >= 0:
            with open(data_file) as json_file:
                json_list = list(json_file)

            for json_str in json_list:
                item = json.loads(json_str)
                new_query = InputQuery()
                new_query.id = item['id']
                new_query.query = item['contents'].split("\n")[0]
                print(new_query.query)
                new_query.query_context = ""    # TODO: item['contents_extended']
                gold_doc_ids = item['relevant_docids']
                for r in gold_doc_ids:
                    ans_url = GoldAnsDoc()
                    # use default rank
                    ans_url.rank = 1
                    ans_url.ans_url = ""
                    ans_url.url_id = r.strip()
                    new_query.ans_docs.add(ans_url)
                self.queries.append(new_query)
            print("Ground Truth: number of queries", len(self.queries))
        return

