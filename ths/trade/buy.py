import time
import win32api
import win32con
import win32gui

from win32_util import get_item_text


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
                # print(handle)
                # if (_right - _left == 362) or (_right - _left == 341):
                #     print(handle)
                #     dialog_l.append(handle)
                if win_is_msg(handle):
                    print(handle)
                    dialog_l.append(handle)

        # todo
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

