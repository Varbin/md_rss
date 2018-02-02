import os, sys, warnings
from urllib.parse import urljoin
from wsgiref.simple_server import make_server

from markdown import markdown
from bs4 import BeautifulSoup

class SitemapApp:
    def __init__(self, indexfile, baseurl):
        self.indexfile = indexfile
        self.baseurl = baseurl
        
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
        
        for link in soup.find_all('a', href=True):
            abs_url = urljoin(self.baseurl, link['href'])
            if abs_url.startswith(self.baseurl):
                yield b'\n'+abs_url.encode('UTF-8')

app = application = SitemapApp(os.environ.get("MAP_INDEXFILE"),
                               os.environ.get("MAP_BASEURL"))

if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=UserWarning, module='bs4')

    server = make_server('', int(os.environ.get('WSGI_PORT', 8001)),
                                 application)
    server.serve_forever()
