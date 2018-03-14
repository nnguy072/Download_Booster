import socket, thread, select, os, sys

__version__ = '0.1.0 Draft 1'
BUFLEN = 8192
VERSION = 'Python Proxy/'+__version__
HTTPVER = 'HTTP/1.1'
CONTENT_LENGTH = 0

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

        CONTENT_LENGTH = 0
        self.client.close()
        self.target.close()

    def get_base_header(self):
        while 1:
            self.client_buffer += self.client.recv(BUFLEN)
            end = self.client_buffer.find('\n')
            if end!=-1:
                break

        #print the request
        print '%s'%self.client_buffer[:end]#debug

        data = (self.client_buffer[:end+1]).split()
        self.client_buffer = self.client_buffer[end+1:]
        return data

    def method_CONNECT(self):
        self._connect_target(self.path)
        self.client.send(HTTPVER+' 200 Connection established\n'+
                         'Proxy-agent: %s\n\n'%VERSION)
        self.client_buffer = ''
        self._read_write()

    def splitRange(self):
        splitPoint = CONTENT_LENGTH / 3
        self.range1 = "bytes=0-" + str(splitPoint - 1)
        self.range2 = "bytes=" + str(splitPoint) + "-" + str(CONTENT_LENGTH - 1)
        # print "Range stuff"
        # print "Range1: " + str(self.range1)
        # print "Range1 done at: " + str(splitPoint)
        # print "Range2: " + str(self.range2)
        # print "Range2 done at: " + str(CONTENT_LENGTH - splitPoint)
        # print "Content Length: " + str(CONTENT_LENGTH)
        # print "End of Range stuff"

    #forward the packet to its final destination
    def method_others(self):
        self.path = self.path[7:]
        i = self.path.find('/')
        host = self.path[:i]
        path = self.path[i:]
        self._connect_target(host)
        global SEND_FLAG
        global SEND_DATA

        #TO DO: first find out the Content-Length by sending a RANGE request
        #send head request to get header (has content-length)
        self.method = "HEAD"

        # print self.client_buffer
        self.target.send('%s %s %s\n'%(self.method, path, self.protocol) + self.client_buffer)
        self.client_buffer = ''         #1
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
        self.target.connect(address)

        self.target2 = socket.socket(soc_family)    #don't think i did this right
        self.target2.connect(address)

    def remove_header(self, data):
        index = data.find("\r\n\r\n", 0) + 4
        return data[index:]

    def send_to_client(self, out, header, data_1, data_2):
        out.send(header + data_1 + data_2)

    def sendRangeRequests(self):
        i = self.path.find('/')
        host = self.path[:i]
        path = self.path[i:]
        self.method = "GET"
        self.target.send('%s %s %s\r\nHost:%s\r\nRange: %s\r\n\r\n'%(self.method, path, self.protocol, host, self.range1)+ self.client_buffer)
        self.target2.send('%s %s %s\r\nHost:%s\r\nRange: %s\r\n\r\n'%(self.method, path, self.protocol, host, self.range2)+ self.client_buffer)
        print "SENT REQUESTS"

    #"revolving door" to re-direct the packets in the right direction
    def _read_write(self):
        time_out_max = self.timeout/3
        socs = [self.client, self.target, self.target2]
        count = 0
        SEND_DATA_1 = ""
        SEND_DATA_2 = ""
        RANGE_1_DONE = False
        RANGE_2_DONE = False
        SEND_FLAG = False
        remove_header_1 = False
        remove_header_2 = False
        header_info = "HTTP/1.1 200 OK\r\n\r\n"
        counter1 = 0
        counter2 = 0

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
                        #TO DO: Check if it's response to the RANGE request and extract the Content-Length
                        if self.method == "HEAD":
                            #finds where "Content-Length" is in header then parses the actual length
                            index = data.find("Content-Length", 0) + 16
                            newData2 = data[index:]
                            index2 = newData2.find('\r')
                            global CONTENT_LENGTH
                            CONTENT_LENGTH = int(newData2[:index2])
                            self.splitRange()
                            self.sendRangeRequests()
                        elif(not SEND_FLAG):
                            # I think this is how you distinguish between 1 and 2
                            # SEND_DATA_1 and 2 both have headers in the beginning [confirmed]
                            # kind of a hack using fileno, better to use header info: ip addr + port
                            if((in_.fileno() == self.target.fileno()) and not RANGE_1_DONE):
                                counter1 = counter1 + 1
                                if(not remove_header_1):
                                    newdata = self.remove_header(data)
                                    remove_header_1 = True
                                    SEND_DATA_1 += newdata
                                else:
                                    SEND_DATA_1 += data
                                print "Size of SEND_DATA_1: " + str(len(SEND_DATA_1))
                            if((in_.fileno() == self.target2.fileno()) and not RANGE_2_DONE):
                                counter2 = counter2 + 1
                                if(not remove_header_2):
                                    newdata = self.remove_header(data)
                                    remove_header_2 = True
                                    SEND_DATA_2 += newdata
                                else:
                                    SEND_DATA_2 += data
                                print "Size of SEND_DATA_2: " + str(len(SEND_DATA_2))

                            #checks if each request is correct size
                            #if so then start sending
                            if(len(SEND_DATA_1) == (CONTENT_LENGTH / 3)):
                                print "Range 1 Done. Size of SEND_DATA_1: " + str(len(SEND_DATA_1))
                                RANGE_1_DONE = True
                            if(len(SEND_DATA_2) == (CONTENT_LENGTH - (CONTENT_LENGTH / 3))):
                                print "Range 2 Done. Size of SEND_DATA_2: " + str(len(SEND_DATA_2))
                                RANGE_2_DONE = True
                            if(RANGE_1_DONE and RANGE_2_DONE):
                                print "got both ranges"
                                SEND_FLAG = True
                                self.send_to_client(out, header_info, SEND_DATA_1, SEND_DATA_2)
                                break
                            count = 0
            if count == time_out_max:
                break

#start the proxy server and listen for connections on port 8080
def start_server(host='localhost', port=8081, IPv6=False, timeout=60,
                  handler=ConnectionHandler):
    if IPv6==True:
        soc_type=socket.AF_INET6
    else:
        soc_type=socket.AF_INET
    soc = socket.socket(soc_type)
    soc.bind((host, port))
    print "Serving on %s:%d."%(host, port)#debug
    soc.listen(0)
    while 1:
        thread.start_new_thread(handler, soc.accept()+(timeout,))

if __name__ == '__main__':
    start_server()
