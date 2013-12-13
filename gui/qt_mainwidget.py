from PyQt4 import QtGui, QtCore
from qt_imageviewer import ImageViewer
from multiprocessing import Queue

class ScaledIcon(QtGui.QLabel):
    def __init__(self, pixmap, sq_dim):
        super(ScaledIcon, self).__init__()
        self.pixmap = pixmap
        self.scaled_pixmap = self.pixmap.scaled(sq_dim, sq_dim,
                QtCore.Qt.KeepAspectRatio)
        self.setPixmap(self.scaled_pixmap)

    def mouseDoubleClickEvent(self, event):
        window = QtGui.QMainWindow(self)
        window.setCentralWidget(ImageViewer(self.pixmap))
        window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        window.resize(800, 600)
        window.show()

class PacVisMainWidget(QtGui.QWidget):
    def __init__(self, pic_queue, fname_queue, dns_queue, arp_queue):
        super(PacVisMainWidget, self).__init__()
        self.pic_queue = pic_queue
        self.fname_queue = fname_queue
        self.dns_queue = dns_queue
        self.arp_queue = arp_queue

        self.initUI()

        timer = QtCore.QTimer(self)
        QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"),
                self.update_pic)
        QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"),
                self.update_filename)
        QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"),
                self.update_dns)
        QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"),
                self.update_arp)
        timer.start(250)

    def initUI(self):
        fname_label = QtGui.QLabel('HTTP GET Requests')
        fname_label.setAlignment(QtCore.Qt.AlignCenter)
        self.fname_disp = QtGui.QListWidget()
        self.fname_disp.setMaximumWidth(275)
        self.fname_disp.setMinimumWidth(275)
        arp_label = QtGui.QLabel('ARP Requests')
        arp_label.setAlignment(QtCore.Qt.AlignCenter)
        self.arp_disp = QtGui.QListWidget()
        self.arp_disp.setMaximumWidth(275)
        self.arp_disp.setMinimumWidth(275)
        dns_label = QtGui.QLabel('DNS Requests')
        dns_label.setAlignment(QtCore.Qt.AlignCenter)
        self.dns_disp = QtGui.QListWidget()
        self.dns_disp.setMaximumWidth(275)
        self.dns_disp.setMinimumWidth(275)

        self.grid = QtGui.QGridLayout()
        pic_disp = QtGui.QWidget()
        pic_disp.setLayout(self.grid)
        self.scroll_area = QtGui.QScrollArea()
        self.scroll_area.setWidget(pic_disp)

        fname_layout = QtGui.QVBoxLayout()
        fname_layout.addWidget(fname_label)
        fname_layout.addWidget(self.fname_disp)

        dns_arp_layout = QtGui.QVBoxLayout()
        dns_arp_layout.addWidget(arp_label)
        dns_arp_layout.addWidget(self.arp_disp)
        dns_arp_layout.addWidget(dns_label)
        dns_arp_layout.addWidget(self.dns_disp)

        main_layout = QtGui.QHBoxLayout()
        main_layout.addWidget(self.scroll_area)
        main_layout.addLayout(fname_layout)
        main_layout.addLayout(dns_arp_layout)
        self.setLayout(main_layout)

    def update_pic(self):
        if not self.pic_queue.empty():
            try:
                pic = self.pic_queue.get(timeout=0.2)
            except: #Queue.Empty
                return

            pixmap = QtGui.QPixmap()
            if pixmap.loadFromData(pic):
                old_grid = self.grid
                self.grid = QtGui.QGridLayout()
                for r in reversed(range(0, old_grid.rowCount()+1)):
                    for c in reversed(range(0, 5)):
                        if c > 0:
                            next_item = old_grid.itemAtPosition(r, c-1)
                            if next_item is None or next_item == None:
                                continue
                            self.grid.addWidget(next_item.widget(), r, c)
                        elif r > 0:
                            next_item = old_grid.itemAtPosition(r-1, 4)
                            if next_item is None or next_item == None:
                                continue
                            self.grid.addWidget(next_item.widget(), r, c)
                edge_len = (self.scroll_area.size().width()-65)/5
                self.grid.addWidget(ScaledIcon(pixmap, edge_len), 0, 0)
                to_delete = self.grid.takeAt(100)
                if to_delete is not None and to_delete != None:
                    to_delete.widget().deleteLater()
                    to_delete = None
                pic_disp = QtGui.QWidget()
                pic_disp.setLayout(self.grid)
                # Explicitly delete the old widget.
                to_delete = self.scroll_area.takeWidget()
                to_delete.deleteLater()
                to_delete = None
                self.scroll_area.setWidget(pic_disp)

    def update_filename(self):
        if not self.fname_queue.empty():
            try:
                self.fname_disp.insertItem(0, self.fname_queue.get(timeout=0.2))
                to_delete = self.fname_disp.takeItem(200)
                if to_delete is not None or to_delete != None:
                    to_delete.deleteLater()
                    to_delete = None
            except: # Queue.Empty
                return

    def update_arp(self):
        if not self.arp_queue.empty():
            try:
                text = '%s -> %s'%self.arp_queue.get(timeout=0.2)
                self.arp_disp.insertItem(0, text)
                to_delete = self.arp_disp.takeItem(200)
                if to_delete is not None or to_delete != None:
                    to_delete.deleteLater()
                    to_delete = None
            except: #Queue.Empty
                return

    def update_dns(self):
        if not self.dns_queue.empty():
            try:
                self.dns_disp.insertItem(0, self.dns_queue.get(timeout=0.2))
                to_delete = self.dns_disp.takeItem(200)
                if to_delete is not None or to_delete != None:
                    to_delete.deleteLater()
                    to_delete = None
            except: #Queue.Empty
                return

