import os, sys, warnings
from urllib.parse import urljoin
from wsgiref.simple_server import make_server

from markdown import markdown
from bs4 import BeautifulSoup

def merge_iter(*args):
    for arg in args:
        for a in arg:
            yield a

class SitemapApp:
    def __init__(self, indexfile, baseurl, add=[]):
        self.indexfile = indexfile
        self.baseurl = baseurl
        self.add = list(map(lambda x: x.strip(), add))
        
    def __call__(self, environ, start_response):
        try:
            with open(self.indexfile, encoding='UTF-8') as index_fd:
                html = markdown(index_fd.read())
        except IOError:
            print(sys.exc_info())
            start_response("500 Server Error", [], sys.exc_info())
            return b''
            
        soup = BeautifulSoup(html)
        
        start_response('200 OK', [('Content-Type', 'text/plain')])
        
        yield self.baseurl.encode('UTF-8')
        
        urllist = map(lambda x: x["href"], soup.find_all('a', href=True))
        
        yield b'\n'+b'\n'.join(sorted(
            map(lambda x: x.encode('UTF-8'), 
            filter(
                lambda x: x.startswith(self.baseurl), 
                map(lambda x: urljoin(self.baseurl, x), 
                    merge_iter(self.add, urllist))))))


app = application = SitemapApp(os.environ.get("MAP_INDEXFILE"),
                               os.environ.get("MAP_BASEURL"),
                               os.environ.get("MAP_ADD").split(","))

if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=UserWarning, module='bs4')

    server = make_server('', int(os.environ.get('WSGI_PORT', 8001)),
                                 application)
    server.serve_forever()
