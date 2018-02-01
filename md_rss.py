import datetime
import os
import re

RE_TITLE = re.compile(r"title(: |( |)=( |))(.*)\b")
RE_DESC = re.compile(r"description(: |( |)=( |))(.*)\b")
RE_DATE = re.compile(r"date(: |( |)=( |))(.*)\b")

from urllib.parse import urljoin
from wsgiref.simple_server import make_server

import PyRSS2Gen
import dateutil.parser

__version__ = '0.1'

class RssApp:
    def __init__(self, directory, link, **meta):
        self.directory = directory
        self.meta = meta
        self.meta["link"] = link
        if 'description' not in self.meta.keys():
            self.meta["description"] = ""

    def __call__(self, environ, start_response):
        file_names = []
        for path, _, files in os.walk(self.directory):
            for file in files:
                if os.path.splitext(file)[-1] in ('.md', '.mardown'):
                    file_names.append(os.path.join(path, file))

        raw_items = []
        for name in file_names:
            url = urljoin(self.meta["link"],
                          os.path.relpath(name, self.directory))

            with open(os.path.join(name), encoding='utf-8') as fd:
                data = fd.read(1024)

            try:
                date = RE_DATE.findall(data)[0][-1]
            except IndexError:
                continue

            try:
                title = RE_TITLE.findall(data)[0][-1]
            except IndexError:
                continue

            try:
                description = RE_DESC.findall(data)[0][-1]
            except IndexError:
                description = title

            raw_items.append(dict(
                url=url,
                date=date,
                title=title,
                description=description
            ))

        items = [
            PyRSS2Gen.RSSItem(
                title = item["title"],
                description = item["description"],
                link = item["url"],
                guid = item["url"],
                pubDate = dateutil.parser.parse(item["date"])
            ) for item in sorted(
                raw_items, reverse=True, key=lambda x: x["date"])]

        headers = []
        headers.append(('Content-Type', 'application/rss+xml; charset=utf-8'))

        raw_bytes = PyRSS2Gen.RSS2(
            **self.meta,
            lastBuildDate = datetime.datetime.now(),
            items = items
        ).to_xml('utf-8').encode()

        headers.append(
            ('Content-Length', str(
                len(raw_bytes))
             )
        )

        start_response('200 OK', headers)
        
        return [raw_bytes]


app = application = RssApp(os.environ.get("RSS_DIRECTORY"),
                           title=os.environ.get("RSS_TITLE"),
                           link=os.environ.get("RSS_LINK"),
                           description=os.environ.get("RSS_DESCRIPTION"))

if __name__ == "__main__":
    server = make_server('', int(os.environ.get('WSGI_PORT', 8001)),
                                 application)
    server.serve_forever()
