import re

__html_tag = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')


def clean_html(raw_html):
    return re.sub(__html_tag, ' ', raw_html)


def normalize_url(url):
    return url.strip().lower().split("/")[-1].split("=")[-1]


def contains_all_toks(all_toks_in_doc, toks_of_term):
    for t in toks_of_term:
        if t not in all_toks_in_doc:
            return False
    return True


def contains_all_toks_in_text(doc_text, toks_of_term):
    doc_text = doc_text.lower()
    for t in toks_of_term:
        if t not in doc_text:
            return False
    return True


def contains_token(text, facet):
    facet = facet.lower()
    text = text.lower()
    return facet in text or (len(facet) > 4 and
                             ((facet.endswith("s") and facet[:-1] in text) or
                              ((facet.endswith("es") or facet.endswith("ed")) and facet[:-2] in text)))


def contains_facet(text, facet):
    return contains_token(text, facet)


def contains_facet_tokens(text, facet):
    for tok in facet.split():
        if not contains_token(text, tok):
            return False

    return True

