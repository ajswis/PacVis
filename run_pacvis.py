#!/usr/bin/env python2

from PyQt4 import QtGui
from multiprocessing import Process, Manager
from multiprocessing.queues import Queue
from collections import OrderedDict
from gui.qt_mainwindow import PacVisMainWindow
import processing, sys

if __name__ == '__main__':
    manager = Manager()
    # TODO:
    # These namespaces could be condensed to a
    # single namespace with multiple set values.
    rt_graphs = manager.Namespace()
    rt_graphs.dict = OrderedDict()
    at_graph = manager.Namespace()
    at_graph.total = ()
    at_graph.specifics = [() for i in range(6)]
    dns_dict = manager.Namespace()
    dns_dict.dict = OrderedDict()
    pic_queue = Queue()
    filename_queue = Queue()
    dns_queue = Queue()
    arp_queue = Queue()
    processing.init(rt_graphs, at_graph, dns_dict, pic_queue,
            filename_queue, dns_queue, arp_queue, interval=6.0, device='mon0')

    app = QtGui.QApplication(sys.argv)
    pacvis = PacVisMainWindow(rt_graphs, at_graph, dns_dict,
            pic_queue, filename_queue, dns_queue, arp_queue)

    Process(target=processing.start).start()
    sys.exit(app.exec_())

