from Queue import Queue as qQueue
from threading import Thread
from multiprocessing import Process, Manager, Lock
from multiprocessing.queues import Queue
from scapy.all import sniff as scapy_sniff
import nids, re, time, os, socket

UNWANTED_IP_PORTS = (
    4321,
    43
)

UNWANTED_TCP_PORTS = (
    4321,
    993,
    443,
    43,
    22
)

UNWANTED_DOMAINS = (
    'www.invisionpower.com',
    'in-addr.arpa',
    'WHOIS PRIVACY PROTECTION SERVICE, INC',
    'WHOISGUARD, INC',
    'localhost.localdomain',
    'localhost.local'
)

UNWANTED_HOSTS = (
    'RIPE Network Coordination Centre',
    'Internet Assigned Numbers Authority',
    ''
)

NONTRUNCATED_DOMAINS = (
    # Empty, for now.
)

_END_STATES = (
    nids.NIDS_CLOSE,
    nids.NIDS_TIMEOUT,
    nids.NIDS_RESET
)

# In case whois lookup hangs, don't execute _clean_timestamps by using a mutex.
_timestamp_cleanup_lock = Lock()
#_traf_dict_access_lock = Lock()
_ip_table = {}
_host_table = {}
_initialized = False
_traf_queue = Queue()
_dns_lookup_queue = Queue()

def init(rt_traf_dict, dns_dict, interval, tcp_queue,
        dns_queue, arp_queue, device):
    global _traf_dict, _dns, _interval, _dns_queue,\
            _tcp_parse_queue, _arp_queue, _device, _initialized
    _traf_dict = rt_traf_dict
    _dns = dns_dict
    _interval = interval + 0.015 # seconds
    _tcp_parse_queue = tcp_queue
    _dns_queue = dns_queue
    _arp_queue = arp_queue
    _device = device
    _initialized = True

def sniff():
    if not _initialized:
        raise NameError('Module vars were not initialized.')

    nids.param('device', _device)
    nids.param('multiproc', 1)
    nids.param('scan_num_hosts', 0)
    nids.chksum_ctl([('0.0.0.0/0', False)])

    nids.init()
    nids.register_tcp(_handle_tcp_stream)
    nids.register_udp(_handle_udp_stream)
    nids.register_ip(_handle_ip_packets)

    arp_sniff = Process(target=scapy_sniff, kwargs=dict(store=0,
            iface=_device, prn=_parse_arp))
    dns_lookups = Process(target=_handle_dns_lookup)
    traf_dict = Process(target=_handle_new_traf)
    arp_sniff.start()
    dns_lookups.start()
    traf_dict.start()

    nids.run()

def _hex_str(h):
    return int(h.encode('hex'), 16)

# For RADIOTAP headers:
def _parse_arp(pkt):
    try:
        pkt = str(pkt)
        header_len = _hex_str(pkt[2])
        if len(pkt) == header_len + 62:
            offset = header_len+32
            pkt_type = _hex_str(pkt[offset:offset+2])
            if pkt_type == 0x0806:
                offset += 16 # +47
                src = '%s.%s.%s.%s'%(_hex_str(pkt[offset]),
                                     _hex_str(pkt[offset+1]),
                                     _hex_str(pkt[offset+2]),
                                     _hex_str(pkt[offset+3]))
                offset += 10
                dst = '%s.%s.%s.%s'%(_hex_str(pkt[offset]),
                                     _hex_str(pkt[offset+1]),
                                     _hex_str(pkt[offset+2]),
                                     _hex_str(pkt[offset+3]))
                _traf_queue.put((src, dst, 0x0806))
    except: # Do nothing. Probably invalid index.
        pass

def _handle_tcp_stream(tcp):
    sport, dport = tcp.addr[0][1], tcp.addr[1][1]
    if tcp.nids_state == nids.NIDS_JUST_EST:
        if sport in UNWANTED_TCP_PORTS or dport in UNWANTED_TCP_PORTS:
            tcp.client.collect = False
            tcp.server.collect = False
        else:
            tcp.client.collect = True
            tcp.server.collect = True
    elif tcp.nids_state == nids.NIDS_DATA:
        if len(tcp.client.data) + len(tcp.server.data) >= 1e7: # 10 MB
            tcp.client.collect = False
            tcp.server.collect = False
            try:
                tcp.discard(tcp.client.count)
                tcp.discard(tcp.server.count)
            except:
                pass # Just in case.
        tcp.discard(0)
    elif tcp.nids_state in _END_STATES:
        _tcp_parse_queue.put((tcp.client.data, tcp.server.data))
        try:
            tcp.discard(tcp.client.count)
            tcp.discard(tcp.server.count)
        except:
            pass # Just in case.

def _handle_udp_stream(addr_tuple, data, pkt):
    dport = addr_tuple[1][1]
    if dport == 53: # DNS Replies port
        domain = ''
        for i in data:
            if ord(i) not in range(45, 123):
                i = '.' # Replace non-legible chars
            domain = domain + i
        domain = domain[10:].strip('.') # Remove lead/trail replaced chars
        if 'whois' not in domain and domain not in UNWANTED_DOMAINS \
                and _get_authoratative_domain(domain) not in UNWANTED_DOMAINS:
            _dns_queue.put(domain)
            _dns_lookup_queue.put(domain)

def _handle_ip_packets(ip):
    # Determine the type of traffic the provided packet is.
    traf_type = ord(ip[9])
    sport = _hex_str(ip[20:22])
    dport = _hex_str(ip[22:24])
    if sport in UNWANTED_IP_PORTS or dport in UNWANTED_IP_PORTS:
        return # Ignore lookup traffic
    if sport == 53 or dport == 53:
        traf_type = 53
    # Determine the sending and recieving IP addresses.
    src = '%s.%s.%s.%s'%(_hex_str(ip[12]), _hex_str(ip[13]),
                         _hex_str(ip[14]), _hex_str(ip[15]))
    dst = '%s.%s.%s.%s'%(_hex_str(ip[16]), _hex_str(ip[17]),
                         _hex_str(ip[18]), _hex_str(ip[19]))
    _traf_queue.put((src, dst, traf_type))

def _handle_dns_lookup():
    # call from the process after lookup instead of hanging the sniffer
    while True:
        domain = _dns_lookup_queue.get()
        domain = _get_host_by_name(_get_authoratative_domain(domain))
        #domain = _get_authoratative_domain(domain)

        if domain not in UNWANTED_DOMAINS:
            dns_dict = _dns.dict
            if domain not in dns_dict:
                dns_dict[domain] = 0
            dns_dict[domain] += 1
            _dns.dict = dns_dict

def _handle_new_traf():
    # Timestamps and the function to clean them must be put into the
    # same process's scope because Queues are not picklable objects.
    # Becuase of this, a dictionary of queues cannot be shared between
    # two processes since sharing the dictionary requires the queues
    # to be pickled.
    timestamps = {}
    def cleantimestamps():
        while True:
            time.sleep(_interval)
            wait_time = time.time()
            _timestamp_cleanup_lock.acquire()
            call_time = time.time()
            wait_time = call_time - wait_time
            #_traf_dict_access_lock.acquire()
            keys = timestamps.keys()
            for k in keys:
                try:
                    try:
                        for i,v in enumerate(timestamps[k].queue):
                            timestamps[k].queue[i] += wait_time
                    except(Exception, e):
                        print(e)
                    while not timestamps[k].empty() \
                            and timestamps[k].queue[0] < call_time-_interval:
                        timestamps[k].get(timeout=0.01)
                except:
                    pass # Ignore if the queue was empty for some reason.
                _traf_dict[k] = timestamps[k].qsize()
            #_traf_dict_access_lock.release()
            _timestamp_cleanup_lock.release()
    Thread(target=cleantimestamps).start()

    while True:
        conn_info = _traf_queue.get()

        src = _get_host_by_addr(conn_info[0])
        dst = _get_host_by_addr(conn_info[1])
        traf_type = conn_info[2]

        if traf_type == 0x0806: # ARP
            _arp_queue.put((src, dst))

        addr_tuple = (src, dst, traf_type)

        #_traf_dict_access_lock.acquire()
        if addr_tuple not in timestamps.keys():
            timestamps[addr_tuple] = qQueue()
        timestamps[addr_tuple].put(time.time())

        if addr_tuple not in _traf_dict.keys():
            _traf_dict[addr_tuple] = 0
        amount_traffic = timestamps[addr_tuple].qsize()
        _traf_dict[addr_tuple] = amount_traffic
        #_traf_dict_access_lock.release()

def _get_host_by_name(domain):
    if domain in _host_table:
        return _host_table[domain]
    else:
        _timestamp_cleanup_lock.acquire()
        host = os.popen('whois %s | grep "Tech Organization" | cut -d: -f2'%domain).read().strip()
        _timestamp_cleanup_lock.release()
        if 'Privacy' in host:
            host = domain
        elif host == '' or host == 'null':
            try:
                host = socket.gethostbyname(domain)
                host = _get_host_by_addr(host)
            except:
                host = domain
        _host_table[domain] = host
        return host

def _get_host_by_addr(ip):
    if ip in _ip_table:
        return _ip_table[ip]
    else:
        _timestamp_cleanup_lock.acquire()
        hosts = os.popen("whois %s | grep 'OrgName' | cut -d: -f2"%ip).read().strip()
        _timestamp_cleanup_lock.release()
        hosts = re.split(r'\n\s*', hosts)
        host = hosts[0]
        for h in hosts:
            if h not in UNWANTED_HOSTS:
                host = h
        if host in UNWANTED_HOSTS:
            try:
                host = socket.gethostbyaddr(ip)[0]
                host = _get_authoratative_domain(host)
            except:
                host = ip
        _ip_table[ip] = host
        return host

def _get_authoratative_domain(domain):
    t, s, l = 0, 0, 0 # Third last, second last, and last dots in the string
    for i,c in enumerate(domain):
        if c == '.':
            t, s, l = s, l, i
    if domain[s+1:] in NONTRUNCATED_DOMAINS:
        s = t # Need to differentiate nodes with common authorative domains
              # by not truncating the address.
    if domain[s] == '.':
        s += 1 # Remove leading '.' if one exists.
    return domain[s:]

