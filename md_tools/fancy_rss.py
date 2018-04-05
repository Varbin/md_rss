#!/usr/bin/env python3

import os
import sys
import traceback
import time

from datetime import datetime
from wsgiref.simple_server import make_server

try:
    from defusedxml import defuse_stdlib
except ImportError:
    pass  # Minor security, as only trusted feed should be parsed


from bs4 import BeautifulSoup
from bs4.element import Comment

import feedparser

cache = {}



DEFAULT_TEMPLATE = """\
<!doctype html>
<html>
    <head>
        <title>Fancy-RSS</title>
        <meta charset="UTF-8">
    </head>
    <body>
        {content}
    </body>
</html>
"""

TEMPLATE_SAFE = """\
<h2><a href="{link}">{escaped_entry_title}</a></h2>
<p><time>{date}</time> <i>//</i> <b>{escaped_feed_title}</b></p>
<iframe srcdoc="{attrescaped_html}" sandbox="allow-forms allow-popups">
<p>{safe_text}</p>
</iframe>
"""

TEMPLATE_UNSAFE = """\
<h2><a href="{link}">{escaped_entry_title}</a></h2>
<p><time>{date}</time> <i>//</i> <b>{escaped_feed_title}</b></p>
<p>{attrescaped_html}</p>
"""


safe_html = {
    "<" : "&lt;",
    ">" : "&gt;",
}

safe = {
    "&" : "&amp;"
}

safe_attr = {
    "\"" : "&quot;",
    "'" : "&#39;"
}

feed = feedparser.parse('https://sbiewald.de/index.rss')
details = feed.feed


def tag_visible(element):
    # Source: https://stackoverflow.com/a/1983219
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

def text_from_html(body):
    # Source: https://stackoverflow.com/a/1983219
    soup = BeautifulSoup(body, 'html.parser')
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)  
    return u" ".join(t.strip() for t in visible_texts)


def get_date(obj):
    return (
        getattr(obj, "published_parsed", None) or
        getattr(obj, "updated_parsed", None)
    )

def multi_replace(text, dictionary):
    for key, value in dictionary.items():
        text = text.replace(key, value)
    return text

def parse_feeds(feeds=(), cache={}):
    parsed_feeds = []
    for feed in feeds:
        cached = cache.get(feed)
        etag = getattr(cached, "etag", None)
        modified = getattr(cached, "updated", None) or getattr(
            cached, "headers", {}).get("Expires")

        try:
            parsed = feedparser.parse(feed, modified=modified, etag=etag)
            if parsed.status != 200:
                if parsed.status != 304:
                    sys.stderr.write("Site error: status {} at {}\n".format(
                        parsed.status, feed))
                parsed = cached

        except Exception:  # Crash prevention
            parsed = cached
            traceback.print_exc(file=sys.stderr)

        if parsed is None:
            sys.stderr.write("No cache hit and not data for {}\n".format(
                feed))
            continue

        cache[feed] = parsed

        for entry in parsed.entries[:3]:
            parsed_feeds.append([entry, parsed.feed])

    return sorted(parsed_feeds, key=lambda x: get_date(x[0]),
                  reverse=True)


def render_entry(entry, feed, unsafe=False):
    if unsafe:
        temp = TEMPLATE_UNSAFE
    else:
        temp = TEMPLATE_SAFE
    return temp.format(
        escaped_entry_title=multi_replace(entry.title, safe_html),
        date=time.strftime('%Y-%m-%dT%H:%M', get_date(entry)),
        link=multi_replace(
            multi_replace(entry.link, safe), safe_attr),
        escaped_feed_title=multi_replace(feed.title, safe_html),
        attrescaped_html=multi_replace(entry.summary, safe_attr),
        safe_text=text_from_html("<p>"+entry.summary+"</p>"),
    )


class FeedApp:
    cache = {}
    def __init__(self, feeds, template=None, template_file=None, unsafe=False):
        if template and template_file:
            raise AttributeError("template or template_file")
        elif template:
            self.template = template
        elif template_file:
            self.template = template_file.read()
        elif not template and not template_file:
            self.template = DEFAULT_TEMPLATE

        if type(feeds) == str:
            raise AttributeError(
                "pass an iterable of feeds, not a single string")
        self.feeds = feeds
        self.unsafe = unsafe

    def __call__(self, environ, start_response):
        html = ""
        parsed = parse_feeds(self.feeds, self.cache)
        for entry, feed in parsed:
            html += render_entry(entry, feed, self.unsafe)

        rendered = self.template.format(content=html).encode('UTF-8')

        headers = []
        headers.append(('Content-Type', 'text/html; charset=utf-8'))
        headers.append(('Content-Length', str(len(rendered))))

        start_response('200 OK', headers)
        
        return [rendered]

if __name__ == "__main__":
    server = make_server('', int(os.environ.get('WSGI_PORT', 8003)),
                                 FeedApp(['https://sbiewald.de/index.rss']))
    server.serve_forever()
