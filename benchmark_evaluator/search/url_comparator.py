from benchmark_evaluator.util.data_structure import DocRank
import benchmark_evaluator.util.misc_util as misc_util


def get_ans_url_position_in_docs(docs_in_search_result, gold_documents):
    """
    :param docs_in_search_result:
    :param gold_documents:
    :return:
    """
    obtained_ans_url_ranks = set()
    for gold_doc in gold_documents:
        # normalizing url by keeping only the last part (i.e. the actual page name) instead of full url
        norm_gold_url = misc_util.normalize_url(gold_doc.ans_url)
        for i in range(len(docs_in_search_result)):
            doc = docs_in_search_result[i]
            # normalizing url by keeping only the last part (i.e. the actual page name) instead of full url
            norm_doc_url = misc_util.normalize_url(doc.url)
            # if the doc url is same as EITHER gold url OR gold url id,
            # OR the doc original id (i.e. uid) is same as gold url id
            if norm_doc_url == norm_gold_url \
                    or norm_doc_url == gold_doc.url_id\
                    or doc.original_id == gold_doc.url_id:
                result_rank = DocRank(i + 1, gold_doc.relevance_rank)
                obtained_ans_url_ranks.add(result_rank)
    return obtained_ans_url_ranks
