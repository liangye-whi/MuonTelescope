import sys
import matplotlib
matplotlib.use('Qt5Agg')

from PyQt5 import QtCore, QtWidgets

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import numpy as np

global data,baseline,signal,peakHeight,peakArea,peakTime

class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setFixedWidth(1900)
        self.setFixedHeight(780)
        self.setWindowTitle("μ子望远镜数据分析系统")

        self.fname=""

        menuBar = self.menuBar()

        fileMenu = QtWidgets.QAction("打开(&O)", self)
        fileMenu.triggered.connect(self.openFile)
        menuBar.addAction(fileMenu)

        oscilloscopePanel = self.setupOscilloscopePanel()

        statPanel = QtWidgets.QVBoxLayout()

        self.statOptionComboBox = QtWidgets.QComboBox()
        self.statOptionComboBox.addItems(["Baseline","Peak Height","Peak Area (Charge)","Peak Time"])
        self.statOptionComboBox.currentIndexChanged.connect(self.setStatOption)
        self.statOptionComboBox.setDisabled(True)
        statPanel.addWidget(self.statOptionComboBox)

        statGrid = QtWidgets.QGridLayout()
        statChannelPanel = []
        self.ChannelCanvases = []
        for i in range(4):
            statChannelPanel.append(self.setupStatChannelPanel(channel=i))
            statGrid.addLayout(statChannelPanel[-1],0,i)
        for i in range(4):
            statChannelPanel.append(self.setupStatChannelPanel(channel=4+i,reverse=True))
            statGrid.addLayout(statChannelPanel[-1],1,i)

        statPanel.addLayout(statGrid)

        widgetLayout = QtWidgets.QHBoxLayout()
        widgetLayout.addLayout(oscilloscopePanel)
        #widgetLayout.addLayout(statPeakPanel)
        widgetLayout.addLayout(statPanel)
        # Create a placeholder widget to hold our toolbar and canvas.
        widget = QtWidgets.QWidget()
        widget.setLayout(widgetLayout)
        self.setCentralWidget(widget)

        self.statusBar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusBar)

        self.show()

    def setupOscilloscopePanel(self):
        layout = QtWidgets.QVBoxLayout()

        self.fnameLabel = QtWidgets.QLabel("当前文件：")
        self.fnameLabel.setFixedWidth(700)
        self.fnameLabel.setAlignment(QtCore.Qt.AlignLeft)
        self.sc = MplCanvas(self, width=7, height=10, dpi=100)
        toolbar = NavigationToolbar(self.sc, self)

        layout.addWidget(self.fnameLabel)
        layout.addWidget(toolbar)
        layout.addWidget(self.sc)

        eventSelectSubLayout = QtWidgets.QHBoxLayout()

        self.totalEventsNumberLabel = QtWidgets.QLabel("0个事例")
        eventSelectSubLayout.addWidget(self.totalEventsNumberLabel,0,QtCore.Qt.AlignRight)
        self.eventSelectSpinBox = QtWidgets.QSpinBox()
        self.eventSelectSpinBox.setRange(0,0)
        self.eventSelectSpinBox.setFixedWidth(100)
        self.eventSelectSpinBox.valueChanged.connect(self.eventConfirmed)
        eventSelectSubLayout.addWidget(self.eventSelectSpinBox)

        layout.addLayout(eventSelectSubLayout)
        return layout

    def setupStatChannelPanel(self,channel,reverse=False):
        global data
        layout = QtWidgets.QVBoxLayout()
        self.ChannelCanvases.append(MplCanvas(self, width=4,height=3, dpi=80))
        toolbar = NavigationToolbar(self.ChannelCanvases[-1], self)
        #self.peakCanvas.axes.plot()
        #self.peakCanvas.draw()
        self.ChannelCanvases[-1].axes.set_title("Channel %d"%channel)
        if reverse == False:
            layout.addWidget(toolbar)
        layout.addWidget(self.ChannelCanvases[-1])
        if reverse == True:
            layout.addWidget(toolbar)
        return layout

    def openFile(self):
        global data
        self.fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file',filter="numpy data files (*.npy)")[0]
        if self.fname=="":
            return
        self.fnameLabel.setText("当前文件：%s"%(self.fname if len(self.fname)<=62 else "..."+self.fname[-65:]) )
        data = np.load(self.fname).astype("int")
        print(data.shape)
        self.eventSelectSpinBox.setRange(0,data.shape[0]-1)
        self.eventSelectSpinBox.setValue(0)
        self.totalEventsNumberLabel.setText("%d个事例(0-%d)"%(data.shape[0],data.shape[0]-1))
        self.eventConfirmed()
        self.statPerChannel()
        self.statOptionComboBox.setEnabled(True)
        self.setStatOption()

    def eventConfirmed(self):
        global data
        self.sc.axes.cla()
        value = self.eventSelectSpinBox.value()
        self.statusBar.showMessage("Triggered! value = %d"%value)
        #if data.shape[0]!=0:
        if self.fname!="":
            for i in range(data.shape[1]):
                self.sc.axes.plot(data[value,i]-30*i,label="Ch%d"%i)
        self.sc.axes.legend()
        self.sc.draw()

    def setStatOption(self):
        if self.statOptionComboBox.currentText() == "Baseline":
            self.statusBar.showMessage("Baseline")
            self.updateBaselineStat()
        if self.statOptionComboBox.currentText() == "Peak Height":
            self.statusBar.showMessage("Peak height")
            self.updatePeakStat()
        if self.statOptionComboBox.currentText() == "Peak Area (Charge)":
            self.statusBar.showMessage("Peak area")
            self.updateChargeStat()
        if self.statOptionComboBox.currentText() == "Peak Time":
            self.statusBar.showMessage("Peak time")
            self.updateTimeStat()

    def statPerChannel(self):
        global data,baseline,signal,peakHeight,peakArea,peakTime
        baseline = np.mean(data[:,:,:250],axis=2)
        signal = baseline[:,:,np.newaxis]-data
        peakHeight = np.max(signal,axis=2)
        peakArea = np.sum(signal[:,:,750:900],axis=2)
        peakTime = np.argmax(signal,axis=2)

    def updateBaselineStat(self):
        global data,baseline,signal,peakHeight
        for ch in range(data.shape[1]):
            self.ChannelCanvases[ch].axes.cla()
            self.ChannelCanvases[ch].axes.set_title("Channel %d"%ch)
            self.ChannelCanvases[ch].axes.hist(baseline[:,ch],bins=50)
            self.ChannelCanvases[ch].draw()

    def updatePeakStat(self):
        global data,baseline,signal,peakHeight
        for ch in range(data.shape[1]):
            self.ChannelCanvases[ch].axes.cla()
            self.ChannelCanvases[ch].axes.set_title("Channel %d"%ch)
            self.ChannelCanvases[ch].axes.hist(peakHeight[:,ch],bins=50)
            self.ChannelCanvases[ch].draw()
        
    def updateChargeStat(self):
        global data,baseline,signal,peakHeight,peakArea
        for ch in range(data.shape[1]):
            self.ChannelCanvases[ch].axes.cla()
            self.ChannelCanvases[ch].axes.set_title("Channel %d"%ch)
            self.ChannelCanvases[ch].axes.hist(peakArea[:,ch],bins=50)
            self.ChannelCanvases[ch].draw()

    def updateTimeStat(self):
        global data,baseline,signal,peakTime
        for ch in range(data.shape[1]):
            self.ChannelCanvases[ch].axes.cla()
            self.ChannelCanvases[ch].axes.set_title("Channel %d"%ch)
            self.ChannelCanvases[ch].axes.hist(peakTime[:,ch],bins=50)
            self.ChannelCanvases[ch].draw()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion');
    w = MainWindow()
    app.exec_()
