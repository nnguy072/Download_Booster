import socket, thread, select, os, sys

__version__ = '0.1.0 Draft 1'
BUFLEN = 8192
VERSION = 'Python Proxy/'+__version__
HTTPVER = 'HTTP/1.1'
CONTENT_LENGTH = 0
RANGE_1_DONE = False
RANGE_2_DONE = False
SEND_DATA_1 = ""
SEND_DATA_2 = ""
ACCEPT_FLAG = True #check if it accepts byte ranges

class ConnectionHandler:
    def __init__(self, connection, address, timeout):
        self.client = connection
        self.client_buffer = ''
        self.timeout = timeout
        self.range1 = "0"
        self.range2 = "0"
        #print the request and it extracts the protocol and path
        self.method, self.path, self.protocol = self.get_base_header()

        if self.method=='CONNECT':
            self.method_CONNECT()

        #handle the GET request
        elif self.method in ('OPTIONS', 'GET', 'HEAD', 'POST', 'PUT',
                             'DELETE', 'TRACE'):
            self.method_others()

        #reset globals
        global SEND_DATA_1, SEND_DATA_2, RANGE_1_DONE, RANGE_2_DONE, CONTENT_LENGTH, ACCEPT_FLAG
        SEND_DATA_1 = ""
        SEND_DATA_2 = ""
        RANGE_1_DONE = False
        RANGE_2_DONE = False
        CONTENT_LENGTH = 0
        ACCEPT_FLAG = True

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

    # TODO: need to create sockets
    def thread_helper(self, path, host, content_range):
        # i tried
        c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try
            s.connect((host, 80))
        except:
            print 'Unable to connect'
            sys.exit()
        if(content_range == self.range1):
            self.target.send('%s %s %s\r\nHost:%s\r\nRange: %s\r\n\r\n'%(self.method, path, self.protocol, host, self.range1)+ self.client_buffer)
            self.client_buffer = '' #3
            self._read_write()
        elif(content_range == self.range2):
            self.target2.send('%s %s %s\r\nHost:%s\r\nRange: %s\r\nConnection: close\r\n\r\n'%(self.method, path, self.protocol, host, self.range2)+ self.client_buffer)
            self.client_buffer = '' #3
            self._read_write()


    #forward the packet to its final destination
    def method_others(self):
        self.path = self.path[7:]
        i = self.path.find('/')
        host = self.path[:i]
        path = self.path[i:]
        self._connect_target(host)
        global SEND_FLAG
        global SEND_DATA

        #TODO: first find out the Content-Length by sending a RANGE request
        #send head request to get header (has content-length)
        temp = self.method  #holds the original method
        self.method = "HEAD"

        # print self.client_buffer
        self.target.send('%s %s %s\n'%(self.method, path, self.protocol) + self.client_buffer)
        self.client_buffer = ''         #1
        self._read_write()

        #if it doesn't just exit
        #could probably change to just do a single request
        if(not ACCEPT_FLAG):
            return

        self.method = temp
        self.splitRange()

        #two threads to handle both range requests
        thread.start_new_thread(self.thread_helper, (path, host, self.range1))
        thread.start_new_thread(self.thread_helper, (path, host, self.range2))


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
        print "Sending..."
        out.send(header + data_1 + data_2)
        print "Sent."

    def findHeaderInfo(self, header, key):
        value = ""
        index = header.find(key, 0)  # +2 bc ": "
        if(index == -1):
            print "cannot find " + key
            return value
        else:
            index = index + len(key) + 2
        newData = header[index:]
        index2 = newData.find('\r')
        value = newData[:index2]
        return value

    #"revolving door" to re-direct the packets in the right direction
    def _read_write(self):
        time_out_max = self.timeout/3
        time_out_max = self.timeout
        socs = [self.client, self.target, self.target2]
        count = 0
        global SEND_DATA_1    #stores data from first range
        global SEND_DATA_2    #stores data from second rang
        global RANGE_1_DONE
        global RANGE_2_DONE
        SEND_FLAG = False       #true when have correct amount of data
        remove_header_1 = False
        remove_header_2 = False
        header_info = "HTTP/1.1 200 OK\r\n\r\n"

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
                #TODO: Check if it's response to the RANGE request and extract the Content-Length
                if self.method == "HEAD":
                    #check if it accepts range requests
                    rangeCheck = self.findHeaderInfo(data, "Accept-Ranges")
                    if(rangeCheck != "bytes"):
                        print "Target does not accept range requests."
                        global ACCEPT_FLAG
                        ACCEPT_FLAG = False
                        break
                    global CONTENT_LENGTH
                    CONTENT_LENGTH = int(self.findHeaderInfo(data, "Content-Length"))
                    break
                elif(not RANGE_1_DONE):
                    #remove header from first recv data | do only once
                    if(not remove_header_1):
                        data = self.remove_header(data)
                        remove_header_1 = True
                    SEND_DATA_1 += data
                    print "Size of SEND_DATA_1: " + str(len(SEND_DATA_1))
                    if(len(SEND_DATA_1) == (CONTENT_LENGTH / 3)):
                        # print "Range 1 Done. Size of SEND_DATA_1: " + str(len(SEND_DATA_1))
                        RANGE_1_DONE = True
                        break
                    count = 0
                elif(not RANGE_2_DONE):
                    if(not remove_header_2):
                        data = self.remove_header(data)
                        remove_header_2 = True
                    SEND_DATA_2 += data
                    print "Size of SEND_DATA_2: " + str(len(SEND_DATA_2))
                    if(len(SEND_DATA_2) == (CONTENT_LENGTH - (CONTENT_LENGTH / 3))):
                        # print "Range 2 Done. Size of SEND_DATA_2: " + str(len(SEND_DATA_2))
                        RANGE_2_DONE = True
                        self.send_to_client(out, header_info, SEND_DATA_1, SEND_DATA_2)
                        break
                    count = 0
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
    print "Serving on %s:%d."%(host, port)#debug
    soc.listen(0)
    while 1:
        thread.start_new_thread(handler, soc.accept()+(timeout,))

if __name__ == '__main__':
    start_server()
