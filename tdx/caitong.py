import ctypes
import win32api
from multiprocessing import Process

import win32con
import win32gui
import pywintypes
import time


class TradeApi:
    def __init__(self, trade_hwnd=None):
        self.trade_hwnd = trade_hwnd
        if trade_hwnd is None:
            self.__set_trade_hwnd()
        self.buy_panel = BuyPanel(self.trade_hwnd)

    def __set_trade_hwnd(self):
        hwnd_list = []
        win32gui.EnumWindows(lambda handle, param: param.append(handle), hwnd_list)
        for hwnd in hwnd_list:
            if win32gui.GetWindowText(hwnd) == "网上股票交易系统5.0" and "Afx:400000" in win32gui.GetClassName(hwnd):
                self.trade_hwnd = hwnd
                return
        print("未找到交易页面")

    def buy(self, stock_code, price, lot):
        p = Process(target=handle_notice, args=(self.trade_hwnd, stock_code, price, lot))
        print(p.start())
        self.buy_panel.buy(stock_code, price, lot)

    def sell(self, stock_code, price, lot):
        # todo
        pass

    def cancel(self):
        # todo
        pass

    def get_hold(self):
        # todo
        pass


class BuyPanel:
    def __init__(self, trade_hwnd):
        self.__parent_trade = trade_hwnd
        self.__handle = None
        self.__hwnd_list = None
        self.__edit_set = {}

    def __enter_buy_panel(self):
        """
        向主句柄 发送 F1，调出 买入股票 界面
        :return:
        """
        win32gui.PostMessage(self.__parent_trade, win32con.WM_KEYDOWN, win32con.VK_F1, 0)
        win32gui.PostMessage(self.__parent_trade, win32con.WM_KEYUP, win32con.VK_F1, 0)

    def __init_handle(self):
        """ 获取 买入界面的 handle 值， 买入界面 的 子句柄
        每点击几次 买入和卖出界面的 句柄都会重建，所以先校验 当前的 handle是否有效
        :return:
        """
        if self.__handle:
            son_of_trade = []
            win32gui.EnumChildWindows(self.__parent_trade, lambda handle, param: param.append(handle), son_of_trade)
            if self.__handle in son_of_trade:
                li = []
                win32gui.EnumChildWindows(self.__handle, lambda handle, param: param.append(handle), li)
                for l in li:
                    if win32gui.GetWindowText(l) == "买入股票":
                        return

        # 如果无效，向下执行，要先 发送 F1 , 调出界面
        self.__enter_buy_panel()

        # 获取所有 dialog 子句柄
        def call_back(handle, hwnd_list):
            if win32gui.GetClassName(handle) == "#32770":
                hwnd_list.append(handle)
        hwnd_l = []
        win32gui.EnumChildWindows(self.__parent_trade, call_back, hwnd_l)
        for hwnd in hwnd_l:
            # 获得 每个 dialog 句柄的子句柄，根据子句柄的内容判断出 dialog 是在 买入界面 或者 卖出界面
            li = []
            win32gui.EnumChildWindows(hwnd, lambda handle, param: param.append(handle), li)
            for l in li:
                if win32gui.GetWindowText(l) == "买入股票":
                    self.__handle = hwnd
                    self.__hwnd_list = li
                    break
        # 更新 证券代码，买入价格，买入数量，买入按钮 四个有用的句柄
        self.__set_useful_handle()

    def __set_useful_handle(self):
        """
        根据 买入界面的 handle 获取 证券代码，买入价格，买入数量，买入按钮 四个有用的句柄
        :return:
        """
        static_set = {}
        edit_list = []
        for hwnd in self.__hwnd_list:
            text = win32gui.GetWindowText(hwnd)
            cls = win32gui.GetClassName(hwnd)
            if text == "证券代码" and cls == "Static":
                static_set.update(code=hwnd)
            elif text == "买入价格" and cls == "Static":
                static_set.update(price=hwnd)
            elif text == "买入数量" and cls == "Static":
                static_set.update(lot=hwnd)
            elif text == "买入[B]" and cls == "Button":
                self.__edit_set.update(buy_btn=hwnd)
            elif cls == "Edit":
                edit_list.append(hwnd)

        code_txt_pos = win32gui.GetWindowRect(static_set["code"])
        price_txt_pos = win32gui.GetWindowRect(static_set["price"])
        lot_txt_pos = win32gui.GetWindowRect(static_set["lot"])

        for edit in edit_list:
            left, top, right, bottom = win32gui.GetWindowRect(edit)
            if code_txt_pos[2] < left < code_txt_pos[2] + 5:
                vertical = (top + bottom) / 2
                if code_txt_pos[1] < vertical < code_txt_pos[3]:
                    self.__edit_set.update(code=edit)
                elif price_txt_pos[1] < vertical < price_txt_pos[3]:
                    self.__edit_set.update(price=edit)
                elif lot_txt_pos[1] < vertical < lot_txt_pos[3]:
                    self.__edit_set.update(lot=edit)

    def buy(self, stock_code, price, lot):
        self.__init_handle()
        self.__send_msg(stock_code, price, lot)

    def __send_msg(self, stock_code, price, lot):
        # 使用 windows 消息机制 登录
        win32gui.SendMessage(self.__edit_set["code"], win32con.WM_SETTEXT, None, stock_code)

        # WM_SETTEXT 不管用，使用 WM_CHAR 消息，先删除原来的内容
        text = get_item_text(self.__edit_set["price"])
        if text:
            for i in range(0, len(text)):
                win32api.PostMessage(self.__edit_set["price"], win32con.WM_CHAR, win32con.VK_BACK, 0)
        content = str(price)
        for char in list(content):
            win32api.PostMessage(self.__edit_set["price"], win32con.WM_CHAR, ord(char), 0)
        win32api.SendMessage(self.__edit_set["lot"], win32con.WM_SETTEXT, None, str(lot * 100))

        win32api.PostMessage(self.__edit_set["buy_btn"], win32con.WM_LBUTTONDOWN, None, None)
        win32api.PostMessage(self.__edit_set["buy_btn"], win32con.WM_LBUTTONUP, None, None)
        # time.sleep(0.04)


class SellPanel:
    def __init__(self, dialog_hwnd):

        pass


def get_item_text(hwnd, max_len=4):
    while True:
        # 创建char[]
        buf = ctypes.create_string_buffer(max_len)
        # 获取内容
        if win32gui.SendMessage(hwnd, win32con.WM_GETTEXT, max_len//2, buf) == 0:
            return None
        # 如果以0,0,0,0结尾，说明缓冲区够大
        if (buf.raw[-4], buf.raw[-3], buf.raw[-2], buf.raw[-1]) == (0, 0, 0, 0):
            # 转成utf-8
            text = pywintypes.UnicodeFromRaw(buf.raw)
            # 去掉末尾的0就能返回
            return text.strip('\00')
        # 否则把缓冲区扩大一倍重试
        else:
            max_len *= 2


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
        print(confirm_list)
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
                    print(txt)
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
    # for j in range(0, 10):
    trade_api.buy("600029", 7.85, 1)
    # print(win32gui.GetWindowText(0x001612AC))
    # print(win32gui.GetClassName(0x001612AC))

    print(time.time() - i)
    # print(win32gui.GetWindowText(0x240688))

