from operator import index
from re import X
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from pyqtgraph import *
from pyqtgraph import PlotWidget, PlotItem
import pyqtgraph as pg
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os
import pathlib
import numpy as np
from pyqtgraph.Qt import _StringIO
from DSP3 import Ui_MainWindow
from DSP3 import MplCanvas
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog
from PyQt5.QtGui import QIcon
from matplotlib.figure import Figure
from fpdf import FPDF
import pyqtgraph.exporters
from scipy.io import wavfile


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        #______________________________Timers for the three different signals________________________#
        self.timer1 = QtCore.QTimer()
        self.timer2 = QtCore.QTimer()
        self.timer3 = QtCore.QTimer()

        #______________________________IMPORTANT INSTANCE VARIABLES___________________________________#
        self.SIGNAL_INDEX=self.ui.SIGNALS.currentIndex()#-----------SIGNALS COMOBOBOX INDEX
        self.SPECTRO_INDEX=self.ui.SPECTROGRAMS.currentIndex()#-----SPECTROGRAMS COMBOBOX INDEX
        self.Color_index = self.ui.COLORS.currentIndex()#------COLORS COMBOBOX INDEX
        self.Interval=100 #-----------------------------------INITIAL VALUE FOR TIME INTERVAL
        self.pen1 = pg.mkPen(color=(0, 0, 255)) #-----Blue
        self.pen2 = pg.mkPen(color=(0, 255, 0)) #-----GREEN
        self.pen3 = pg.mkPen(color=(255, 0, 0)) #-----RED
        self.Pen = [self.pen1, self.pen2,self.pen3]
        self.GraphicsView = [self.ui.graphicsView]
        self.data_lines=[]
        self.Timer = [self.timer1, self.timer2,self.timer3]
        self.SIGNAL_X=[[],[],[]]
        self.SIGNAL_Y=[[],[],[]]
        #______________________________________CONNECTING BUTTONS WITH THEIR FUNCTIONS____________________________#
        self.ui.OPEN.clicked.connect(lambda: self.load())
        self.ui.PLAY.clicked.connect(lambda: self.play())
        self.ui.PAUSE.clicked.connect(lambda: self.pause())
        self.ui.CLEAR.clicked.connect(lambda: self.clear())
        self.ui.ZOOMIN.clicked.connect(lambda: self.zoomIn())
        self.ui.ZOOMOUT.clicked.connect(lambda: self.zoomOut())
        self.ui.HIDE.clicked.connect(lambda: self.HIDE())
        self.ui.SHOW.clicked.connect(lambda: self.SHOW())
        self.ui.ADD.clicked.connect(lambda: self.ADD_LABEL())
        self.ui.SPECTRO_PLAY.clicked.connect(lambda: self.SPECTROGRAM())
        self.ui.SPEED_UP.clicked.connect(lambda: self.speed_up())
        self.ui.SPEED_DOWN.clicked.connect(lambda: self.speed_down())
        self.ui.SETCOLOR.clicked.connect(lambda: self.Choose_Color())
        self.ui.horizontalScrollBar.valueChanged.connect(self.Scroll_X)
        self.ui.verticalScrollBar.valueChanged.connect(self.Scroll_Y)
        self.ui.ADD.clicked.connect(lambda:self.ADD_LABEL())
        self.ui.EXPORT.clicked.connect(lambda:self.generate_pdf())
        

    #_____________________________________________BUTTTONS FUNCTIONS_______________________________________________________#     
    
    def read_file(self, Channel_ID):#----------------->>BROWSE TO READ THE FILE<<
        path = QFileDialog.getOpenFileName()[0]
        if pathlib.Path(path).suffix == ".csv":
            self.data = np.genfromtxt(path, delimiter=',')
            self.x = list(self.data[:, 0])
            self.y = list(self.data[:, 1])
            self.SIGNAL_X[Channel_ID]=self.x
            self.SIGNAL_Y[Channel_ID]=self.y

    def load(self):#------------------------>>LOAD THE SIGNAL AND PLOT IT<<
        self.Color_index = self.ui.COLORS.currentIndex()
        self.COLOR_Pen=self.Pen[self.Color_index]
        Channel_ID=self.ui.SIGNALS.currentIndex()
        self.read_file(Channel_ID)
        self.data_lines.append(self.GraphicsView[0].plot(self.x, self.y, pen=self.COLOR_Pen))
        self.GraphicsView[0].plotItem.setLabel("bottom", text="Time (ms)")
        self.GraphicsView[0].plotItem.showGrid(True, True, alpha=1)
        self.GraphicsView[0].plotItem.setLimits(xMin=0, xMax=12, yMin=-0.6, yMax=0.6)
        self.IDX = 0
        self.Timer[Channel_ID].setInterval(100)
        self.Timer[Channel_ID].timeout.connect(lambda: self.update_plot_data(Channel_ID))
        self.Timer[Channel_ID].start()

    
    def update_plot_data(self, Channel_ID):#------------>>UPDATE THE VALUES FOR A LIVE SIGNAL<<
        self.Color_index = self.ui.COLORS.currentIndex()
        self.COLOR_Pen=self.Pen[self.Color_index]
        x = self.x[:self.IDX]
        y = self.y[:self.IDX]
        self.IDX += 10
        if self.IDX > len(self.x):
            self.IDX = 0
        if self.x[self.IDX] > 0.5:
            self.GraphicsView[0].setLimits(xMin=min(x, default=0),#!!!
                                            xMax=max(x, default=0))  # disable paning over xlimits
        self.GraphicsView[0].plotItem.setXRange(max(x, default=0) - 0.5, max(x, default=0))
        self.data_lines[Channel_ID].setData(x, y)


    def play(self):#------------------------------->>RESUME THE SIGNAL<<
        Channel_ID=self.ui.SIGNALS.currentIndex()
        self.Timer[Channel_ID].start()

    def pause(self):#------------------------------>>PAUSE THE SIGNAL<<
        Channel_ID=self.ui.SIGNALS.currentIndex()
        self.Timer[Channel_ID].stop()

    def clear(self):#------------------------------>>CLEAR THE GRAPH<<
        Channel_ID=self.ui.SIGNALS.currentIndex()
        self.GraphicsView[0].clear()
        self.pause()

    def zoomIn(self):#----------------->>ZOOMIN THE GRAPH<<
        xrange, yrange = self.GraphicsView[0].viewRange()
        self.GraphicsView[0].setYRange(yrange[0] / 2, yrange[1] / 2, padding=0)
        self.GraphicsView[0].setXRange(xrange[0] / 2, xrange[1] / 2, padding=0)

    def zoomOut(self):#---------------->>ZOOMOUT THE GRAPH<<
        xrange, yrange = self.GraphicsView[0].viewRange()
        self.GraphicsView[0].setYRange(yrange[0] * 2, yrange[1] * 2, padding=0)
        self.GraphicsView[0].setXRange(xrange[0] * 2, xrange[1] * 2, padding=0)

    
    def SPECTROGRAM(self):#-------------------->>DRAW THE SPECTROGRAM<<
        self.SPECTRO_INDEX=self.ui.SPECTROGRAMS.currentIndex()
        for i in reversed(range(self.ui.verticalLayout_3.count())):
            self.ui.verticalLayout_3.itemAt(i).widget().deleteLater()
        PALETTES_INDEX=self.ui.COLOR_PALETTE.currentIndex()
        PALLETES=['viridis','plasma','inferno','magma','cividis']
        MINVALUE=self.ui.verticalSlider_MIN.value()
        MAXVALUE=self.ui.verticalSlider_MAX.value()
        self.ui.sc_1 = MplCanvas(self.ui.verticalLayoutWidget_2, width=5, height=5, dpi=100)
        self.ui.verticalLayout_3.addWidget(self.ui.sc_1)
        spec, freqs, t, im = self.ui.sc_1.axes.specgram(self.SIGNAL_Y[self.SPECTRO_INDEX],Fs=200,cmap=PALLETES[PALETTES_INDEX],vmin=MINVALUE, vmax=MAXVALUE)
        self.ui.sc_1.figure.colorbar(im).set_label('Intensity [dB]')
        self.ui.sc_1.draw()
        

    def HIDE(self):#-------------------------->>HIDE THE SIGNAL<<
        Channel_ID=self.ui.SIGNALS.currentIndex()
        self.data_lines[Channel_ID].hide()
    
    def SHOW(self):#-------------------------->>SHOW THE SIGNAL<<
        Channel_ID=self.ui.SIGNALS.currentIndex()
        self.data_lines[Channel_ID].show()
    
    def ADD_LABEL(self):#--------------------->>ADD SIGNAL LABEL<<
        Channel_ID=self.ui.SIGNALS.currentIndex()
        self.LABEL=["","",""]
        self.LABEL[Channel_ID]=self.ui.SIGNAL_LABEL.text()
        self.Color_index = self.ui.COLORS.currentIndex()
        self.COLOR_Pen=self.Pen[self.Color_index]
        self.data_lines[Channel_ID] = self.GraphicsView[0].plot(self.SIGNAL_X[Channel_ID], self.SIGNAL_Y[Channel_ID], pen=self.COLOR_Pen)
        self.GraphicsView[0].plotItem.setLabel("bottom", text="Time (ms)")
        self.GraphicsView[0].plotItem.showGrid(True, True, alpha=1)
        self.GraphicsView[0].plotItem.setLimits(xMin=0, xMax=12, yMin=-0.6, yMax=0.6)
        self.GraphicsView[0].plotItem.setLabel("top",text=self.LABEL[Channel_ID])
        self.IDX = 0
        self.Timer[Channel_ID].setInterval(100)
        self.Timer[Channel_ID].timeout.connect(lambda: self.update_plot_data(Channel_ID))
        self.Timer[Channel_ID].start()

    def Choose_Color(self):#------------------->>CHANGE SIGNAL PLOT COLOR<<
        Channel_ID=self.ui.SIGNALS.currentIndex()
        self.Color_index = self.ui.COLORS.currentIndex()
        self.COLOR_Pen=self.Pen[self.Color_index]
        self.data_lines[Channel_ID] = self.GraphicsView[0].plot(self.SIGNAL_X[Channel_ID], self.SIGNAL_Y[Channel_ID], pen=self.COLOR_Pen)
        self.GraphicsView[0].plotItem.setLabel("bottom", text="Time (ms)")
        self.GraphicsView[0].plotItem.showGrid(True, True, alpha=1)
        self.GraphicsView[0].plotItem.setLimits(xMin=0, xMax=12, yMin=-0.6, yMax=0.6)
        self.IDX = 0
        self.Timer[Channel_ID].setInterval(100)
        self.Timer[Channel_ID].timeout.connect(lambda: self.update_plot_data(Channel_ID))
        self.Timer[Channel_ID].start()

    def speed_up(self):#------------>>INCREASE SIGNAL SPEED<<
        Channel_ID=self.ui.SIGNALS.currentIndex()
        x = self.x[:self.IDX]
        y = self.y[:self.IDX]
        self.IDX += 30
        if self.IDX > len(self.x):
            self.IDX = 0
        if self.x[self.IDX] > 0.5:
            self.GraphicsView[0].setLimits(xMin=min(x, default=0),
                                                    xMax=max(x, default=0))  #---disable paning over xlimits
        self.GraphicsView[0].plotItem.setXRange(max(x, default=0) - 0.5, max(x, default=0))
        self.data_lines[Channel_ID].setData(x, y)
        self.Interval=self.Interval-10
        self.Timer[Channel_ID].setInterval(self.Interval)

    def speed_down(self):#------------>>DECREASE SIGNAL SPEED<<
        Channel_ID=self.ui.SIGNALS.currentIndex()
        x = self.x[:self.IDX]
        y = self.y[:self.IDX]
        self.IDX += 0
        if self.IDX > len(self.x):
            self.IDX = 0
        if self.x[self.IDX] > 0.5:
            self.GraphicsView[0].setLimits(xMin=min(x, default=0),
                                                    xMax=max(x, default=0))  # disable paning over xlimits
        self.GraphicsView[0].plotItem.setXRange(max(x, default=0) - 0.5, max(x, default=0))
        self.data_lines[Channel_ID].setData(x, y)
        self.Interval=self.Interval+10
        self.Timer[Channel_ID].setInterval(self.Interval)

    def Scroll_X(self, val):#-------------------->>X-SCROLL BAR<<
        new_index = int(val / self.ui.horizontalB_bar_limit * len(self.x))
        x_left, x_right = self.x[new_index] - .25, self.x[new_index] + 0.25
        self.GraphicsView[0].setXRange(x_left, x_right)

    def Scroll_Y(self, val):#-------------------->>Y-SCROLL BAR<<
        new_index = int(val / self.ui.Vertical_bar_limit * len(self.y))
        y_down, y_up = self.y[new_index] - 0.25, self.y[new_index] + 0.25
        self.GraphicsView[0].setYRange(y_down, y_up)

    def generate_pdf(self):
        exporter1 = pg.exporters.ImageExporter(self.ui.graphicsView.plotItem)
        exporter1.export('signals'+ '.png')
        self.images2=[]
        self.ui.sc_1.print_png('DSP.png')
        self.images = ['signals.png']
        Channel_ID=self.ui.SIGNALS.currentIndex()
        pdf = FPDF()
        # set pdf title
        pdf.add_page()
        pdf.set_font('Arial', 'B', 15)
        pdf.ln(80)
        pdf.cell(0, 0, 'Signals picture', 0, 1, 'C')
        pdf.image(self.images[0], 30, 20, 150, 50)
        pdf.add_page()
        pdf.ln(80)
        pdf.cell(0, 0, 'SPECTROS picture', 0, 1, 'C')
        pdf.image('DSP.png', 30, 20, 150, 50)
        #pdf.image(self.spectroImg_list[channel], 30, 80, 150, 100)
        pdf.add_page()
        pdf.set_font('Arial', 'B', 15)
        for Channel_ID in range (len(self.SIGNAL_X)):
            pdf.cell(60, 0, 'Signal no: ' + str(Channel_ID + 1), 0, 1, 'C')
            self.x_STRING = pd.Series(self.SIGNAL_X[Channel_ID])
            self.Y_STRING = pd.Series(self.SIGNAL_X[Channel_ID])
            self.x_STRING.describe().to_string()
            self.Y_STRING.describe().to_string()
            pdf.ln(10)
            pdf.multi_cell(70, 9, self.x_STRING.describe().to_string(), 1, 0, 'C')
            pdf.ln(10)
        pdf.output("report.pdf", "F")




    def close_app(self):
        sys.exit()
#---------------------------------END OF MAINWINDOW CLASS---------------------------------------------#


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
