
import socket, thread, select, os, sys

__version__ = '0.1.0 Draft 1'
BUFLEN = 8192
VERSION = 'Python Proxy/'+__version__
HTTPVER = 'HTTP/1.1'

class ConnectionHandler:
    def __init__(self, connection, address, timeout):
        self.client = connection
        self.client_buffer = ''
        self.timeout = timeout
        self.range1 = ""
        self.range2 = ""
        #print the request and it extracts the protocol and path
        self.method, self.path, self.protocol = self.get_base_header()

        if self.method=='CONNECT':
            self.method_CONNECT()

        #handle the GET request
        elif self.method in ('OPTIONS', 'GET', 'HEAD', 'POST', 'PUT',
                             'DELETE', 'TRACE'):
            self.method_others()

        self.client.close()
        self.target.close()

    def get_base_header(self):
        while 1:
            self.client_buffer += self.client.recv(BUFLEN)
            end = self.client_buffer.find('\n')
            if end!=-1:
                break

        #print the request
        print '%s'%self.client_buffer[:end]

        data = (self.client_buffer[:end+1]).split()
        self.client_buffer = self.client_buffer[end+1:]
        return data

    def method_CONNECT(self):
        self._connect_target(self.path)
        self.client.send(HTTPVER+' 200 Connection established\n'+
                         'Proxy-agent: %s\n\n'%VERSION)
        self.client_buffer = ''
        self._read_write()

    #forward the packet to its final destination
    def method_others(self):
        self.path = self.path[7:]
        i = self.path.find('/')
        host = self.path[:i]
        path = self.path[i:]
        self._connect_target(host)

        # CHANGE TO HEAD REQUEST TO GET CONTENT LENGTH
        self.method = "HEAD"
        self.target.send('%s %s %s\n'%(self.method, path, self.protocol) + self.client_buffer)
        self.client_buffer = ''
        self._read_write()

    def _connect_target(self, host):
        i = host.find(':')
        if i!=-1:
            port = int(host[i+1:])
            host = host[:i]
        else:
            port = 80
        (soc_family, _, _, _, address) = socket.getaddrinfo(host, port)[0]
        self.target = socket.socket(soc_family)
        self.target.bind(('10.25.1.210',0)) #device 1
        self.target.connect(address)

        #TODO: change for different interfaces i.g. wifi & ethernet
        self.target2 = socket.socket(soc_family)
        self.target2.bind(('10.25.1.210',0)) #device 2
        self.target2.connect(address)

    #trims header off of packet
    def remove_header(self, data):
        index = data.find("\r\n\r\n", 0) + 4
        return data[index:]

    #sends two requests with different ranges
    def sendRangeRequests(self):
        i = self.path.find('/')
        host = self.path[:i]
        path = self.path[i:]
        self.method = "GET"
        print "Sending requests..."
        self.target.send('%s %s %s\r\nHost:%s\r\nRange: %s\r\n\r\n'%(self.method, path, self.protocol, host, self.range1)+ self.client_buffer)
        self.target2.send('%s %s %s\r\nHost:%s\r\nRange: %s\r\n\r\n'%(self.method, path, self.protocol, host, self.range2)+ self.client_buffer)
        print "Requets sent"

    #given a key it'll find a value in the header
    def findHeaderInfo(self, header, key):
        value = ""
        index = header.find(key, 0)
        if(index == -1):
            print "cannot find " + key
            return value
        else:
            index = index + len(key) + 2    # add to index 2 because of ": " i.g. "Connection: "
        newData = header[index:]
        index2 = newData.find('\r')
        value = newData[:index2]
        print "value: " + value
        return value

    #split the CONTENT_LENGTH into two ranges
    def splitRange(self, CONTENT_LENGTH):
        splitPoint = CONTENT_LENGTH / 3
        self.range1 = "bytes=0-" + str(splitPoint - 1)
        self.range2 = "bytes=" + str(splitPoint) + "-" + str(CONTENT_LENGTH - 1)

    #"revolving door" to re-direct the packets in the right direction
    def _read_write(self):
        time_out_max = self.timeout/3
        socs = [self.client, self.target, self.target2]
        count = 0
        SEND_DATA_1 = ""                    #container for data from request 1
        SEND_DATA_2 = ""                    #container for data from request 2
        RANGE_1_DONE = False                #checks for correct sizes
        RANGE_2_DONE = False
        SEND_FLAG = False                   #tells function to send to client
        remove_header_1 = False             #removes headers
        remove_header_2 = False
        header_info = "HTTP/1.1 200 OK\r\n\r\n" #custom header bc we trimmed them off
        CONTENT_LENGTH = 0                  #length of file we're downloding

        while 1:
            count += 1
            (recv, _, error) = select.select(socs, [], socs, 3)
            if error:
                break
            if recv:
                for in_ in recv:
                    data = in_.recv(BUFLEN)
                    if in_ is self.client:
                        out = self.target
                    else:
                        out = self.client
                    if data:
                        #handle GET requests
                        if self.method == "HEAD":
                            print data
                            CONTENT_LENGTH = int(self.findHeaderInfo(data, "Content-Length"))
                            self.splitRange(CONTENT_LENGTH)
                            self.sendRangeRequests()
                        elif(not SEND_FLAG):
                            #determine which interface sent/receive to
                            if(in_ == self.target and not RANGE_1_DONE):
                                #trim headers when ended (only beginning)
                                if(not remove_header_1):
                                    data = self.remove_header(data)
                                    remove_header_1 = True
                                SEND_DATA_1 += data
                            if(in_ == self.target2 and not RANGE_2_DONE):
                                if(not remove_header_2):
                                    data = self.remove_header(data)
                                    remove_header_2 = True
                                SEND_DATA_2 += data

                            #checks if each request is correct size
                            #if so then start sending
                            if(len(SEND_DATA_1) == (CONTENT_LENGTH / 3)):
                                print "Range 1 Done. Size of SEND_DATA_1: " + str(len(SEND_DATA_1))
                                RANGE_1_DONE = True
                            if(len(SEND_DATA_2) == (CONTENT_LENGTH - (CONTENT_LENGTH / 3))):
                                print "Range 2 Done. Size of SEND_DATA_2: " + str(len(SEND_DATA_2))
                                RANGE_2_DONE = True
                            if(RANGE_1_DONE and RANGE_2_DONE):
                                print "Got both ranges"
                                SEND_FLAG = True
                                print "SENDING DATA..."
                                out.send(header_info + SEND_DATA_1 + SEND_DATA_2)
                                print "SENT."
                                return
                        count = 0
            if (SEND_FLAG):
                break
            if count == time_out_max:
                break

#start the proxy server and listen for connections on port 8080
def start_server(host='localhost', port=8080, IPv6=False, timeout=60,
                  handler=ConnectionHandler):
    if IPv6==True:
        soc_type=socket.AF_INET6
    else:
        soc_type=socket.AF_INET
    soc = socket.socket(soc_type)
    soc.bind((host, port))
    print "Serving on %s:%d."%(host, port)
    soc.listen(0)
    while 1:
        thread.start_new_thread(handler, soc.accept()+(timeout,))

if __name__ == '__main__':
    start_server()
