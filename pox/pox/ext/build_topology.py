import os
import sys
import math
import random
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.node import OVSController
from mininet.node import Controller
from mininet.node import RemoteController
from mininet.cli import CLI
sys.path.append("../../")
from pox.ext.jelly_pox import JELLYPOX
from subprocess import Popen
from time import sleep, time
from collections import defaultdict


class Switch(object):

    def __init__(self, switch):
        self.switch = switch
        self.ports_in_use = 0


class JellyFishTop(Topo):

    def __init__(self, num_servers=686,
                rack_height=5, ports_per_switch=32):
        self.num_servers = num_servers
        self.rack_height = rack_height
        self.ports_per_switch = ports_per_switch
        self.num_switches = int(math.ceil(float(num_servers)/rack_height))
        Topo.__init__(self)



    def build(self):
        switches, servers = list(), list()
        self.switch_map = defaultdict(list)
        for i in range(0, self.num_switches):
            switches.append(Switch(self.addSwitch('s%s' % i)))
        for i in range(0, self.num_servers):
            servers.append(self.addHost('h%s' % i))
        random.shuffle(servers)
        self.add_links(switches, servers)

    def get_random_edge(self, switches):
        available = [s for s in switches if s.ports_in_use < self.ports_per_switch]
        if len(available) < 2:
            return None
        # Check for case when network cannot be completely saturated
        for i in range(0,100):
            sample = random.sample(available, 2)
            s1,s2 = sample[0], sample[1]
            if s2 not in self.switch_map[s1]:
                return s1, s2
        return None

    def add_links(self, switches, servers):
        # Add servers
        switch_num = 0
        s = switches[switch_num]
        for server in servers:
            while s.ports_in_use >= self.rack_height:
                switch_num += 1
                s = switches[switch_num]
            self.addLink(server, s.switch)
            s.ports_in_use += 1
        while True:
            e = self.get_random_edge(switches)
            if e == None:
                break
            s1,s2 = e
            self.addLink(s1.switch, s2.switch)
            self.switch_map[s1].append(s2)
            self.switch_map[s2].append(s1)
            s1.ports_in_use += 1
            s2.ports_in_use += 1
        print 'Topology: {} hosts, {} switches, {} links'.format(
            len(self.hosts()), len(self.switches()), len(self.links()))


def experiment(net):
        print 'start experiment'
        net.start()
        # sleep(3)
        # net.pingAll()
        net.stop()

def main():
	topo = JellyFishTop()
	net = Mininet(topo=topo, host=CPULimitedHost, link = TCLink, controller=JELLYPOX)
	experiment(net)

if __name__ == "__main__":
	main()

