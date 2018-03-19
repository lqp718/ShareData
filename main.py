#!/C/Python27/python.exe
# -*- coding: UTF-8 -*-

import wx  
import logging
import threading
import multiprocessing
import time
import datetime

from error import trace_log
from Strategy import StockStrategy
from ShareDB import ShareDB
from RealtimeDB import Realtime

def is_valid_date(str):
	try:
		time.strptime(str, "%Y-%m-%d")
		return True
	except:
		return False

class Frame1(wx.Frame):
    def __init__(self,parent):
        wx.Frame.__init__(self, parent=parent, style = wx.CAPTION | wx.SIMPLE_BORDER | wx.MINIMIZE_BOX | wx.CLOSE_BOX, \
            title='TuShare Strategy system',size=(1380,800))
        # self.SetMaxSize((1380,800))
        self.thread = {
                    # "target" = function_thread,
                    }
        self.process = {
                    # "target" = function_process,
                    }

        self.thread_alive = {}
        self.process_alive = {}

        # 窗口布局，左右布局
        self.spW = wx.SplitterWindow(self, size = self.Size)
        self.panel = wx.Panel(self.spW, style=wx.SUNKEN_BORDER, size = (self.spW.Size.width / 2.0, self.spW.Size.height))
        self.pane2 = wx.Panel(self.spW, style=wx.SUNKEN_BORDER, size = (self.spW.Size.width / 2.0, self.spW.Size.height))
        self.notebookLog = wx.Notebook(self.pane2, id = -1, pos = (0,0), size = (self.pane2.Size.width, self.pane2.Size.height - 25))
        self.spW.SplitVertically(self.panel, self.pane2, self.Size.width / 2)

        # 数据收集交互框 >>>
        # 历史数据
        self.ShareDBbox = wx.RadioBox(self.panel, label='历史数据收集',pos=(30, 20), size=(550, 120), majorDimension=1, style=wx.RA_SPECIFY_ROWS)
        wx.StaticText(self.ShareDBbox, label = '输入股票代码:', pos=(30, 20), size=(100, 25))
        self.ShareCodeText = wx.TextCtrl(self.ShareDBbox, value = "600050", pos=(30, 45), size=(100, 25))
        wx.StaticText(self.ShareDBbox, label = '*注：第一次运行某只股票收据时是按照起始日期开始收集，二次运行时同只股票将按照历史数据库中的时间开始收集', pos=(220, 75), size=(320, 40))

        wx.StaticText(self.ShareDBbox,label = '输入起始日期yyyy-mm-dd:', pos=(200, 20), size=(200, 25))
        self.StartDateText = wx.TextCtrl(self.ShareDBbox, value = "2015-01-05", pos=(200, 45), size=(100, 25))

        self.btnShareDB = wx.Button(self.ShareDBbox, label="开始收集数据", pos=(350, 45), size=(90, 25))
        self.btnShareDBStop = wx.Button(self.ShareDBbox, label="停止", pos=(470, 45), size=(45, 25))

        # 实时数据
        self.ShareRealtimebox = wx.RadioBox(self.panel, label='实时数据收集',pos=(30, 160), size=(550, 100), majorDimension=1, style=wx.RA_SPECIFY_ROWS)
        wx.StaticText(self.ShareRealtimebox, label = '输入股票代码:', pos=(30, 20), size=(100, 25))
        self.ShareCodeRealTimeText = wx.TextCtrl(self.ShareRealtimebox, value = "600050", pos=(30, 45), size=(100, 25))
        wx.StaticText(self.ShareRealtimebox, label = '*注：此功能只能在交易日的上午9点25到下午15点之间使用！', pos=(220, 75), size=(330, 20))

        self.btnShareRealTime = wx.Button(self.ShareRealtimebox, label="开始收集数据", pos=(350, 45), size=(90, 25))
        self.btnShareRealTimeStop = wx.Button(self.ShareRealtimebox, label="停止", pos=(470, 45), size=(45, 25))
        # 数据收集交互框 <<<

        # 数据分析交互框 >>>
        self.ShareStrategybox = wx.RadioBox(self.panel, label='数据分析', pos=(30, 280), size=(550, 260), majorDimension=1, style=wx.RA_SPECIFY_ROWS)
        wx.StaticText(self.ShareStrategybox, label = '输入股票代码:', pos=(30, 20), size=(100, 25))
        self.ShareCodeStrategyText = wx.TextCtrl(self.ShareStrategybox, value = "600050", pos=(30, 45), size=(100, 25))
        wx.StaticText(self.ShareStrategybox, label = '*注：如果输入的股票代码在没有在数据库中列出，将尝试从网络中获取数据，建议提前通过数据收集模块收集历史数据', pos=(220, 75), size=(320, 40))

        wx.StaticText(self.ShareStrategybox, label = '输入均值以“-”分割（默认值为5日及20日均线）：', pos=(200, 20), size=(300, 25))
        self.ShareAverageText = wx.TextCtrl(self.ShareStrategybox, value = "5-20", pos=(200, 45), size=(100, 25))

        wx.StaticText(self.ShareStrategybox, label = '输入起始资金量（元）：', pos=(30, 140), size=(300, 25))
        self.ShareCashText = wx.TextCtrl(self.ShareStrategybox, value = "1000000", pos=(30, 165), size=(100, 25))

        self.btnShareKAverage = wx.Button(self.ShareStrategybox, label="绘制K线图", pos=(350, 45), size=(90, 25))
        self.btnShareSingal = wx.Button(self.ShareStrategybox, label="交易信号分析", pos=(440, 45), size=(90, 25))
        self.btnShareBackTest = wx.Button(self.ShareStrategybox, label="数据回测", pos=(350, 165), size=(90, 25))
        # 数据分析交互框 <<<

        # 系统日志显示 >>>
        self.LogText = wx.TextCtrl(self.notebookLog, style=wx.TE_MULTILINE | wx.TE_READONLY, size=self.notebookLog.Size)
        self.RealTimeText = wx.TextCtrl(self.notebookLog, style=wx.TE_MULTILINE | wx.TE_READONLY, size=self.notebookLog.Size)
        self.ShareDBText = wx.TextCtrl(self.notebookLog, style=wx.TE_MULTILINE | wx.TE_READONLY, size=self.notebookLog.Size)
        self.notebookLog.AddPage(self.LogText, "系统日志:",True)
        self.notebookLog.AddPage(self.ShareDBText, "历史数据:",False)
        self.notebookLog.AddPage(self.RealTimeText, "实时数据:",False)
        # 系统日志显示 <<<

        self.btnShareDB.Bind(wx.EVT_BUTTON,	self.CollectShareData)
        self.btnShareDBStop.Bind(wx.EVT_BUTTON, self.StopCollectShareData)

        self.btnShareRealTime.Bind(wx.EVT_BUTTON, self.CollectRealTimeData)
        self.btnShareRealTimeStop.Bind(wx.EVT_BUTTON, self.StopCollectRealTimeData)

        self.btnShareKAverage.Bind(wx.EVT_BUTTON, self.ShareKAverage)
        self.btnShareSingal.Bind(wx.EVT_BUTTON, self.ShareSingal)
        self.btnShareBackTest.Bind(wx.EVT_BUTTON, self.ShareBackTest)

        self.__attach_events()


    def __attach_events(self):
    	self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_SIZE, self.OnFrameSize)
    #
    # Collect Share data >>>
    #
    def CollectShareData(self,event):
        ShareCode = self.ShareCodeText.GetValue().replace(' ','')
        StartDate = self.StartDateText.GetValue().replace(' ','')
        if StartDate == "" or ShareCode == "":
            self.PopupMessage(message = "股票代码及起始日期不能为空！")
            return 0

        if not is_valid_date(StartDate):
            self.PopupMessage(message = "日期格式不符合yyyy-mm-dd！请正确输入如：2015-01-05")
            return 0

        try:
            share = ShareDB(sharecode = ShareCode, startdate = StartDate, output = self.ShareDBText)
            wx.LogMessage("开始收集历史数据...")
            # self.share.StopCollect = False
            self.StartThread(key = "ShareDB", target = share.GetHistoryData)
        except:
            trace_log()


    def StopCollectShareData(self, event):
        self.StopThread("ShareDB")

    #
    # Collect share data <<<

    # Collect real time share data >>>
    #
    def CollectRealTimeData(self, event):
        t = datetime.datetime.strptime(datetime.datetime.now().strftime('%H:%M:%S'), '%H:%M:%S')
        if t <= datetime.datetime.strptime("09:25:00", '%H:%M:%S') or \
           t >= datetime.datetime.strptime("15:00:00", '%H:%M:%S'):
           self.PopupMessage("此功能只能在交易日的上午9点25到下午15点之间使用！")
           return 0
        ShareCode = self.ShareCodeRealTimeText.GetValue().replace(' ','')
        RT = Realtime(sharecode = ShareCode, output = self.RealTimeText)
        wx.LogMessage("开始收集实时数据...")
        self.StartThread(key = "RealTimeData", target = RT.GetRealTimeData)

    def StopCollectRealTimeData(self, event):
        self.StopThread("RealTimeData")
    #
    # Collect real time share data <<<
    #

    def ShareKAverage(self, event):
        code = self.ShareCodeStrategyText.GetValue().replace(" ", "")
        ma_list = self.ShareAverageText.GetValue().split('-')
        s_Strategy = StockStrategy(code = code, start = "1970-01-01")
        self.StartProcess(key = "RealTimeData", target = s_Strategy.stock_average, ex_args = (ma_list, ))

    def ShareSingal(self, event):
        code = self.ShareCodeStrategyText.GetValue().replace(" ", "")
        ma_list = self.ShareAverageText.GetValue().split('-')
        print ma_list
        s_Strategy = StockStrategy(code = code, start = "1970-01-01")
        self.StartProcess(key = "RealTimeData", target = s_Strategy.stock_singal, ex_args = (ma_list[0], ma_list[1], ))

    def ShareBackTest(self, event):
        code = self.ShareCodeStrategyText.GetValue().replace(" ", "")
        ma_list = self.ShareAverageText.GetValue().split('-')
        cash = int(self.ShareCashText.GetValue().replace(" ", ''))
        s_Strategy = StockStrategy(code = code, start = "1970-01-01")
        self.StartProcess(key = "RealTimeData", target = s_Strategy.stock_backtest, ex_args = (cash, ma_list[0], ma_list[1], ))

    def PopupMessage(self, message = ""):
        self.msg1 = wx.MessageDialog(parent=None, message=message, caption="提示消息",\
                                     style=wx.OK | wx.ICON_INFORMATION)
        self.msg1.ShowModal()

    #
    # Multi-Thread progress function >>>
    #
    def StartThread(self, key, target, ex_args = None):
        """Start the receiver thread"""
        if key in self.thread.keys() and self.thread[key] is not None:
            wx.LogMessage("This jod is already started, please stop the pre-job and try again")
            return 0
        self.thread_alive[key] = threading.Event()
        if ex_args is not None:
        	args = (self.thread_alive[key],) + ex_args
        else:
        	args = (self.thread_alive[key],)
        self.thread[key] = threading.Thread(target=target, args = args)
        self.thread[key].setDaemon(True)
        self.thread_alive[key].set()
        self.thread[key].start()

    def StopThread(self, key = None):
        if key in self.thread.keys():
            if self.thread[key] is not None:
                wx.LogMessage("StopThread")
                self.thread_alive[key].clear()
                self.thread[key].join(1)
                self.thread_alive[key] = None
                self.thread[key] = None
                wx.LogMessage("StopThread stopped")
        elif key is None:
            for key in self.thread.keys():
                if self.thread[key] is None:
                    continue
                wx.LogMessage("StopThread")
                self.thread_alive[key].clear()
                self.thread[key].join(1)
                self.thread[key] = None
                wx.LogMessage("StopThread stopped")
    #
    # Multi-Thread progress function <<<
    #

    #
    # Multi-process progress function >>>
    #
    def StartProcess(self, key, target, ex_args = None):
        """Start the receiver process"""
        self.process_alive[key] = multiprocessing.Event()
        if ex_args is not None:
        	args = (self.process_alive[key],) + ex_args
        else:
        	args = (self.process_alive[key],)
        self.process[key] = multiprocessing.Process(target=target, args = args)
        self.process_alive[key].set()
        self.process[key].start()

    def StopProcess(self, key = None):
        if key in self.process.keys():
            if self.process[key] is not None:
                wx.LogMessage("StopProcess")
                self.process_alive[key].clear()
                self.process[key].join(1)
                self.process_alive[key] = None
                self.process[key] = None
                wx.LogMessage("StopProcess stopped")
        elif key is None:
            for key in self.process.keys():
                if self.process[key] is None:
                    continue
                wx.LogMessage("StopProcess")
                self.process_alive[key].clear()
                self.process[key].join(1)
                self.process[key] = None
                wx.LogMessage("StopProcess stopped")
    #
    # Multi-process progress function <<<
    #

    def write(self, s):
    	wx.LogMessage(s.replace("\n", ''))


    def OnClose(self, event):
        self.StopThread()
        self.Destroy()

    def OnFrameSize(self, event):
        size = event.Size
        self.spW.Size=size#这一句很重要
        self.spW.SetSashPosition(size.width / 2)
  
if __name__ == '__main__':
    app = wx.App()
    frame = Frame1(None)
    log_file = "ShareDB.log"
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(message)s",
        # filename = log_file,
        stream=frame
        )
    console_logger = logging.StreamHandler()
    console_logger.setLevel(logging.DEBUG)
    console_logger.setFormatter(logging.Formatter("%(message)s"))
    logging.getLogger().addHandler(console_logger)

    wx.Log.SetActiveTarget(wx.LogTextCtrl(frame.LogText))

    frame.Show()
    app.MainLoop()

