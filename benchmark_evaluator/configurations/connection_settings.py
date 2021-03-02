class Connection:
    USERNAME = ""
    PASSWORD = ""

    SEARCH_ENGINE = "es"
    SERVER = ""
    COLL = ""

    MAX_FACETS = 5
    MAX_RESULTS = 100
    SEARCH_SERVICE_URL = ""

    @staticmethod
    def __get_search_service():
        return "/corpus/%s/faceted_search" % Connection.COLL

    PORT = "5555"

    @staticmethod
    def get_search_service_url():
        return "http://" + Connection.SERVER + ":" + Connection.PORT + Connection.__get_search_service()

    DEFAULT_POSITIVE_RELEVANCE_JUDGEMENT = "1.0"
    DEFAULT_PARAMS = "page_size=" + str(MAX_RESULTS)

    FEATURES_SERVICE = "/corpus/%s/get_qf_feature_vectors" % COLL
    FEATURES_SERVICE_URL = "http://" + SERVER + ":" + PORT + FEATURES_SERVICE



