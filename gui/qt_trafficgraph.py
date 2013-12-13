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
        self.last_specific_graphs = ['' for i in range(6)]

        self.rt_graph_images = []
        self.at_graph_image = QtGui.QPixmap()
        self.specific_at_graph_images = [QtGui.QPixmap() for i in range(6)]

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
        self.alltime_total_button = QtGui.QPushButton('Alltime Total')
        self.alltime_total_button.setCheckable(True)
        self.alltime_total_button.clicked.connect(self.display_at_total)

        self.last_checked = -1
        self.alltime_specific_buttons = [QtGui.QPushButton() for i in range(6)]
        for i in self.alltime_specific_buttons:
            i.setCheckable(True)
            i.clicked.connect(self.display_at_specific)
        self.alltime_specific_buttons[0].setText('Alltime ICMP')
        self.alltime_specific_buttons[1].setText('Alltime IGMP')
        self.alltime_specific_buttons[2].setText('Alltime TCP')
        self.alltime_specific_buttons[3].setText('Alltime UDP')
        self.alltime_specific_buttons[4].setText('Alltime DNS')
        self.alltime_specific_buttons[5].setText('Alltime ARP')

        self.graph_display = ImageViewer()
        self.graph_list = QtGui.QListWidget()
        self.graph_list.setMaximumWidth(90)

        left_layout = QtGui.QVBoxLayout()
        toolbar_layout1 = QtGui.QHBoxLayout()
        toolbar_layout1.addWidget(self.pause_updating)
        toolbar_layout1.addWidget(self.alltime_total_button)
        toolbar_layout2 = QtGui.QHBoxLayout()
        for i in self.alltime_specific_buttons:
            toolbar_layout2.addWidget(i)

        left_layout.addLayout(toolbar_layout1)
        left_layout.addLayout(toolbar_layout2)
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
        rt_graphs = self.rt_graphs.dict
        for k in rt_graphs.keys():
            self.graph_list.insertItem(0, QtGui.QListWidgetItem(k))
            self.last_rt_graph = k
        if self.last_rt_graph != '':
            image = QtGui.QImage.fromData(rt_graphs[self.last_rt_graph])
            pixmap = QtGui.QPixmap().fromImage(image)
            self.graph_display.set_pixmap(pixmap)

        self.at_graph_image, self.last_at_graph = \
                self.update_at_graph(self.at_graph.total, self.last_at_graph,
                        self.at_graph_image)
        specific_graphs = self.at_graph.specifics
        for i,v in enumerate(specific_graphs):
            self.specific_at_graph_images[i], self.last_specific_graphs[i] = \
                    self.update_at_graph(v, self.last_specific_graphs[i],
                            self.specific_at_graph_images[i])

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
                if not self.pause_updating.isChecked() \
                        and not self.alltime_total_button.isChecked():
                    at_specific_ischecked = False
                    for i in self.alltime_specific_buttons:
                        at_specific_ischecked = at_specific_ischecked or i.isChecked()
                    if not at_specific_ischecked:
                        image = QtGui.QImage.fromData(rt_graphs[self.last_rt_graph])
                        pixmap = QtGui.QPixmap().fromImage(image)
                        self.graph_display.set_pixmap(pixmap)

        self.at_graph_image, self.last_at_graph = \
                self.update_at_graph(self.at_graph.total, self.last_at_graph,
                        self.at_graph_image)
        specific_graphs = self.at_graph.specifics
        for i,v in enumerate(specific_graphs):
            self.specific_at_graph_images[i], self.last_specific_graphs[i] = \
                    self.update_at_graph(v, self.last_specific_graphs[i],
                            self.specific_at_graph_images[i])

    def update_at_graph(self, graph_info, last_graph, last_graph_pixmap):
        try:
            time, image = graph_info
            if time != last_graph:
                image = QtGui.QImage.fromData(image)
                pixmap = QtGui.QPixmap.fromImage(image)
                if not pixmap.isNull():
                    return pixmap, time
        except ValueError:
            # Nothing was in stored in self.at_graph.ATTRIBUTE
            pass # Only needed the before the first graphs are generated.
        # Stick to using the previous image and timestamp if a new one did
        # not appear.
        return last_graph_pixmap, last_graph

# The following four functions are in desperate need of refactoring
# and consolidation.
    def display_at_total(self):
        if self.alltime_total_button.isChecked():
            if not self.pause_updating.isChecked():
                self.pause_updating.toggle()
            for i in self.alltime_specific_buttons:
                if i.isChecked():
                    i.toggle()
            self.last_checked = -1
            self.graph_display.set_pixmap(self.at_graph_image)
        else:
            if self.pause_updating.isChecked():
                self.pause_updating.toggle()
            if self.last_rt_graph != '':
                rt_graphs = self.rt_graphs.dict
                image = QtGui.QImage.fromData(rt_graphs[self.last_rt_graph])
                pixmap = QtGui.QPixmap().fromImage(image)
                self.graph_display.set_pixmap(pixmap)

    def display_at_specific(self):
        checked_button = -1
        for i,v in enumerate(self.alltime_specific_buttons):
            if v.isChecked() and self.last_checked != i:
                checked_button = i
        if checked_button > -1:
            self.last_checked = checked_button
            for i,v in enumerate(self.alltime_specific_buttons):
                if i != checked_button and v.isChecked():
                    v.toggle()
            if not self.pause_updating.isChecked():
                self.pause_updating.toggle()
            if self.alltime_total_button.isChecked():
                self.alltime_total_button.toggle()
            self.graph_display.set_pixmap(self.specific_at_graph_images[checked_button])
        else:
            self.last_checked = -1
            if self.pause_updating.isChecked():
                self.pause_updating.toggle()
            if self.last_rt_graph != '':
                rt_graphs = self.rt_graphs.dict
                image = QtGui.QImage.fromData(rt_graphs[self.last_rt_graph])
                pixmap = QtGui.QPixmap().fromImage(image)
                self.graph_display.set_pixmap(pixmap)

    def pause_rt_update(self):
        self.last_checked = -1
        if self.alltime_total_button.isChecked():
            self.alltime_total_button.toggle()
        for i in self.alltime_specific_buttons:
            if i.isChecked():
                i.toggle()
        if not self.pause_updating.isChecked():
            rt_graphs = self.rt_graphs.dict
            image = QtGui.QImage.fromData(rt_graphs[self.last_rt_graph])
            pixmap = QtGui.QPixmap().fromImage(image)
            self.graph_display.set_pixmap(pixmap)

    def display_stored_image(self):
        self.last_checked = -1
        if not self.pause_updating.isChecked():
            self.pause_updating.toggle()
        if self.alltime_total_button.isChecked():
            self.alltime_total_button.toggle()
        for i in self.alltime_specific_buttons:
            if i.isChecked():
                i.toggle()
        rt_graphs = self.rt_graphs.dict
        keys = rt_graphs.keys()[::-1]
        image = QtGui.QImage.fromData(rt_graphs[keys[self.graph_list.currentRow()]])
        pixmap = QtGui.QPixmap().fromImage(image)
        self.graph_display.set_pixmap(pixmap)

