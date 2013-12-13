from PyQt4 import QtGui, QtCore
from qt_trafficgraph import RealtimeGraphVisualizer
from qt_histogram import DNSHistogram
from qt_mainwidget import PacVisMainWidget

class PacVisMainWindow(QtGui.QMainWindow):
    def __init__(self, rt_graphs, at_graph, dns_dict,
            pic_queue, filename_queue, dns_queue, arp_queue):
        super(PacVisMainWindow, self).__init__()
        self.rt_graphs = rt_graphs
        self.at_graph = at_graph
        self.dns_dict = dns_dict

        graph_view = QtGui.QAction(QtGui.QIcon(), 'Network Graph', self)
        graph_view.triggered.connect(self.handle_new_graph_window)
        histo_view = QtGui.QAction(QtGui.QIcon(), 'Network DNS Histogram', self)
        histo_view.triggered.connect(self.handle_new_hist_window)

        self.toolbar = self.addToolBar('Utility Windows')
        self.toolbar.addAction(graph_view)
        self.toolbar.addAction(histo_view)

        self.setCentralWidget(PacVisMainWidget(pic_queue,
                filename_queue, dns_queue, arp_queue))
        self.setWindowTitle('PacVis')
        self.showMaximized()
        self.show()

    def handle_new_graph_window(self):
        window = QtGui.QMainWindow(self)
        window.setCentralWidget(RealtimeGraphVisualizer(self.rt_graphs, self.at_graph))
        window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        window.setWindowTitle('PacVis Realtime Graphic Display')
        window.setMinimumSize(900, 600)
        window.showMaximized()

    def handle_new_hist_window(self):
        window = QtGui.QMainWindow(self)
        window.setCentralWidget(DNSHistogram(self.dns_dict))
        window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        window.setWindowTitle('PacVis DNS Histogram')
        window.setMinimumSize(900, 600)
        window.showMaximized()

