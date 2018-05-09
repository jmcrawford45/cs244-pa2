import os
import sys
import math
import random
import re
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
from mininet.log import setLogLevel, info, warn, output
from tqdm import tqdm
from mininet.util import quietRun, natural, custom



class Switch(object):

    def __init__(self, switch):
        self.switch = switch
        self.ports_in_use = 0


class JellyFishTop(Topo):

    def __init__(self, num_servers=686,
                rack_height=4, ports_per_switch=36):
        self.num_servers = num_servers
        self.rack_height = rack_height
        self.ports_per_switch = ports_per_switch
        self.num_switches = int(math.ceil(float(num_servers)/rack_height))
        self.graph = networkx.Graph()
        self.switch_links = 0
        Topo.__init__(self)

    def build(self):
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
            #1 Gbps links
            self.addLink(s1.switch, s2.switch, bw=0.1)
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




def experiment(net, switches):
    print 'start experiment'
    for r in range(5):
        net.start()
        intervals, cpuEntries = iperfPairs([h for h in net.hosts if h.name.startswith('s')])
        print intervals
        print cpuEntries
        net.stop()

# Next 5 methods taken from github.com/mininet/mininet-tests/blob/master/pairs/
# Parse output from packetcount.c (github.com/mininet/mininet-tests/blob/master/pairs/)

def pct( x ):
    "pretty percent"
    return round(  x * 100.0, 2 )

def parseIntfStats( startTime, stats ):
    """Parse stats; return dict[intf] of (s, rxbytes, txbytes)
       and list of ( start, stop, user%... )"""
    spaces = re.compile('\s+')
    colons = re.compile( r'\:' )
    seconds = re.compile( r'(\d+\.\d+) seconds')
    intfEntries, cpuEntries, lastEntries = {}, [], []
    for line in stats.split( '\n' ):
        m = seconds.search(line)
        if m:
            s = round( float( m.group( 1 ) ) - startTime, 3 )
        elif '-eth' in line:
            line = spaces.sub( ' ', line ).split()
            intf = colons.sub( '', line[ 0 ] )
            rxbytes, txbytes = int( line[ 1 ] ), int( line[ 9 ] )
            intfEntries[ intf ] = intfEntries.get( intf, [] ) +  [
                    (s, rxbytes, txbytes ) ]
        elif 'cpu ' in line:
            line = spaces.sub( ' ', line ).split()
            entries = map( float, line[ 1 : ] )
            if lastEntries:
                dtotal = sum( entries ) - sum( lastEntries )
                if dtotal == 0:
                    raise Exception( "CPU was stalled from %s to %s - giving up" %
                                     ( lastTime, s ) )
                deltaPct = [ pct( ( x1 - x0 ) / dtotal ) 
                             for x1, x0 in zip( entries, lastEntries) ]
                interval = s - lastTime
                cpuEntries += [ [ lastTime, s ] + deltaPct ]
            lastTime = s
            lastEntries = entries

    return intfEntries, cpuEntries

def remoteIntf( intf ):
    "Return other side of link that intf is connected to"
    link = intf.link
    return link.intf1 if intf == link.intf2 else link.intf2

def listening( src, dest, port=5001 ):
    "Return True if we can connect from src to dest on port"
    cmd = 'echo A | telnet -e A %s %s' % (dest.IP(), port)
    result = src.cmd( cmd )
    return 'Connected' in result

def iperfPairs(switches):
    "Run iperf semi-simultaneously one way for all pairs"
    quietRun( "pkill -9 iperf" )
    info( "*** Starting iperf servers\n" )
    for dest in switches:
        dest.cmd( "iperf -s &" )
    info( "*** Waiting for servers to start listening\n" )
    for i in range(len(switches)):
        src, dest = switches[i], switches[(switch_num+i+1)%len(switches)]
        info( dest.name, '' )
        while not listening( src, dest ):
            info( '.' )
            sleep( .5 )
    info( '\n' )
    info( "*** Starting iperf clients\n" )
    for i in range(len(switches)):
        src, dest = switches[i], switches[(switch_num+i+1)%len(switches)]
        src.sendCmd( "sleep 1; iperf -t %s -i .5 -c %s" % (
            1, dest.IP() ) )
    info( '*** Running cpu and packet count monitor\n' )
    startTime = int( time() )
    cmd = "./packetcount %s .5" % ( 3 )
    stats = quietRun( cmd  )
    intfEntries, cpuEntries = parseIntfStats( startTime, stats )
    info( "*** Waiting for clients to complete\n" )
    results = []
    for i in range(len(switches)):
        src, dest = switches[i], switches[(switch_num+i+1)%len(switches)]
        result = src.waitOutput()
        dest.cmd( "kill -9 %iperf" )
        # Wait for iperf server to terminate
        dest.cmd( "wait" )
        # We look at the stats for the remote side of the destination's
        # default intf, as it is 1) now in the root namespace and easy to
        # read and 2) guaranteed by the veth implementation to have
        # the same byte stats as the local side (with rx and tx reversed,
        # naturally.)  Otherwise
        # we would have to spawn a packetcount process on each server
        intfName = remoteIntf( dest.defaultIntf() ).name
        intervals = intfEntries[ intfName ]
        # Note: we are reversing txbytes and rxbytes to reflect
        # the statistics *at the destination*
        results += [ { 'src': src.name, 'dest': dest.name,
                    'destStats(s,txbytes,rxbytes)': intervals } ]
    return results, cpuEntries

def main():
    topo = JellyFishTop()
    print 'Generate table 9 data'
    g = topo.graph
    shortest8 = dict()
    ecmp8 = dict()
    ecmp64 = dict()
    switches = [s for s in topo.switches()]
    for e in topo.links():
        shortest8[e] = ecmp8[e] = ecmp64[e] = 0
    # I've surmised that server-TOR connections don't count as links
    for switch_num in tqdm(range(len(switches))):
        for r in range(topo.rack_height):
            paths = ksp(copy.deepcopy(topo.graph), 
                switches[switch_num],
                switches[(switch_num+r+1)%len(switches)], 
                64, 'weight')
            lengths = [len(p) for p in paths]
            shortest = len([l for l in lengths if l == lengths[0]])
            ecmp8_count, ecmp64_count = min(shortest, 8), min(shortest, 64)
            for path in paths[:8]:
                for i in range(0, len(path)-1):
                    if (path[i], path[i+1]) in shortest8:
                        shortest8[(path[i], path[i+1])] += 1
                    else:
                        shortest8[(path[i+1], path[i])] += 1
            for path in paths[:ecmp8_count]:
                for i in range(0, len(path)-1):
                    if (path[i], path[i+1]) in ecmp8:
                        ecmp8[(path[i], path[i+1])] += 1
                    else:
                        ecmp8[(path[i+1], path[i])] += 1
            for path in paths[:ecmp64_count]:
                for i in range(0, len(path)-1):
                    if (path[i], path[i+1]) in ecmp64:
                        ecmp64[(path[i], path[i+1])] += 1
                    else:
                        ecmp64[(path[i+1], path[i])] += 1
    table_9(shortest8, ecmp8, ecmp64)
    net = Mininet(
    topo=topo, host=CPULimitedHost, link = TCLink, controller=JELLYPOX)
    # experiment(net, switches)

def sanityCheck():
    "Make sure we have stuff we need"
    reqs = [ 'iperf', 'telnet', './packetcount' ]
    for req in reqs:
        if quietRun( 'which ' + req ) == '':
            print ( "Error: cannot find", req,
               " - make sure it is built and/or installed." )
            exit( 1 )

if __name__ == "__main__":
    sanityCheck()
    setLogLevel( 'info' )
    main()