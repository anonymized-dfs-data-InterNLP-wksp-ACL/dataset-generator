import urllib
import time
import requests
from requests.auth import HTTPBasicAuth
from benchmark_evaluator.util.data_structure import TypedFacet, Facet, SearchResults, Doc
from abc import ABC


class QueryEngine(ABC):
    """
        Abstract class for query engine to connect to the DFS component and the search engine inside the DFS component
    """

    # abstract method
    def get_search_results_with_facets(self, query, query_id, conn, selected_facet_list, use_facets_as_filters=True):
        """
            Retrieve both documents and dynamic facets suggested by the DFS component, given a query
        """
        pass


class ExampleQueryEngine(QueryEngine):
    @staticmethod
    def __append_common_params(conn, query, topic_similarity_threshold,
                               query_field_name="", use_facets_as_filters=True):
        """
        Append query parameters
        """
        return "&".join(["",
                         "query=" + urllib.parse.quote(query),
                         "json=true",
                         "search_engine=" + conn.SEARCH_ENGINE,
                         "query_field_name=" + query_field_name,
                         "results_limit=" + str(conn.MAX_RESULTS),
                         "flat_dfs_q_facets=" + str(conn.MAX_FACETS),
                         "use_facets_as_filters=" + str(use_facets_as_filters),
                         "topic_similarity_threshold=" + str(topic_similarity_threshold)])

    def get_search_results_with_facets(self, query, query_id, conn, selected_facet_list, use_facets_as_filters=True):
        query_with_results = SearchResults(query_text=query, query_id=query_id)
        search_result = ExampleQueryEngine.__es_search(query, conn, facet_list=selected_facet_list, use_facets_as_filters=use_facets_as_filters)

        documents_results = ExampleQueryEngine.__get_documents(search_result)
        if documents_results and len(documents_results) > 0:
            for i, doc_item in enumerate(documents_results):
                doc = Doc()
                if "text" in doc_item:
                    doc.full_text = doc_item["text"].strip()
                else:
                    doc.full_text = doc_item["head"].strip()
                if "title" in doc_item:
                    doc.title = doc_item["title"].strip()
                else:  # generate title from full text, if missing in search result
                    doc.title = doc.full_text.strip().split("\n")[0].strip()
                if "original_id" in doc_item:
                    doc.original_id = doc_item["original_id"].strip()
                if "doc_id" in doc_item and len(doc_item["doc_id"].strip()) > 0:
                    doc.original_id = doc_item["doc_id"].strip()
                doc.url = doc_item["url"].strip()
                doc.search_rank = int(doc_item["rank"])
                doc.search_score = float(doc_item["search_engine_score"])
                query_with_results.documents.append(doc)
            facets = ExampleQueryEngine.__get_facets(search_result)
            query_with_results.facets = facets
            query_with_results.number_of_documents = len(documents_results)
        return query_with_results

    @staticmethod
    def __es_search(query, conn, facet_list=None, topic_similarity_threshold=0.5, use_facets_as_filters=True):
        """
        Uses vanilla ES as search engine
        """
        print("\nSearching (query_id '%s')" % query)
        query_with_params = ExampleQueryEngine.__append_common_params(conn, query, topic_similarity_threshold,
                                                   query_field_name="natural_language_query",
                                                   use_facets_as_filters=use_facets_as_filters)
        if facet_list:
            query_with_params += "".join(["&facet=" + urllib.parse.quote(f) for f in facet_list])
        query_with_params += "&extra_fields[]=doc_id"
        print(query_with_params)
        return ExampleQueryEngine.__query_service(conn.get_search_service_url(), query_with_params, conn)

    @staticmethod
    def __get_documents(json_output):
        """
        Given json results, gets the documents_from_search_results
        """
        if json_output:
            docs = json_output['documents']
            print("Got total docs: ", len(docs))
            return docs
        else:
            return None

    @staticmethod
    def __get_facets(json_output, debug=False):
        """
        Given json results, gets the facets
        """
        tot_facet = 0
        if json_output:
            facet_to_doc_map = dict()
            if 'facet_to_doc_map' in json_output:
                for f in json_output['facet_to_doc_map']:
                    facet_to_doc_map[f] = json_output['facet_to_doc_map'][f]
            facets = list()
            if 'facets_tree' in json_output:
                facet_structure = json_output['facets_tree']
                for facet_group in facet_structure:
                    typed_facet = TypedFacet()
                    typed_facet.facet_type = facet_group['id']
                    for f in facet_group['facets']:
                        new_facet = Facet()
                        new_facet.text = f['name']
                        new_facet.score = f['score']
                        if 'pervasive_score_in_search_results' in f:
                            new_facet.pervasive_score = f['pervasive_score_in_search_results']
                        if 'relevance_score_in_search_results' in f:
                            new_facet.relevance_score = f['relevance_score_in_search_results']

                        if f['id'] in facet_to_doc_map:
                            new_facet.mapped_doc_ranks = facet_to_doc_map[f['id']]
                        typed_facet.facet_ind.append(new_facet)
                        tot_facet += 1
                    typed_facet.facet_ind.sort(key=lambda x: x.score, reverse=True)
                    facets.append(typed_facet)
            elif 'facets' in json_output:
                facet_scores = json_output['facet_scores']
                facet_structure = json_output['facets']
                for key in facet_structure:
                    typed_facet = TypedFacet()
                    typed_facet.facet_type = key
                    for f in facet_structure[key]:
                        new_facet = Facet()
                        new_facet.text = f
                        new_facet.score = facet_scores[f]
                        typed_facet.facet_ind.append(new_facet)
                        if f in facet_to_doc_map:
                            new_facet.mapped_doc_ranks = facet_to_doc_map[f]
                        tot_facet += 1
                    typed_facet.facet_ind.sort(key=lambda x: x.score, reverse=True)
                    facets.append(typed_facet)
            if debug:
                print("Got total facets: ", tot_facet)
            return facets
        return list()

    @staticmethod
    def __query_service(service, query_with_params, conn, debug=True):
        """
        Generic query service
        """
        furl = service
        if query_with_params:
            furl += "?" + conn.DEFAULT_PARAMS + query_with_params
        if debug:
            print("CALL: ", furl)
        start = time.time()
        r = requests.get(furl, auth=HTTPBasicAuth(conn.USERNAME, conn.PASSWORD))
        print('__query_service("%s") took %d seconds' % (furl, time.time() - start))
        if debug:
            print("status code", r.status_code)
            print("encoding: ", r.encoding)
        json_obj = ""
        try:
            json_obj = r.json()
        except ValueError:
            print("WARNING: Cannot get JSON")
        if debug:
            print("query service returned")
        return json_obj
