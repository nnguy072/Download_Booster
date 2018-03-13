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
    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')
    #s3 = net.addSwitch('s3')
    info( '*** Add hosts\n')
    client1 = net.addHost('client1', dpid="0000000000000002")
    router = net.addHost('router', dpid="0000000000000500")
    server = net.addHost('server', dpid="00000000000001000")
    #h3 = net.addHost('h3')
	
    info( '*** Add links\n')
    """net.addLink(h1, h2)
    net.addLink(h2, s1)
    net.addLink(h2, s2)
    net.addLink(s2, h3)
    net.addLink(h3, s1)"""
    Link(client1, s1, intfName1='c1-eth1', intfName2='s1-eth1')
    Link(client1, s2, intfName1='c1-eth2', intfName2='s2-eth1')
    Link(s1, router, intfName1='s1-eth0', intfName2='r-eth1')
    Link(s2, router, intfName1='s2-eth0', intfName2='r-eth2')
    Link(router, server, intfName1='r-eth0', intfName2='server-eth0')
    Link(router, server, intfName1='r-eth10', intfName2='server-eth1')
    #h1.cmd('ifconfig h1-eth1 10.0.1.1 netmask 255.255.255.0')
    #h1.cmd('ifconfig h1-eth2 10.0.2.1 netmask 255.255.255.0')
    #h2.cmd('ifconfig h2-eth0 10.0.100.1 netmask 255.255.255.0')
    #s1.cmd('ifconfig s1-eth0 10.0.1.2 netmask 255.255.255.0')
    #s1.cmd('ifconfig s1-eth1 10.0.1.3 netmask 255.255.255.0')
    #s2.cmd('ifconfig s2-eth0 10.0.2.2 netmask 255.255.255.0')
    #s2.cmd('ifconfig s2-eth1 10.0.2.3 netmask 255.255.255.0')


    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    #info( '*** Starting switches\n')
    net.get('s1').start([c0])
    net.get('s2').start([c0])
    #net.get('s3').start([c0])
    

    #info( '*** Post configure switches and hosts\n')
    client1.cmd('ifconfig c1-eth1 10.0.1.1 netmask 255.255.255.0')
    client1.cmd('ifconfig c1-eth2 10.0.2.1 netmask 255.255.255.0')
    client1.cmd('ip route add 100.100.1.0/24 via 10.0.1.200 dev c1-eth1')
    client1.cmd('ip route add 100.100.2.0/24 via 10.0.2.200 dev c1-eth2')
    router.cmd('sysctl net.ipv4.ip_forward=1')
    router.cmd('ifconfig r-eth1 10.0.1.200 netmask 255.255.255.0')
    router.cmd('ifconfig r-eth2 10.0.2.200 netmask 255.255.255.0')
    router.cmd('ifconfig r-eth0 100.100.1.10 netmask 255.255.255.0')
    router.cmd('ifconfig r-eth10 100.100.2.10 netmask 255.255.255.0')
    router.cmd('ip route add 10.0.1.0/24 dev r-eth1')
    router.cmd('ip route add 10.0.2.0/24 dev r-eth2')
    router.cmd('ip route add 100.100.1.0/24 dev r-eth0')
    router.cmd('ip route add 100.100.2.0/24 dev r-eth10')
    server.cmd('ifconfig server-eth0 100.100.1.1 netmask 255.255.255.0')
    server.cmd('ifconfig server-eth1 100.100.2.1 netmask 255.255.255.0')
    server.cmd('ip route add 10.0.1.0/24 via 100.100.1.10 dev server-eth0')
    server.cmd('ip route add 10.0.2.0/24 via 100.100.2.10 dev server-eth1')
    #h1.cmd('ifconfig h1-eth2 10.0.2.1 netmask 255.255.255.0')
    #h2.cmd('ifconfig h2-eth0 10.0.100.1 netmask 255.255.255.0')
    #h1.cmd('ifconfig h1-eth1 10.0.1.1 netmask 255.255.255.0')
    #h1.cmd('ifconfig h1-eth2 10.0.2.1 netmask 255.255.255.0')
    #h2.cmd('ifconfig h2-eth0 10.0.100.1 netmask 255.255.255.0')
    #net.startTerms()
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()

