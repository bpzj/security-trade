import time
import win32gui
import win32con


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
        # 使用 windows 消息机制 登录
        win32gui.SendMessage(self.__edit_set["code"], win32con.WM_SETTEXT, None, stock_code)
        win32gui.SendMessage(self.__edit_set["price"], win32con.WM_SETTEXT, None, str(price))
        win32gui.SendMessage(self.__edit_set["lot"], win32con.WM_SETTEXT, None, str(lot*100))
        # win32gui.SendMessage(handles["login_btn_hwnd"], win32con.WM_LBUTTONDOWN, None, None)
        # win32gui.SendMessage(handles["login_btn_hwnd"], win32con.WM_LBUTTONUP, None, None)
        pass


class SellPanel:
    def __init__(self, dialog_hwnd):

        pass


if __name__ == '__main__':
    trade_api = TradeApi()
    trade_api.buy("000001", 12.12, 4)

