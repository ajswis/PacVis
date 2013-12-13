from PyQt4 import QtGui, QtCore
from time import strftime
from qt_imageviewer import ImageViewer

class RealtimeGraphVisualizer(QtGui.QWidget):
    def __init__(self, rt_graphs, at_graph):
        super(RealtimeGraphVisualizer, self).__init__()
        self.is_display_paused = False
        self.is_total_displayed = False
        self.scale_factor = 1.0
        self.rt_graphs = rt_graphs
        self.at_graph = at_graph
        self.last_rt_graph = ''
        self.last_at_graph = ''

        self.rt_graph_images = []
        self.at_graph_image = QtGui.QPixmap()

        self.init_ui()
        self.init_image_display()

        timer = QtCore.QTimer(self)
        QtCore.QObject.connect(timer, QtCore.SIGNAL('timeout()'),
                self.check_new_images)
        timer.start(1000)

    def init_ui(self):
        self.pause_updating = QtGui.QPushButton('Pause Updating')
        self.pause_updating.setCheckable(True)
        self.pause_updating.clicked.connect(self.pause_rt_update)
        self.running_total = QtGui.QPushButton('Display Total')
        self.running_total.setCheckable(True)
        self.running_total.clicked.connect(self.display_at_graph)

        self.graph_display = ImageViewer()
        self.graph_list = QtGui.QListWidget()
        self.graph_list.setMaximumWidth(90)

        left_layout = QtGui.QVBoxLayout()
        toolbar_layout = QtGui.QHBoxLayout()
        toolbar_layout.addWidget(self.pause_updating)
        toolbar_layout.addWidget(self.running_total)

        left_layout.addLayout(toolbar_layout)
        left_layout.addWidget(self.graph_display)
        right_layout = QtGui.QVBoxLayout()
        right_layout.addWidget(self.graph_list)
        global_layout = QtGui.QHBoxLayout()
        global_layout.addLayout(left_layout)
        global_layout.addLayout(right_layout)
        self.setLayout(global_layout)

        QtCore.QObject.connect(self.graph_list,
                QtCore.SIGNAL('itemClicked()'), self.display_stored_image)
        QtCore.QObject.connect(self.graph_list,
                QtCore.SIGNAL('itemSelectionChanged()'),
                self.display_stored_image)

    def init_image_display(self):
        #resolution = QtGui.QDesktopWidget().screenGeometry()
        #pbar = QtGui.QProgressBar()

        #window = QtGui.QMainWindow(self)
        #window.setCentralWidget(pbar)
        #window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        #window.resize(300, 40)
        #window.move((resolution.width() / 2) - (window.frameSize().width() / 2),
                #(resolution.height() / 2) - (window.frameSize().height() / 2))
        #window.show()

        rt_graphs = self.rt_graphs.dict
        for k in rt_graphs.keys():
            self.graph_list.insertItem(0, QtGui.QListWidgetItem(k))
            self.last_rt_graph = k
        #pbar.setRange(0, len(rt_graphs)+1)
        #for k,v in rt_graphs.iteritems():
            #image = QtGui.QImage.fromData(v)
            #pixmap = QtGui.QPixmap().fromImage(image)
            #if not pixmap.isNull():
                #self.rt_graph_images.insert(0, pixmap)
                #self.graph_list.insertItem(0, QtGui.QListWidgetItem(k))
                #self.last_rt_graph = k
            #pbar.setValue(rt_graphs.keys().index(k))
        if self.last_rt_graph != '':
            image = QtGui.QImage.fromData(rt_graphs[self.last_rt_graph])
            pixmap = QtGui.QPixmap().fromImage(image)
            self.graph_display.set_pixmap(pixmap)
        rt_graphs = None # Just in case.

        try:
            time, image = self.at_graph.graph
            image = QtGui.QImage.fromData(image)
            pixmap = QtGui.QPixmap.fromImage(image)
            if not pixmap.isNull():
                self.at_graph_image = pixmap
                self.last_at_graph = time
            #pbar.setValue(len(rt_graphs)+1)
        except ValueError:
            # Nothing was in stored in self.at_graph.graph yet.
            pass
        #window.close()

    def check_new_images(self):
        rt_graphs = self.rt_graphs.dict
        new_images = False
        for k in rt_graphs.keys():
            if self.last_rt_graph == '':
                new_images = True
            if k == self.last_rt_graph:
                new_images = True
                continue
            if new_images:
                self.graph_list.insertItem(0, QtGui.QListWidgetItem(k))
                self.last_rt_graph = k
                while self.graph_list.count() > 200:
                    self.graph_list.takeItem(200)
                #image = QtGui.QImage.fromData(v)
                #pixmap = QtGui.QPixmap().fromImage(image)
                #if not pixmap.isNull():
                    #self.rt_graph_images.insert(0, pixmap)
                    #self.graph_list.insertItem(0, QtGui.QListWidgetItem(k))
                    #self.last_rt_graph = k
                    #while len(self.rt_graph_images) > 200:
                        #del self.rt_graph_images[200]
                    #while self.graph_list.count() > 200:
                        #self.graph_list.takeItem(200)
                if not self.pause_updating.isChecked() \
                        and not self.running_total.isChecked():
                    image = QtGui.QImage.fromData(rt_graphs[self.last_rt_graph])
                    pixmap = QtGui.QPixmap().fromImage(image)
                    self.graph_display.set_pixmap(pixmap)

        try:
            time, image = self.at_graph.graph
            if time != self.last_at_graph:
                image = QtGui.QImage.fromData(image)
                pixmap = QtGui.QPixmap.fromImage(image)
                if not pixmap.isNull():
                    self.at_graph_image = pixmap
                    self.last_at_graph = time
        except ValueError:
            # Nothing was in stored in self.at_graph.graph.
            pass

    def display_at_graph(self):
        if self.running_total.isChecked():
            if not self.pause_updating.isChecked():
                self.pause_updating.toggle()
            self.graph_display.set_pixmap(self.at_graph_image)
        else:
            if self.pause_updating.isChecked():
                self.pause_updating.toggle()
            if self.last_rt_graph != '':
                rt_graphs = self.rt_graphs.dict
                image = QtGui.QImage.fromData(rt_graphs[self.last_rt_graph])
                pixmap = QtGui.QPixmap().fromImage(image)
                self.graph_display.set_pixmap(pixmap)
                rt_graphs = None # Just in case.

    def pause_rt_update(self):
        if self.running_total.isChecked():
            self.running_total.toggle()
        if not self.pause_updating.isChecked():
            rt_graphs = self.rt_graphs.dict
            image = QtGui.QImage.fromData(rt_graphs[self.last_rt_graph])
            pixmap = QtGui.QPixmap().fromImage(image)
            self.graph_display.set_pixmap(pixmap)
            rt_graphs = None # Just in case.

    def display_stored_image(self):
        if not self.pause_updating.isChecked():
            self.pause_updating.toggle()
        if self.running_total.isChecked():
            self.running_total.toggle()
        rt_graphs = self.rt_graphs.dict
        keys = rt_graphs.keys()[::-1]
        image = QtGui.QImage.fromData(rt_graphs[keys[self.graph_list.currentRow()]])
        pixmap = QtGui.QPixmap().fromImage(image)
        self.graph_display.set_pixmap(pixmap)
        keys = None # Just in case.
        rt_graphs = None # Just in case.
