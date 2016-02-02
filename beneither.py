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


def search(client, search_str):
    try:
        res = client.search(q=search_str, include_entities=False, count=100,
                            result_type='recent')
        return [tweet['text'].lower() for tweet in res['statuses']]
    except TwythonError as err:
        print '{} {}'.format(datetime.now(), err.message)
        return []


def get_spans(doc):
    get_max = lambda x: min(x + 1, len(doc) - 1)
    not_username = lambda t: t.prefix != doc.vocab.strings['@']
    spans = []
    curr_start = None
    curr_end = 0
    in_span = False
    curr_head = None
    i_idx = doc.vocab.strings['i']
    be_orth = doc.vocab.strings["'m"]
    comb_orth = doc.vocab.strings["i'm"]
    for idx, token in enumerate(doc):
        if not_username(token):
            if token.lemma == i_idx:
                nxt = doc[get_max(idx)]
                if nxt.orth == be_orth:
                    in_span = True
                    curr_head = nxt
            elif token.orth == comb_orth:
                in_span = True
                curr_head = token
            elif curr_head not in {token.head, token.head.head, token, None}:
                in_span = False
            if in_span:
                if curr_start is None:
                    curr_start = idx
                curr_end = idx
            else:
                if curr_start is not None:
                    end = get_max(curr_end)
                    span = doc[curr_start:end]
                    if span:
                        spans.append(span)
                    curr_start = None
    if curr_start:
        span = doc[curr_start:]
        if span:
            spans.append(span)
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

