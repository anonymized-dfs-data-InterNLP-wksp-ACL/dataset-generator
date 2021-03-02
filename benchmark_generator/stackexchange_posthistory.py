##############################################################
#
# NOTE: the code leverages stackoverflow.com-PostHistory.7z and stackoverflow.com-Posts.7z
# downloaded from https://archive.org/details/stackexchange.
#
###############################################################

import argparse
import json
import urllib.parse
import xml.etree.ElementTree as ET
import re
import gzip
import bz2
import os
import glob
import time
from bs4 import BeautifulSoup
import collections

parser = argparse.ArgumentParser()

parser.add_argument("--posts", default=None, type=str, required=True)
parser.add_argument("--posthistory", default=None, type=str, required=True)
parser.add_argument("--outdir", default=None, type=str, required=True)
parser.add_argument("--before_year", default=2020, type=int)
parser.add_argument("--link_regex", default=None, type=str, required=True)
parser.add_argument("--lowercase_link", action="store_true")
parser.add_argument("--corpus", default='', type=str, required=False)
parser.add_argument("--line_limit", default=-1, type=int)
args = parser.parse_args()

print(f'Using link regex: {args.link_regex}'+(' (lowercased)' if args.lowercase_link else ''))

link_regex = re.compile(args.link_regex)
whitespace = re.compile(r"""\s+""")
start_time = time.time()

def jsonl_lines(input_files, completed_files=None, limit=0, report_every=100000):
    return read_lines(jsonl_files(input_files, completed_files), limit=limit, report_every=report_every)


def jsonl_files(input_files, completed_files=None):
    return expand_files(input_files, '*.jsonl*', completed_files)


def expand_files(input_files, file_pattern='*', completed_files=None):
    """
    expand the list of files and directories
    :param input_files:
    :param file_pattern: glob pattern for recursive example '*.jsonl*' for jsonl and jsonl.gz
    :param completed_files: these will not be returned in the final list
    :return:
    """
    if type(input_files) is str:
        if ':' in input_files:
            input_files = input_files.split(':')
        else:
            input_files = [input_files]
    # expand input files recursively
    all_input_files = []
    if completed_files is None:
        completed_files = []
    for input_file in input_files:
        if input_file in completed_files:
            continue
        if not os.path.exists(input_file):
            raise ValueError(f'no such file: {input_file}')
        if os.path.isdir(input_file):
            sub_files = glob.glob(input_file + "/**/" + file_pattern, recursive=True)
            sub_files = [f for f in sub_files if not os.path.isdir(f)]
            sub_files = [f for f in sub_files if f not in input_files and f not in completed_files]
            all_input_files.extend(sub_files)
        else:
            all_input_files.append(input_file)
    all_input_files.sort()
    return all_input_files


def read_open(input_file):
    """
    Open text file for reading, assuming compression from extension
    :param input_file:
    :return:
    """
    if input_file.endswith(".gz"):
        return gzip.open(input_file, "rt", encoding='utf-8')
    elif input_file.endswith('.bz2'):
        return bz2.open(input_file, "rt", encoding='utf-8')
    else:
        return open(input_file, "r", encoding='utf-8')


def write_open(output_file, *, mkdir=True):
    """
    Open text file for writing, assuming compression from extension
    :param output_file:
    :param mkdir:
    :return:
    """
    if mkdir:
        dir = os.path.split(output_file)[0]
        if dir:
            os.makedirs(dir, exist_ok=True)
    if output_file.endswith('.gz'):
        return gzip.open(output_file, 'wt', encoding='utf-8')
    elif output_file.endswith('.bz2'):
        return bz2.open(output_file, 'wt', encoding='utf-8')
    else:
        return open(output_file, 'w', encoding='utf-8')


def read_lines(input_files, limit=0, report_every=1000000):
    """
    This takes a list of input files and iterates over the lines in them
    :param input_files: Directory name or list of file names
    :param completed_files: The files we have already processed; We won't read these again.
    :param limit: maximum number of examples to load
    :return:
    """
    if type(input_files) is str:
        if ':' in input_files:
            input_files = input_files.split(':')
        else:
            input_files = [input_files]
    count = 0
    for input_file in input_files:
        with read_open(input_file) as reader:
            for line in reader:
                yield line
                count += 1
                if count % report_every == 0:
                    print(f'On line {count} in {input_file}')
                if 0 < limit <= count:
                    return


class ForumPostLinkInst:
    __slots__ = 'qid', 'question_body', 'question_title', 'link_ids'

    def __init__(self):
        self.qid = None
        self.question_body = None
        self.question_title = None
        self.link_ids = None

    def to_json(self):
        jobj = {'id': str(self.qid),
                'title': whitespace.sub(' ', self.question_title),
                'body': self.question_body.replace('\r\n', '\n'),
                'relevant_docids': self.link_ids}
        return json.dumps(jobj)


# load the set of ids in the corpus
if args.corpus:
    doc_ids = dict()
    for line in jsonl_lines(args.corpus):
        jobj = json.loads(line)
        if isinstance(jobj, dict):
            id = jobj['id']
            doc_ids[id.lower() if args.lowercase_link else id] = id
        else:
            for jobji in jobj:
                id = jobji['id']
                doc_ids[id.lower() if args.lowercase_link else id] = id
    print(f'found {len(doc_ids)} doc ids in corpus')
else:
    doc_ids = None


def links_from_answer_text(text: str, doc_ids):
    """
    get ids of documents linked to by the post text
    :param text: text of post to search for links to corpus
    :param doc_ids: the valid ids for documents in the corpus
    :return: ids of documents the post links to, ids that match the regex but are not in the corpus
    """
    if args.lowercase_link:
        text = text.lower()
    link_ids = []
    excluded_link_ids = []
    for m in link_regex.finditer(text):
        docid = m.group(1)
        if docid.endswith('/'):
            docid = docid[:-1]
        docid = urllib.parse.unquote_plus(docid)
        full_docid = docid
        if doc_ids is not None and docid not in doc_ids:
            # maybe we matched a little too much (like an extra close paren)
            for i in range(min(len(docid)-3, 3)):
                docid = docid[:-1]
                if docid in doc_ids:
                    break
        if doc_ids is None:
            link_ids.append(docid)
        elif docid in doc_ids:
            link_ids.append(doc_ids[docid])
        else:
            excluded_link_ids.append(full_docid)
    return link_ids, excluded_link_ids


# Posts.xml: find ids for accepted answers, with id of the question
aid2qid = dict()
for line_ndx, line in enumerate(read_lines(args.posts)):
    if 0 < args.line_limit < line_ndx:
        break
    line = line.strip()
    if not line.startswith('<row '):
        continue
    tree = ET.fromstring(line)
    post_type = int(tree.attrib['PostTypeId'])  # 1 for question, 2 for answer
    if post_type != 1:
        continue
    if 'AcceptedAnswerId' not in tree.attrib:
        continue
    qid = int(tree.attrib['Id'])
    aid = int(tree.attrib['AcceptedAnswerId'])
    aid2qid[aid] = qid
print(f'found {len(aid2qid)} accepted answers')


link_matched_regex_not_in_corpus_count = 0
sample_links_excluded = set()
qid2inst = dict()
# PostHistory.xml: find accepted answer posts with a link of interest, before the cutoff date
for line_ndx, line in enumerate(read_lines(args.posthistory)):
    if 0 < args.line_limit < line_ndx:
        break
    line = line.strip()
    if not line.startswith('<row '):
        continue
    tree = ET.fromstring(line)
    post_type = int(tree.attrib['PostHistoryTypeId'])  # 1 for initial title, 2 for initial body, 4 edit title, 5 edit body
    if post_type not in [1, 2, 4, 5]:
        continue
    id = int(tree.attrib['PostId'])
    if id not in aid2qid:
        continue
    qid = aid2qid[id]
    creation_date_str = tree.attrib['CreationDate']
    year = int(creation_date_str[0:4])
    if year >= args.before_year:
        continue
    text = tree.attrib['Text']
    link_ids, excluded_link_ids = links_from_answer_text(text, doc_ids)
    if len(excluded_link_ids) > 0:
        link_matched_regex_not_in_corpus_count += len(excluded_link_ids)
        if len(sample_links_excluded) < 10:
            sample_links_excluded.add(excluded_link_ids[0])
    if len(link_ids) == 0:
        if qid in qid2inst:
            del qid2inst[qid]
        continue
    # fill in the qid to instance
    inst = ForumPostLinkInst()
    inst.qid = qid
    inst.link_ids = list(set(link_ids))
    qid2inst[qid] = inst
print(f'found {len(qid2inst)} answer posts with link in post history')
if doc_ids is not None:
    print(f'matched {link_matched_regex_not_in_corpus_count} links not in corpus')
    if len(sample_links_excluded) > 0:
        print(f'  sample of excluded links: {sample_links_excluded}')

# PostHistory.xml: find the question title and body for these answers
for line_ndx, line in enumerate(read_lines(args.posthistory)):
    if 0 < args.line_limit < line_ndx:
        break
    line = line.strip()
    if not line.startswith('<row '):
        continue
    tree = ET.fromstring(line)
    post_type = int(tree.attrib['PostHistoryTypeId'])  # 1 for initial title, 2 for initial body, 4 edit title, 5 edit body
    if post_type not in [1, 2, 4, 5]:
        continue
    id = int(tree.attrib['PostId'])
    if id not in qid2inst:
        continue
    creation_date_str = tree.attrib['CreationDate']
    year = int(creation_date_str[0:4])
    if year >= args.before_year:
        continue
    inst = qid2inst[id]
    text = tree.attrib['Text']
    if post_type in [1, 4]:
        inst.question_title = text
    else:
        inst.question_body = BeautifulSoup(text, "html.parser").text  # body sometimes contains html

# now write out qid2inst
train_instances_created = 0
test_instances_created = 0
num_relevant_distribution = collections.Counter()
with write_open(os.path.join(args.outdir, 'train.jsonl.gz')) as train_out, \
     write_open(os.path.join(args.outdir, 'test.jsonl.gz')) as test_out:
    for inst in qid2inst.values():
        if (inst.question_title is None or inst.question_body is None):
            print(f'missing question for {inst.qid}: {inst.question_title[:20]}..., {inst.question_body[:20]}...')
            continue
        num_relevant_distribution[len(inst.link_ids)] += 1
        # ~30% in test, ids with last digit of 0,1,2
        if int(str(inst.qid)[-1]) < 3:
            test_out.write(inst.to_json()+'\n')
            test_instances_created += 1
        else:
            train_out.write(inst.to_json()+'\n')
            train_instances_created += 1
print(f'created {test_instances_created+train_instances_created} instances, '
      f'{train_instances_created} train and {test_instances_created} test')
# CONSIDER: show other stats: avg. length?
print(f'took {(time.time()-start_time)/(60*60)} hours')
distinct_link_counts = list(num_relevant_distribution.keys())
distinct_link_counts.sort()
print(f'Distribution of number of relevant docids')
for lc in distinct_link_counts:
    print(f'  {lc}: {num_relevant_distribution[lc]}')
