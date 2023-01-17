from multiprocessing import Process
import time
from ctypes import windll
import pandas as pd
import win32api
import win32con
import win32gui
from pandas.io.clipboard import clipboard_get

from security_trade.util.ocr_util import ocr_string_from_hwnd
from security_trade.util.win32_util import get_item_text, GuiPosition, HwndType, pos_in_window_rect
from security_trade.verify import handle_verify


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
        return self.__get_order_msg()

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

    def __get_order_msg(self):
        # 判断窗口是不是提示窗口，是，就返回true
        def win_is_msg(hand):
            text = ""
            sons = []
            win32gui.EnumChildWindows(hand, lambda handle, param: param.append(handle), sons)
            for son in sons:
                if win32gui.GetClassName(son) in ["Static", "Button"]:
                    t = get_item_text(son)
                    if t:
                        text = text + t
            return "提示" in text and ("确定" in text or "终止" in text) and ("成功" in text or "失败" in text)

        #
        # 根据 弹出窗口大小判断更快，所以按大小判断
        def call_back(handle, dialog_l):
            _left, _top, _right, _bottom = win32gui.GetWindowRect(handle)
            # (_right - _left == 300) and (_bottom - _top == 195)
            # print(win32gui.GetParent(handle))
            if win32gui.GetClassName(handle) == "#32770" and \
                    win32gui.GetWindow(handle, win32con.GW_OWNER) == self.__parent_trade:
                # if (_right - _left == 362) or (_right - _left == 341):
                #     print(handle)
                #     dialog_l.append(handle)
                if win_is_msg(handle):
                    dialog_l.append(handle)

        # todo
        """ 下单 时不论成功失败，肯定在最后有一个 提示 弹框 """
        while True:
            dialog_list = []
            win32gui.EnumWindows(call_back, dialog_list)
            # 获得 每个 dialog 句柄的子句柄，判断出是 提示 弹出窗

            if len(dialog_list) > 1:
                exit(-1)
            # 如果没有提示信息窗口，而存在委托窗口，判断无误下单后 退出
            if len(dialog_list) == 0:
                time.sleep(0.01)
                continue

            if len(dialog_list) == 1:
                prompt = dialog_list[0]
                prompt_info = {}
                prompt_sons = []
                win32gui.EnumChildWindows(prompt, lambda handle, param: param.append(handle), prompt_sons)
                for prompt_son in prompt_sons:
                    txt = win32gui.GetWindowText(prompt_son)
                    if txt == "":
                        txt = get_item_text(prompt_son)
                    if txt and (("[" in txt and "]" in txt) or "成功" in txt):
                        prompt_info.update(info=str(txt).replace("\r\n", ""))
                    elif txt == "确定" or txt == "终止":
                        prompt_info.update(confirm_btn=prompt_son)

                # 提示信息弹出框 发送取消 后，直接退出
                win32api.PostMessage(prompt_info["confirm_btn"], win32con.WM_LBUTTONDOWN, None, None)
                win32api.PostMessage(prompt_info["confirm_btn"], win32con.WM_LBUTTONUP, None, None)
                return prompt_info["info"]
                # 如果发送 继续委托，还要继续循环


class SellPanel:
    def __init__(self, trade_hwnd):
        self.__parent_trade = trade_hwnd
        self.__handle = None
        self.__hwnd_list = None
        self.__edit_set = {}

    def __enter_sell_panel(self):
        """
        向主句柄 发送 F2，调出 卖出股票 界面
        :return:
        """
        win32gui.PostMessage(self.__parent_trade, win32con.WM_KEYDOWN, win32con.VK_F2, 0)
        win32gui.PostMessage(self.__parent_trade, win32con.WM_KEYUP, win32con.VK_F2, 0)

    def __init_handle(self):
        """ 获取 卖出界面的 handle 值， 卖出界面 的 子句柄
        每点击几次 卖出和卖出界面的 句柄都会重建，所以先校验 当前的 handle是否有效
        :return:
        """
        if self.__handle:
            son_of_trade = []
            win32gui.EnumChildWindows(self.__parent_trade, lambda handle, param: param.append(handle), son_of_trade)
            if self.__handle in son_of_trade:
                li = []
                win32gui.EnumChildWindows(self.__handle, lambda handle, param: param.append(handle), li)
                for l in li:
                    if win32gui.GetWindowText(l) == "卖出股票":
                        return

        # 如果无效，向下执行，要先 发送 F2 , 调出界面
        self.__enter_sell_panel()

        # 获取所有 dialog 子句柄
        def call_back(handle, hwnd_list):
            if win32gui.GetClassName(handle) == "#32770":
                hwnd_list.append(handle)

        hwnd_l = []
        win32gui.EnumChildWindows(self.__parent_trade, call_back, hwnd_l)
        for hwnd in hwnd_l:
            # 获得 每个 dialog 句柄的子句柄，根据子句柄的内容判断出 dialog 是在 卖出界面 或者 卖出界面
            li = []
            win32gui.EnumChildWindows(hwnd, lambda handle, param: param.append(handle), li)
            for l in li:
                if win32gui.GetWindowText(l) == "卖出股票":
                    self.__handle = hwnd
                    self.__hwnd_list = li
                    break
        # 更新 证券代码，卖出价格，卖出数量，卖出按钮 四个有用的句柄
        self.__set_useful_handle()

    def __set_useful_handle(self):
        """
        根据 卖出界面的 handle 获取 证券代码，卖出价格，卖出数量，卖出按钮 四个有用的句柄
        :return:
        """
        static_set = {}
        edit_list = []
        for hwnd in self.__hwnd_list:
            text = win32gui.GetWindowText(hwnd)
            cls = win32gui.GetClassName(hwnd)
            if text == "证券代码" and cls == "Static":
                static_set.update(code=hwnd)
            elif text == "卖出价格" and cls == "Static":
                static_set.update(price=hwnd)
            elif text == "卖出数量" and cls == "Static":
                static_set.update(lot=hwnd)
            elif text == "卖出[S]" and cls == "Button":
                self.__edit_set.update(sell_btn=hwnd)
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

    def sell(self, stock_code, price, lot):
        self.__init_handle()
        self.__send_msg(stock_code, price, lot)
        return self.__get_order_msg()

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

        win32api.PostMessage(self.__edit_set["sell_btn"], win32con.WM_LBUTTONDOWN, None, None)
        win32api.PostMessage(self.__edit_set["sell_btn"], win32con.WM_LBUTTONUP, None, None)
        # time.sleep(0.04)

    def __get_order_msg(self):
        # time.sleep(0.005)

        # 根据 弹出窗口大小判断更快，所以按大小判断
        def call_back(handle, dialog_l):
            _left, _top, _right, _bottom = win32gui.GetWindowRect(handle)
            # (_right - _left == 300) and (_bottom - _top == 195)
            # print(win32gui.GetParent(handle))
            if win32gui.GetClassName(handle) == "#32770" and \
                    win32gui.GetWindow(handle, win32con.GW_OWNER) == self.__parent_trade:
                if (_right - _left == 362) and (_bottom - _top == 204):
                    dialog_l.append(handle)

        """ 下单 时不论成功失败，肯定在最后有一个 提示 弹框 """
        while True:
            dialog_list = []
            win32gui.EnumWindows(call_back, dialog_list)
            # 获得 每个 dialog 句柄的子句柄，判断出是 提示 弹出窗
            prompt_list = []
            for dialog in dialog_list:
                li = []
                win32gui.EnumChildWindows(dialog, lambda handle, param: param.append(handle), li)
                for l in li:
                    txt = win32gui.GetWindowText(l)
                    if txt == "提示":
                        prompt_list.append(dialog)

            if len(prompt_list) > 1:
                exit(-1)
            # 如果没有提示信息窗口，而存在委托窗口，判断无误下单后 退出
            if len(prompt_list) == 0:
                time.sleep(0.01)
                continue

            if len(prompt_list) == 1:
                prompt = prompt_list[0]
                prompt_info = {}
                prompt_sons = []
                win32gui.EnumChildWindows(prompt, lambda handle, param: param.append(handle), prompt_sons)
                for prompt_son in prompt_sons:
                    txt = win32gui.GetWindowText(prompt_son)
                    left, top, right, bottom = win32gui.GetWindowRect(prompt_son)
                    if right - left == 332 and bottom - top == 129:
                        prompt_info.update(info=get_item_text(prompt_son))
                    elif txt == "确定" or txt == "终止":
                        prompt_info.update(confirm_btn=prompt_son)

                # 提示信息弹出框 发送取消 后，直接退出
                win32api.PostMessage(prompt_info["confirm_btn"], win32con.WM_LBUTTONDOWN, None, None)
                win32api.PostMessage(prompt_info["confirm_btn"], win32con.WM_LBUTTONUP, None, None)
                return prompt_info["info"]
                # 如果发送 继续委托，还要继续循环


class HoldPanel:
    def __init__(self, trade_hwnd):
        self.__parent_trade = trade_hwnd
        self.__hold_panel_hwnd = None
        self.__AfxMDIFrame_hwnd = None
        self.__hwnd_list = None
        self.__edit_set = {}
        self.__data_grid_hwnd = None
        self.available_cash = None

    def __enter_hold_panel(self):
        """
        向主句柄 发送 F4，调出 查询 - 资金股票 界面
        :return:
        """
        win32gui.PostMessage(self.__parent_trade, win32con.WM_KEYDOWN, win32con.VK_F4, 0)
        win32gui.PostMessage(self.__parent_trade, win32con.WM_KEYUP, win32con.VK_F4, 0)

    def __init_handle(self):
        # 发送 F4 , 调出界面
        self.__enter_hold_panel()

        """ 获取 持仓界面的 handle 值
            每点击几次 句柄都会重建，所以先校验 当前的 handle是否有效
        """
        if self.__hold_panel_hwnd:
            son_of_hold = []
            win32gui.EnumChildWindows(self.__parent_trade, lambda handle, param: param.append(handle), son_of_hold)
            if self.__hold_panel_hwnd in son_of_hold:
                li = []
                win32gui.EnumChildWindows(self.__hold_panel_hwnd, lambda handle, param: param.append(handle), li)
                for l in li:
                    if win32gui.GetWindowText(l) == "资金余额":
                        return

        # 获取所有 dialog 子句柄
        def call_back(handle, hwnd_list):
            txt = win32gui.GetWindowText(handle)
            if txt and txt == "资金余额":
                hwnd_list.append(win32gui.GetParent(handle))
                return

        hwnd_l = []
        win32gui.EnumChildWindows(self.__parent_trade, call_back, hwnd_l)
        self.__handle = hwnd_l[0]

        # 调用
        self.__set_useful_handle()

    def __set_useful_handle(self):
        """
        根据 持仓界面的 handle 获取 可用资金 数值， 持仓
        :return:
        """
        # 获得 根据子句柄
        li = []
        win32gui.EnumChildWindows(self.__handle, lambda handle, param: param.append(handle), li)
        for i in range(0, len(li)):
            if win32gui.GetWindowText(li[i]) == "可用金额":
                s = win32gui.GetWindowText(li[i + 3])
                self.available_cash = float(s) if s != '' else None
            elif win32gui.GetClassName(li[i]) == "CVirtualGridCtrl":
                self.__data_grid_hwnd = li[i]

    def __set_useful_handle_old(self):
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

    def get_hold(self):
        if windll.user32.OpenClipboard(None):  # 打开剪切板
            windll.user32.EmptyClipboard()  # 清空剪切板
            windll.user32.CloseClipboard()  # 关闭剪切板

        # 将窗口调到前台，激活
        self.__init_handle()
        # ctrl c
        win32api.keybd_event(win32con.VK_LCONTROL, 0, 0, 0)
        try:
            win32gui.SendMessageTimeout(self.__data_grid_hwnd, win32con.WM_KEYDOWN, win32api.VkKeyScan('c'), 0, win32con.SMTO_NORMAL, 5)
            win32gui.SendMessageTimeout(self.__data_grid_hwnd, win32con.WM_KEYUP, win32api.VkKeyScan('c'), 0, win32con.SMTO_NORMAL, 5)
        except Exception as e:
            pass
        win32api.keybd_event(win32con.VK_LCONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)

        # 另起进程处理输入验证码问题
        # todo 连个进程一个发 ctrl c，一个处理验证码
        p = Process(target=handle_verify, args=(self.__parent_trade, self.__hold_panel_hwnd, self.__data_grid_hwnd))
        p.start()
        p.join()
        # df = pd.read_clipboard(converters={'证券代码': str}).drop(
        #     columns=['冻结数量', '交易市场', '股东帐户', '汇率', '成本价港币', '成本价港币', '买入成本价港币', '买入在途数量', '卖出在途数量', 'Unnamed: 17', ])
        # 返回持仓数量大于 0 的股票
        # return df[df["股票余额"] > 0]
        # todo return pd.read_clipboard()
        return ''


class TradeApi:
    def __init__(self, trade_hwnd=None):
        self.trade_hwnd = trade_hwnd
        if trade_hwnd is None:
            self.__set_trade_hwnd()
        self.buy_panel = BuyPanel(self.trade_hwnd)
        self.sell_panel = SellPanel(self.trade_hwnd)
        self.hold_panel = HoldPanel(self.trade_hwnd)

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
        return self.hold_panel.get_hold()


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
                    and str(lot * 100) in confirm_info["info"]:
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
                if cls == "Static" and right - left == 300:
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
    from login import login

    hwnd = login()
    trade_api = TradeApi(trade_hwnd=hwnd)
    i = time.time()
    # for j in range(0, 5):
    # msg = trade_api.buy("600029", 7.00, 1)
    # print(msg)
    # time.sleep(0.5)
    # print(win32gui.GetWindowText(0x001612AC))
    # print(win32gui.GetClassName(0x001612AC))
    # msg = trade_api.sell("600029", 7.85, 1)
    # print(msg)
    df = trade_api.get_hold()
    print(df)

    print(time.time() - i)
