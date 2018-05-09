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
from pox.ext.ksp import ksp
from pox.ext.plot import table_9
from subprocess import Popen
from time import sleep, time
from collections import defaultdict
import networkx
import itertools
import copy
from tqdm import tqdm


class Switch(object):

    def __init__(self, switch):
        self.switch = switch
        self.ports_in_use = 0


class JellyFishTop(Topo):

    def __init__(self, num_servers=100,
                rack_height=5, ports_per_switch=6):
        self.num_servers = num_servers
        self.rack_height = rack_height
        self.ports_per_switch = ports_per_switch
        self.num_switches = int(math.ceil(float(num_servers)/rack_height))
        self.graph = networkx.Graph()
        self.switch_links = 0
        Topo.__init__(self)

    def build(self):
	leftHost = self.addHost( 'h1' )
 	rightHost = self.addHost( 'h2' )
	leftSwitch = self.addSwitch( 's3' )
	rightSwitch = self.addSwitch( 's4' )

            # Add links
	self.addLink(rightHost, rightSwitch)
        self.addLink( leftHost, leftSwitch )
        self.addLink( leftSwitch, rightSwitch )
        self.addLink( rightSwitch, rightHost )
        return
	switches, servers = list(), list()
        self.switch_map = defaultdict(list)
        for i in range(0, self.num_switches):
            switches.append(Switch(self.addSwitch('s%s' % i)))
            self.graph.add_node('s%s' % i)
        for i in range(0, self.num_servers):
            servers.append(self.addHost('h%s' % i))
            self.graph.add_node('h%s' % i)
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

    def connect_servers(self, switches, servers):
        # Add servers
        for server in servers:
            s = random.choice(switches)
            while s.ports_in_use >= self.rack_height:
                s = random.choice(switches)
            self.addLink(server, s.switch)
            self.graph.add_edge(s.switch, server, weight=1)
            s.ports_in_use += 1

    def connect_switches(self, switches):
        while True:
            e = self.get_random_edge(switches)
            if e == None:
                break
            s1,s2 = e
            self.addLink(s1.switch, s2.switch)
            self.graph.add_edge(s1.switch, s2.switch, weight=1)
            self.switch_links += 1
            self.switch_map[s1].append(s2)
            self.switch_map[s2].append(s1)
            s1.ports_in_use += 1
            s2.ports_in_use += 1

    def add_links(self, switches, servers):
        self.connect_servers(switches, servers)
        self.connect_switches(switches)
        print 'Topology: {} hosts, {} switches, {} links, {} switch links'.format(
            len(self.hosts()), len(self.switches()), len(self.links()),
            self.switch_links)
        print len(self.graph.edges())




def experiment(net):
        print 'start experiment'
        net.start()
        sleep(3)
        net.pingAll()
        net.stop()

def derangement(l, original):
    random.shuffle(l)
    for i in range(len(l)):
        if l[i] == original[i]:
            return derangement(l, original)
    return l

def main():
    topo = JellyFishTop()
    # print 'Generate table 9 data'
    # g = topo.graph
    # shortest8 = dict()
    # ecmp8 = dict()
    # ecmp64 = dict()
    # switches = [s for s in topo.switches()]
    # for e in topo.links():
    #     shortest8[e] = ecmp8[e] = ecmp64[e] = 0
    # # I've surmised that server-TOR connections don't count as links
    # for switch_num in tqdm(range(len(switches))):
    #     for r in range(topo.rack_height):
    #         paths = ksp(copy.deepcopy(topo.graph), 
    #             switches[switch_num],
    #             switches[(switch_num+r+1)%len(switches)], 
    #             64, 'weight')
    #         lengths = [len(p) for p in paths]
    #         shortest = len([l for l in lengths if l == lengths[0]])
    #         ecmp8_count, ecmp64_count = min(shortest, 8), min(shortest, 64)
    #         for path in paths[:8]:
    #             for i in range(0, len(path)-1):
    #                 if (path[i], path[i+1]) in shortest8:
    #                     shortest8[(path[i], path[i+1])] += 1
    #                 else:
    #                     shortest8[(path[i+1], path[i])] += 1
    #         for path in paths[:ecmp8_count]:
    #             for i in range(0, len(path)-1):
    #                 if (path[i], path[i+1]) in ecmp8:
    #                     ecmp8[(path[i], path[i+1])] += 1
    #                 else:
    #                     ecmp8[(path[i+1], path[i])] += 1
    #         for path in paths[:ecmp64_count]:
    #             for i in range(0, len(path)-1):
    #                 if (path[i], path[i+1]) in ecmp64:
    #                     ecmp64[(path[i], path[i+1])] += 1
    #                 else:
    #                     ecmp64[(path[i+1], path[i])] += 1
    # table_9(shortest8, ecmp8, ecmp64)
    net = Mininet(
    topo=topo, host=CPULimitedHost, link = TCLink, controller=JELLYPOX)
    experiment(net)

if __name__ == "__main__":
    main()
