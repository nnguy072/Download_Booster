"""
Very simple HTTP server in python.
Usage::
    ./dummy-web-server.py [<port>]
Send a GET request::
    curl http://localhost
Send a HEAD request::
    curl -I http://localhost
Send a POST request::
    curl -d "foo=bar&bin=baz" http://localhost
"""
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
import os
from os import curdir, sep, stat

class S(BaseHTTPRequestHandler):
    def _set_headers(self):
        test = os.path.getsize(curdir + sep + self.path)    #content-length
        self.send_response(200)
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-Length', test)
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        f = open(curdir + sep + self.path)
        self.wfile.write(f.read())

    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
        # Doesn't do anything with posted data
        self._set_headers()
        self.wfile.write("<html><body><h1>POST!</h1></body></html>")

def run(server_class=HTTPServer, handler_class=S, port=80):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print 'Starting httpd...'
    httpd.serve_forever()

if __name__ == "__main__":
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()