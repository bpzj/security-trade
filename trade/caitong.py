import ctypes
import win32api

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
        get_notice_hwnd(self.__parent_trade)
        # todo 查找提醒消息，委托确认窗口，校验内容后，确认下单

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


def get_notice_hwnd(trade_hwnd=None):
    """ 下单 时的提示信息 """
    # 获取所有 dialog 句柄,
    # 提示信息 的父句柄不是 主窗口，
    def call_back(handle, hwnd_list):
        if win32gui.GetClassName(handle) == "#32770":
            hwnd_list.append(handle)

    hwnd_l = []
    win32gui.EnumWindows(call_back, hwnd_l)
    if trade_hwnd:
        for hwnd in hwnd_l:
            owner_hwnd = win32gui.GetWindow(hwnd, win32con.GW_OWNER)
            if owner_hwnd == trade_hwnd:
                return hwnd

    # for hwnd in hwnd_l:
    #     # 获得 每个 dialog 句柄的子句柄，根据子句柄的内容判断出 dialog 是在 买入界面 或者 卖出界面
    #     li = []
    #     win32gui.EnumChildWindows(hwnd, lambda handle, param: param.append(handle), li)
    #     for l in li:
    #         if win32gui.GetWindowText(l) == "提示信息":
    #             return hwnd


if __name__ == '__main__':
    trade_api = TradeApi()
    i = time.time()
    trade_api.buy("000001", 2, 3)
    print(get_item_text(get_notice_hwnd()))
    print(time.time() - i)
