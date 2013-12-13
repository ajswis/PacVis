from multiprocessing import Process, Manager
from multiprocessing.queues import Queue
from collections import OrderedDict
import sniffer, re, zlib, hashlib, time, pydot

_initialized = False

def init(rt_graphs, at_graph, dns_dict, pic_queue=Queue(),
        filename_queue=Queue(), dns_queue=Queue(), arp_queue=Queue(),
        interval=5.0, device='mon0'):
    global _interval, _rt_graphs, _at_graph, _pic_queue,\
            _filename_queue, _dns, _manager, _traf_dict,\
            _tcp_parse_queue, _traffic_colors, _initialized

    _interval = interval
    _rt_graphs = rt_graphs
    _at_graph = at_graph
    _pic_queue = pic_queue
    _filename_queue = filename_queue
    _dns = dns_dict

    _manager = Manager()
    _traf_dict = _manager.dict()
    _tcp_parse_queue = Queue()

    _traffic_colors = OrderedDict()
    _traffic_colors[1] = 'orange' # ICMP
    _traffic_colors[2] = 'yellow' # IGMP
    _traffic_colors[6] = 'red'    # TCP
    _traffic_colors[17] = 'blue'  # UDP
    _traffic_colors[53] = 'green' # DNS
    _traffic_colors[0x0806] = 'purple' # ARP

    sniffer.init(
            rt_traf_dict = _traf_dict,
            dns_dict = _dns,
            interval = _interval,
            tcp_queue = _tcp_parse_queue,
            dns_queue = dns_queue,
            arp_queue = arp_queue,
            device = device)

    _initialized = True

def start():
    if not _initialized:
        raise NameError('Module vars were not initialized.')

    build_rt_graph = Process(target=_update_graph,
            args=(True,'realtime',_interval))
    build_at_graph = Process(target=_update_graph, args=(False,'alltime',6))
    parse_tcp = Process(target=_parse_finished_tcp)
    build_rt_graph.start()
    build_at_graph.start()
    parse_tcp.start()
    sniffer.sniff()

def _parse_finished_tcp():
    ucmpr = re.compile(r'(?<=Content-Encoding:\s).*(?=\r\n)')
    rcode = re.compile(r'(?<=HTTP/\d.\d\s)\d{3}(?=\s)')
    contt = re.compile(r'(?<=Content-Type:\s).*(?=\r\n)')
    cname = re.compile(r'GET\s.*\sHTTP/\d.\d\r\n')

    def is_compressed(data):
        comp_encoded = ucmpr.search(data)
        if comp_encoded != None:
            comp_types = ('gzip', 'x-gzip', 'deflate')
            for ct in comp_types:
                if ct in comp_encoded.group():
                    return comp_encoded.group()
        return False

    def stream_returned_ok(data):
        return_code =  rcode.search(data)
        if return_code != None:
            return return_code.group() in ('200', '304')
        return False

    def is_wanted_content(data):
        content = contt.search(data)
        if content != None:
            types = ('image') #, 'text', 'javascript')
            for t in types:
                if t in content.group():
                    return True
        return False

    def get_content_name(http_dump):
        name = cname.search(http_dump)
        if name != None:
            name = name.group().split()[1]
            name = re.sub(r'(\?.*|;.*|&.*)', '', name) # Remove trailing url vars
            if len(name) > 200:
                name = name[:200]
            return name
        return 'no_name_'+hashlib.md5(http_dump).hexdigest()

    def queue_content(data, name, compressed=False):
        if compressed:
            data = zlib.decompress(data, 16+zlib.MAX_WBITS)
        if len(data) > 4000:
            _pic_queue.put(data)

    def queue_fname(name):
        _filename_queue.put(get_content_name(name))

    while True:
        client_data, server_data, conn = _tcp_parse_queue.get()
        with open('tcp_streams/client-%s:%s-%s:%s'%(conn[0][0],conn[0][1],conn[1][0],conn[1][1]),'w') as f:
            f.write(client_data)
        with open('tcp_streams/server-%s:%s-%s:%s'%(conn[1][0],conn[1][1],conn[0][0],conn[0][1]),'w') as f:
            f.write(server_data)

        # Split HTTP responses and combine into matching groups consisting
        # of HTTP return code and remaining HTTP info plus payload.
        stream = re.split(r'(HTTP/\d.\d\s\d{3}\s.*?\r\n)', client_data, 1)
        stream = [[i,j] for i,j in zip(stream[1::2], stream[2::2])]
        for data in stream:
            try:
                pkt_info, payload = re.split(r'\r\n.*?\r\n\r\n', data[1], 1)
                if (stream_returned_ok(data[0]) and
                        is_wanted_content(pkt_info)):
                    queue_content(payload, is_compressed(pkt_info))
            except ValueError:
                pass # re.split doesn't have enough values to unpack
        stream = re.split(r'(GET.*?\r\n)', server_data)
        if len(stream) == 3: # re.split creates ['', name_line, junk] on success
            queue_fname(stream[1])

# It may just be better to seperate realtime and alltime graph generation into
# different functions.
# graph_id is used if saving the generated image to differentiate realtime
# and alltime graphs
def _update_graph(realtime, graph_id, interval):
    while True:
        time.sleep(interval)

        graph = _convert_dict_to_graph(realtime)
        image = graph.create_png(prog='twopi')
        if realtime:
            rt_graphs = _rt_graphs.dict
            rt_graphs[time.strftime('%I:%M:%S')] = image
            while len(rt_graphs) > 200:
                keys = rt_graphs.keys()
                del rt_graphs[keys[0]]
            _rt_graphs.dict = rt_graphs
            rt_graphs = None # Just in case.
        else:
            _at_graph.total = (time.strftime('%I:%M:%S'), image)
            # Omit unknown traffic from specialized graphs.
            specific_graphs = _at_graph.specifics
            for i,v in enumerate(_traffic_colors):
                graph = _convert_dict_to_graph(realtime, (v,))
                image = graph.create_png(prog='twopi')
                specific_graphs[i] = (time.strftime('%I:%M:%S'), image)
            _at_graph.specifics = specific_graphs

# Take in specific_types as a tuple that way, if I wanted, I could
# generate graphs of multiple specific connection types.
def _convert_dict_to_graph(realtime, specific_types=()):
    graph = pydot.Dot(graph_type='digraph', ranksep=3, ratio='auto')
    keys = _traf_dict.keys()
    for ip in keys:
        try:
            src = ip[0]
            dst = ip[1]
            # Get value if exists, else default to black.
            traffic_type = _traffic_colors.get(ip[2], 'black')
            amount_traffic = _traf_dict[ip] ** (0.5)
            if realtime:
                if amount_traffic > 0:
                    if amount_traffic > 10: amount_traffic = 10
                    if amount_traffic < 1: amount_traffic = 1
                else:
                    continue
            else:
                if specific_types and ip[2] not in specific_types:
                    continue
                amount_traffic = 1
            src_node = pydot.Node(src, shape='rectangle')
            dst_node = pydot.Node(dst, shape='rectangle')
            edge = pydot.Edge(src_node, dst_node, color=traffic_type,
                    penwidth=amount_traffic)
            graph.add_node(src_node)
            graph.add_node(dst_node)
            graph.add_edge(edge)
        except KeyError:
            pass # In case a race condition arises for _traf_dict. (It shouldn't.)
    return graph

