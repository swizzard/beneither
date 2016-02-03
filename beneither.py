#!/home/ubuntu/beneither/venv/bin/python
from datetime import datetime
import json
from random import randrange
import re
import sys
import time

from wordfilter import Wordfilter
from spacy.en import English
from twython import Twython
from twython.exceptions import TwythonError



def get_client(cfg_path):
    with open(cfg_path) as cfg_fil:
        cfg = json.load(cfg_fil)
    return Twython(app_key=cfg['consumer_key'],
                   app_secret=cfg['consumer_secret'],
                   oauth_token=cfg['token'],
                   oauth_token_secret=cfg['secret'])


def prep(tweet):
    txt = tweet['text'].lower()
    return re.sub(r'^rt @[\w\d]+:?', '', txt)


def search(client, search_str):
    try:
        res = client.search(q=search_str, include_entities=False, count=100,
                            result_type='recent')
        return [prep(tweet) for tweet in res['statuses']]
    except TwythonError as err:
        print '{} {}'.format(datetime.now(), err.message)
        return []


def get_spans(doc):
    spans = []
    in_span = False
    be_orth = doc.vocab.strings["'m"]
    not_orth = doc.vocab.strings['not']
    idx = 0
    while idx < len(doc):
        token = doc[idx]
        if in_span:
            span = doc[idx:token.head.right_edge.i + 1]
            if span:
                if span[-1].pos_ in ('CONJ', 'PUNCT'):
                    span = span[:-1]
                if span[0].orth == not_orth:
                    span = span[1:]
                spans.append(span.text)
                idx = span[-1].i + 1
                in_span = False
            else:
                idx += 1
                in_span = False
        else:
            if token.orth == be_orth:
                in_span = True
            idx += 1
    return spans


def get_np(span):
    mtch = re.match(r'i\'m.*?a ([\w\s+]+)', span.string)
    if mtch:
        return mtch.group(1)


def retrieve_spans(client, nlp):
    return [get_spans(nlp(txt)) for txt in
            search(client, '"i\'m not a" "i\'m a"')]


def get_antonyms(spans, wordfilter):
    ants = []
    for sp in spans:
        nps = []
        for span in sp:
            np = get_np(span)
            if np is not None:
                np = np.strip()
                if not wordfilter.blacklisted(np):
                    nps.append(np)
        if len(nps) >= 2:
            ants.append(nps)
    return ants


def assemble_tweets(antonyms, seen):
    if len(antonyms) >= 2:
        ants = []
        while len(ants) < 2:
            ants = [ant for ant in antonyms.pop(randrange(0, len(antonyms))) if ant]
            if tuple(ants) in seen:
                ants = []
        else:
            seen.add(tuple(ants))
            yield {'status': 'Neither a {} nor a {} be'.format(*ants[:2])}
    else:
        raise StopIteration


def run(client, nlp, wordfilter):
    spans = retrieve_spans(client, nlp)
    antonyms = get_antonyms(spans, wordfilter)
    seen = set()
    while True:
        for tweet in assemble_tweets(antonyms, seen):
            try:
                print '{}: tweet'.format(datetime.now())
                client.update_status(**tweet)
            except Exception as err:
                if 'Status is a duplicate' in err.message:
                    print 'duplicate'
                    continue
            else:
                time.sleep(2100)
        else:
            print 'reset'
            spans = retrieve_spans(client, nlp)
            antonyms = get_antonyms(spans, wordfilter)
            seen = set()


if __name__ == '__main__':
    cfg = sys.argv[1]
    client = get_client(cfg)
    nlp = English()
    wordfilter = Wordfilter()
    run(client, nlp, wordfilter)

