import win32api
from multiprocessing import Process
import win32con
import win32gui
import time
from buy import BuyPanel
from sell import SellPanel


class TradeApi:
    def __init__(self, trade_hwnd=None):
        self.trade_hwnd = trade_hwnd
        if trade_hwnd is None:
            self.__set_trade_hwnd()
        self.buy_panel = BuyPanel(self.trade_hwnd)
        self.sell_panel = SellPanel(self.trade_hwnd)

    def __set_trade_hwnd(self):
        hwnd_list = []
        win32gui.EnumWindows(lambda handle, param: param.append(handle), hwnd_list)
        for hwnd in hwnd_list:
            if win32gui.GetWindowText(hwnd) == "网上股票交易系统5.0" and "Afx:400000" in win32gui.GetClassName(hwnd):
                self.trade_hwnd = hwnd
                return
        print("未找到交易页面")

    def buy(self, stock_code, price, lot):
        confirm_pro = Process(target=handle_notice, args=(self.trade_hwnd, stock_code, price, lot))
        confirm_pro.start()
        return self.buy_panel.buy(stock_code, price, lot)

    def sell(self, stock_code, price, lot):
        confirm_pro = Process(target=handle_notice, args=(self.trade_hwnd, stock_code, price, lot))
        confirm_pro.start()
        return self.sell_panel.sell(stock_code, price, lot)

    def cancel(self):
        # todo
        pass

    def get_hold(self):
        # todo
        pass


def handle_notice(trade_hwnd, stock_code, price, lot):
    # 获取 desktop 句柄
    # desktop = win32gui.GetDesktopWindow()

    # 获取所有 提示信息 或 委托确认 弹出窗的句柄
    # 两者的共同特征是
    #       父句柄 是 #32769 Desktop 主窗口，pywin32 GetParent 函数获取的不是父窗口的句柄
    #       owner 句柄是 交易窗口主句柄
    # 根据 弹出窗口大小判断更快，所以按大小判断
    def call_back(handle, dialog_l):
        _left, _top, _right, _bottom = win32gui.GetWindowRect(handle)
        # (_right - _left == 300) and (_bottom - _top == 195)
        # print(win32gui.GetParent(handle))
        if win32gui.GetClassName(handle) == "#32770" and win32gui.GetWindow(handle, win32con.GW_OWNER) == trade_hwnd:
            if (_right - _left == 300) and (_bottom - _top == 195):
                dialog_l.append(handle)
            elif (_right - _left == 345) and (_bottom - _top == 229):
                dialog_l.append(handle)

    """ 下单 时的提示信息 """
    while True:
        dialog_list = []
        win32gui.EnumWindows(call_back, dialog_list)
        # 获得 每个 dialog 句柄的子句柄，判断出是 提示信息 或 委托确认 弹出窗
        notice_list = []
        confirm_list = []
        for dialog in dialog_list:
            li = []
            win32gui.EnumChildWindows(dialog, lambda handle, param: param.append(handle), li)
            for l in li:
                txt = win32gui.GetWindowText(l)
                if txt == "提示信息":
                    notice_list.append(dialog)
                elif txt == "委托确认":
                    confirm_list.append(dialog)

        if len(notice_list) > 1 or len(confirm_list) > 1:
            exit(-1)
        # 如果没有提示信息窗口，而存在委托窗口，判断无误下单后 退出
        if len(confirm_list) == 1 and len(notice_list) == 0:
            # 确认委托 或 取消委托 后退出
            confirm = confirm_list[0]
            confirm_info = {}
            confirm_son = []
            win32gui.EnumChildWindows(confirm, lambda handle, param: param.append(handle), confirm_son)
            for son in confirm_son:
                txt = win32gui.GetWindowText(son)
                # print(txt)
                cls = win32gui.GetClassName(son)
                left, top, right, bottom = win32gui.GetWindowRect(son)
                if cls == "Static" and right - left == 227:
                    confirm_info.update(info=txt)
                elif txt == "是(&Y)":
                    confirm_info.update(yes_btn=son)
                elif txt == "否(&N)":
                    confirm_info.update(no_btn=son)

            if stock_code in confirm_info["info"] and str(price) in confirm_info["info"] \
                    and str(lot*100) in confirm_info["info"]:
                win32api.PostMessage(confirm_info["yes_btn"], win32con.WM_LBUTTONDOWN, None, None)
                win32api.PostMessage(confirm_info["yes_btn"], win32con.WM_LBUTTONUP, None, None)
            else:
                win32api.PostMessage(confirm_info["no_btn"], win32con.WM_LBUTTONDOWN, None, None)
                win32api.PostMessage(confirm_info["no_btn"], win32con.WM_LBUTTONUP, None, None)
            return "成功"

        # 如果当前只存在 提示信息窗口
        if len(notice_list) == 1:
            notice = notice_list[0]
            notice_info = {}
            notice_son = []
            win32gui.EnumChildWindows(notice, lambda handle, param: param.append(handle), notice_son)
            for son in notice_son:
                txt = win32gui.GetWindowText(son)
                cls = win32gui.GetClassName(son)
                left, top, right, bottom = win32gui.GetWindowRect(son)
                if cls == "Static" and right-left == 300:
                    notice_info.update(info=txt)
                elif txt == "是(&Y)":
                    notice_info.update(yes_btn=son)
                elif txt == "否(&N)":
                    notice_info.update(no_btn=son)

            # 提示信息弹出框 发送取消 后，直接退出
            if "超出涨跌停限制" in notice_info["info"]:
                win32api.PostMessage(notice_info["no_btn"], win32con.WM_LBUTTONDOWN, None, None)
                win32api.PostMessage(notice_info["no_btn"], win32con.WM_LBUTTONUP, None, None)
                return
            # 如果发送 继续委托，还要继续循环


if __name__ == '__main__':
    trade_api = TradeApi()
    i = time.time()
    # for j in range(0, 5):
    msg = trade_api.buy("600029", 7.85, 1)
    print(msg)
    time.sleep(0.5)
    # print(win32gui.GetWindowText(0x001612AC))
    # print(win32gui.GetClassName(0x001612AC))
    msg = trade_api.sell("600029", 7.85, 1)
    print(msg)

    print(time.time() - i)