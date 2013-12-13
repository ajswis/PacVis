from PyQt4 import QtGui, QtCore
from numpy import arange
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class DNSHistogram(FigureCanvas):
    def __init__(self, dns_dict):
        fig = Figure(figsize=(250, 50), dpi=75)
        self.axes = fig.add_subplot(111)
        self.dns = dns_dict

        FigureCanvas.__init__(self, fig)
        FigureCanvas.setSizePolicy(self,
                QtGui.QSizePolicy.Expanding,
                QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        timer = QtCore.QTimer(self)
        QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"), self.update_figure)
        timer.start(5000) # milliseconds
        self.update_figure()

    def update_figure(self):
        dns_dict = self.dns.dict
        if len(dns_dict) == 0:
            return

        labels = dns_dict.keys()
        pos = arange(len(labels)) + 0.5
        vals = dns_dict.values()

        self.axes.barh(pos, vals, color='green')
        self.axes.set_yticks(pos)
        self.axes.set_yticklabels(labels)

        self.axes.relim()
        self.axes.autoscale_view()
        self.draw()
