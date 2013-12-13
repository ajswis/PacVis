from PyQt4 import QtGui, QtCore

class ImageViewer(QtGui.QWidget):
    def __init__(self, *args):
        super(ImageViewer, self).__init__()
        self.scale_factor = 1
        self.init_ui()
        if args:
            self.set_pixmap(args[0])

    def init_ui(self):
        self.image_display = QtGui.QLabel()
        self.image_display.setBackgroundRole(QtGui.QPalette.Base)
        self.image_display.setSizePolicy(QtGui.QSizePolicy.Ignored,
                QtGui.QSizePolicy.Ignored)
        self.image_display.setScaledContents(True)

        self.scroll_area = QtGui.QScrollArea()
        self.scroll_area.setWidget(self.image_display)
        self.scroll_area.setBackgroundRole(QtGui.QPalette.Light)

        zoom_in = QtGui.QPushButton('+')
        zoom_in.clicked.connect(self.zoom_in)
        zoom_out = QtGui.QPushButton('-')
        zoom_out.clicked.connect(self.zoom_out)

        main_layout = QtGui.QVBoxLayout()
        toolbar_layout = QtGui.QHBoxLayout()
        toolbar_layout.addWidget(zoom_in)
        toolbar_layout.addWidget(zoom_out)

        main_layout.addLayout(toolbar_layout)
        main_layout.addWidget(self.scroll_area)
        self.setLayout(main_layout)

    def set_pixmap(self, pixmap):
        self.pixmap = pixmap
        self.image_display.setPixmap(self.pixmap)
        self.scale_factor = 1.0
        self.image_display.adjustSize()
        self.fit_to_frame()

    def fit_to_frame(self):
        size = self.image_display.size()
        h, w = size.height(), size.width()
        max_h = self.scroll_area.size().height()+25
        max_w = self.scroll_area.size().width()+25
        while h > max_h or w > max_w:
            self.zoom_out()
            size = self.image_display.size()
            h, w = size.height(), size.width()

    def zoom_in(self):
        self.scale_image(1.25)

    def zoom_out(self):
        self.scale_image(0.80)

    def scale_image(self, factor):
        self.scale_factor *= factor
        self.image_display.resize(self.scale_factor
                * self.image_display.pixmap().size())
        self.adjust_scroll_bar(self.scroll_area.horizontalScrollBar(), factor)
        self.adjust_scroll_bar(self.scroll_area.verticalScrollBar(), factor)

    def adjust_scroll_bar(self, scroll_bar, factor):
        scroll_bar.setValue(int(factor * scroll_bar.value()
                + ((factor-1) * scroll_bar.pageStep()/2)))

