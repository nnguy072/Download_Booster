#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf, Link
from subprocess import call

def myNetwork():

    net = Mininet(controller=RemoteController, link=TCLink, switch=OVSKernelSwitch)

    info( '*** Adding controller\n' )
    c0=net.addController(name='c0',
                      controller=RemoteController,
                      ip='127.0.0.1',
                      protocol='tcp',
                      port=6633)

    info( '*** Add switches\n')
    s1 = net.addHost('s1')
    s2 = net.addHost('s2')
    s3 = net.addHost('s3')
    info( '*** Add hosts\n')
    client1 = net.addHost('client1', dpid="0000000000000001")
    server = net.addHost('server', dpid="00000000000001000")
	
    info( '*** Add links\n')
    Link(client1, s1, intfName1='c1-eth1', intfName2='s1-eth1')
    Link(client1, s2, intfName1='c1-eth2', intfName2='s2-eth1')
    Link(s1, s3, intfName1='s1-eth0', intfName2='s3-eth1')
    Link(s2, s3, intfName1='s2-eth0', intfName2='s3-eth2')
    Link(s3, server, intfName1='s3-eth0', intfName2='server-eth0')


    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    #info( '*** Starting switches\n')
    #net.get('s1').start([c0])
    #net.get('s2').start([c0])
    #net.get('s3').start([c0])
    

    #info( '*** Post configure switches and hosts\n')
    client1.cmd('ifconfig c1-eth1 10.0.1.1 netmask 255.255.255.0')
    client1.cmd('ifconfig c1-eth2 10.0.2.1 netmask 255.255.255.0')
    s1.cmd('ifconfig s1-eth1 10.0.1.100 netmask 255.255.255.0')
    s1.cmd('ifconfig s1-eth0 10.0.4.100 netmask 255.255.255.0')
    s2.cmd('ifconfig s2-eth1 10.0.2.100 netmask 255.255.255.0')
    s2.cmd('ifconfig s2-eth0 10.0.5.100 netmask 255.255.255.0')
    s3.cmd('ifconfig s3-eth1 10.0.4.101 netmask 255.255.255.0')
    s3.cmd('ifconfig s3-eth2 10.0.5.101 netmask 255.255.255.0')
    s3.cmd('ifconfig s3-eth0 10.0.3.100 netmask 255.255.255.0')
    server.cmd('ifconfig server-eth0 10.0.3.1 netmask 255.255.255.0')
    
    client1.cmd('ip rule add from 10.0.1.1 table 10')
    client1.cmd('ip route add 10.0.1.0/24 dev c1-eth1 scope link table 10')
    client1.cmd('ip route add default via 10.0.1.100 dev c1-eth1 table 10')

    client1.cmd('ip rule add from 10.0.2.1 table 20')
    client1.cmd('ip route add 10.0.2.0/24 dev c1-eth2 scope link table 20')
    client1.cmd('ip route add default via 10.0.2.100 dev c1-eth2 table 20')

    server.cmd('ip route add default via 10.0.3.100 dev server-eth0')
   
    s1.cmd('sysctl -w net.ipv4.ip_forward=1')
    s2.cmd('sysctl -w net.ipv4.ip_forward=1')
    s3.cmd('sysctl -w net.ipv4.ip_forward=1')

    s1.cmd ('ip route add 10.0.3.0/24 via 10.0.4.101 dev s1-eth0')
    s2.cmd ('ip route add 10.0.3.0/24 via 10.0.5.101 dev s2-eth0')
    s3.cmd ('ip route add 10.0.1.0/24 via 10.0.4.100 dev s3-eth1')
    s3.cmd ('ip route add 10.0.2.0/24 via 10.0.5.100 dev s3-eth2')

    #net.startTerms()
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()

