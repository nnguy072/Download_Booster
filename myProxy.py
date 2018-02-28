#-*- coding: cp1252 -*-
# <PythonProxy.py>
#
#Copyright (c) <2009> <F�bio Domingues - fnds3000 in gmail.com>
#
#Permission is hereby granted, free of charge, to any person
#obtaining a copy of this software and associated documentation
#files (the "Software"), to deal in the Software without
#restriction, including without limitation the rights to use,
#copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the
#Software is furnished to do so, subject to the following
#conditions:
#
#The above copyright notice and this permission notice shall be
#included in all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#OTHER DEALINGS IN THE SOFTWARE.

"""
Copyright (c) <2009> <F�bio Domingues - fnds3000 in gmail.com> <MIT Licence>

                  **************************************
                 *** Python Proxy - A Fast HTTP proxy ***
                  **************************************

Neste momento este proxy � um Elie Proxy.

Suporta os m�todos HTTP:
 - OPTIONS;
 - GET;
 - HEAD;
 - POST;
 - PUT;
 - DELETE;
 - TRACE;
 - CONENCT.

Suporta:
 - Conex�es dos cliente em IPv4 ou IPv6;
 - Conex�es ao alvo em IPv4 e IPv6;
 - Conex�es todo o tipo de transmiss�o de dados TCP (CONNECT tunneling),
     p.e. liga��es SSL, como � o caso do HTTPS.

A fazer:
 - Verificar se o input vindo do cliente est� correcto;
   - Enviar os devidos HTTP erros se n�o, ou simplesmente quebrar a liga��o;
 - Criar um gestor de erros;
 - Criar ficheiro log de erros;
 - Colocar excep��es nos s�tios onde � previs�vel a ocorr�ncia de erros,
     p.e.sockets e ficheiros;
 - Rever tudo e melhorar a estrutura do programar e colocar nomes adequados nas
     vari�veis e m�todos;
 - Comentar o programa decentemente;
 - Doc Strings.

Funcionalidades futuras:
 - Adiconar a funcionalidade de proxy an�nimo e transparente;
 - Suportar FTP?.


(!) Aten��o o que se segue s� tem efeito em conex�es n�o CONNECT, para estas o
 proxy � sempre Elite.

Qual a diferen�a entre um proxy Elite, An�nimo e Transparente?
 - Um proxy elite � totalmente an�nimo, o servidor que o recebe n�o consegue ter
     conhecimento da exist�ncia do proxy e n�o recebe o endere�o IP do cliente;
 - Quando � usado um proxy an�nimo o servidor sabe que o cliente est� a usar um
     proxy mas n�o sabe o endere�o IP do cliente;
     � enviado o cabe�alho HTTP "Proxy-agent".
 - Um proxy transparente fornece ao servidor o IP do cliente e um informa��o que
     se est� a usar um proxy.
     S�o enviados os cabe�alhos HTTP "Proxy-agent" e "HTTP_X_FORWARDED_FOR".

"""
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
        range1point5 = CONTENT_LENGTH / 2
        self.range1 = "bytes=0-" + str(range1point5)
        self.range2 = "bytes=" + str(range1point5+1) + "-" + str(CONTENT_LENGTH - 1)
        print "Range stuff"
        print self.range1
        print self.range2
        print CONTENT_LENGTH
        print range1point5 + 1
        print CONTENT_LENGTH - range1point5 - 1
        print "End of Range stuff"

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
        temp = self.method  #holds the original method
        self.method = "HEAD"

        # print self.client_buffer
        self.target.send('%s %s %s\n'%(self.method, path, self.protocol) + self.client_buffer)
        self.client_buffer = ''         #1
        self._read_write()

        self.method = temp
        self.splitRange()

        #TO DO: need to send another request to "target2" that GETs a different range of bytes
        # self.target.send('%s %s %s\r\nHost:%s\r\n\r\n'%(self.method, path, self.protocol, host)+ self.client_buffer)
        self.target.send('%s %s %s\r\nHost:%s\r\nRange: %s\r\n\r\n'%(self.method, path, self.protocol, host, self.range1)+ self.client_buffer)
        self.target2.send('%s %s %s\r\nHost:%s\r\nRange: %s\r\n\r\n'%(self.method, path, self.protocol, host, self.range2)+ self.client_buffer)

        self.client_buffer = '' #3
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

    #"revolving door" to re-direct the packets in the right direction
    def _read_write(self):
        time_out_max = self.timeout/3
        time_out_max = self.timeout
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
                    newData = data[index:]
                    index2 = newData.find('\r')
                    global CONTENT_LENGTH
                    CONTENT_LENGTH = int(newData[:index2])
                    break
                elif(not SEND_FLAG):
                    # I think this is how you distinguish between 1 and 2
                    # SEND_DATA_1 and 2 both have headers in the beginning [confirmed]
                    # kind of a hack using fileno, better to use header info: ip addr + port
                    if((in_.fileno() == self.target.fileno()) and not RANGE_1_DONE):
                        if(not remove_header_1):
                            data = self.remove_header(data)
                            remove_header_1 = True
                        SEND_DATA_1 += data
                        print "Size of SEND_DATA_1: " + str(len(SEND_DATA_1))
                    if((in_.fileno() == self.target2.fileno()) and not RANGE_2_DONE):
                        if(not remove_header_2):
                            data = self.remove_header(data)
                            remove_header_2 = True
                        SEND_DATA_2 += data
                        print "Size of SEND_DATA_2: " + str(len(SEND_DATA_2))

                    #checks if each request is correct size
                    #if so then start sending
                    #Problem: A lot of the time RANGE_2 finishes
                    #         sometimes both of them finish. Why??
                    if(len(SEND_DATA_1) == ((CONTENT_LENGTH / 2) + 1)):
                        print "Range 1 Done. Size of SEND_DATA_1: " + str(len(SEND_DATA_1))
                        RANGE_1_DONE = True
                    if(len(SEND_DATA_2) == (CONTENT_LENGTH - (CONTENT_LENGTH / 2) - 1)):
                        print "Range 2 Done. Size of SEND_DATA_2: " + str(len(SEND_DATA_2))
                        RANGE_2_DONE = True
                    if(RANGE_1_DONE and RANGE_2_DONE):
                        print "got both ranges"
                        SEND_FLAG = True
                        ## ------------------
                        #testing this
                        self.send_to_client(out, header_info, SEND_DATA_1, SEND_DATA_2)
                        break
                        ## -------------------
                    count = 0
                elif(SEND_FLAG):
                    #merge header + both request and send
                    print "Sending to Client"
                    out.send(header_info + SEND_DATA_1 + SEND_DATA_2)
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
