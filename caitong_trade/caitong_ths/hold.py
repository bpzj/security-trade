import time
import win32api
import win32con
import win32gui
from caitong_trade.util.win32_util import get_item_text
from caitong_trade.util.ocr_util import ocr_string_from_hwnd
from caitong_trade.util.win32_util import pos_in_window_rect


class HoldPanel:
    def __init__(self, trade_hwnd):
        self.__parent_trade = trade_hwnd
        self.__handle = None
        self.__hwnd_list = None
        # self.__edit_set = {}
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
        if self.__handle:
            son_of_hold = []
            win32gui.EnumChildWindows(self.__parent_trade, lambda handle, param: param.append(handle), son_of_hold)
            if self.__handle in son_of_hold:
                li = []
                win32gui.EnumChildWindows(self.__handle, lambda handle, param: param.append(handle), li)
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
                self.available_cash = float(win32gui.GetWindowText(li[i + 3]))
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
        # self.__init_handle()
        self.__get_hold()
        # return self.__get_order_msg()

    def __get_hold(self):
        # 将窗口调到前台，激活
        self.__init_handle()
        # ctrl c
        win32api.keybd_event(win32con.VK_LCONTROL, 0, 0, 0)
        win32gui.PostMessage(self.__data_grid_hwnd, win32con.WM_KEYDOWN, win32api.VkKeyScan('c'), 0)
        win32gui.SendMessage(self.__data_grid_hwnd, win32con.WM_KEYUP, win32api.VkKeyScan('c'), 0)
        win32api.keybd_event(win32con.VK_LCONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)

        self.__get_order_msg()

        # win32gui.ShowWindow(self.__parent_trade, win32con.SW_SHOWNORMAL)
        # win32gui.SetForegroundWindow(self.__parent_trade)
        # # 使用 windows 消息机制 登录
        # win32api.keybd_event(win32con.VK_LCONTROL, 0, 0, 0)
        # win32api.keybd_event(win32api.VkKeyScan('s'), 0, 0, 0)
        # win32api.keybd_event(win32api.VkKeyScan('s'), 0, win32con.KEYEVENTF_KEYUP, 0)
        # win32api.keybd_event(win32con.VK_LCONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
        # time.sleep(0.1)
        # hwnd = win32gui.FindWindow("#32770", "Save As")
        # win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
        # win32gui.SetForegroundWindow(hwnd)
        #
        # win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_MENU, 0)
        # win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, win32api.VkKeyScan('s'), 1 << 29)
        # time.sleep(0.05)
        # win32gui.PostMessage(hwnd, win32con.WM_KEYUP, win32api.VkKeyScan('s'), 0)
        # win32gui.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_MENU, 0)
        # win32api.keybd_event(win32con.VK_LCONTROL, 0, 0, 0)
        # win32api.keybd_event(win32api.VkKeyScan('s'), 0, 0, 0)
        # win32api.keybd_event(win32api.VkKeyScan('s'), 0, win32con.KEYEVENTF_KEYUP, 0)
        # win32api.keybd_event(win32con.VK_LCONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)

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
            return '检测到您正在拷贝数据' in text and "提示" in text and '确定' in text

        #
        # 1. 可以根据 验证码弹窗的 OWNER 句柄 = 父句柄 判断
        # 2. 可以根据 弹出窗口大小判断更快，所以按大小判断
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
                _left, _top, _right, _bottom = win32gui.GetWindowRect(prompt)
                input_pos = [_left + (_right - _left) * 0.3991, _top + (_bottom - _top) * 0.5504]
                image_pos = [_left + (_right - _left) * 0.6362, _top + (_bottom - _top) * 0.5504]

                win32gui.EnumChildWindows(prompt, lambda handle, param: param.append(handle), prompt_sons)
                for prompt_son in prompt_sons:
                    if win32gui.GetClassName(prompt_son) == 'Static' and pos_in_window_rect(image_pos, win32gui.GetWindowRect(prompt_son)):
                        prompt_info.update(image=prompt_son)
                    elif win32gui.GetClassName(prompt_son) == 'Edit' and pos_in_window_rect(input_pos, win32gui.GetWindowRect(prompt_son)):
                        prompt_info.update(input=prompt_son)
                    txt = win32gui.GetWindowText(prompt_son)
                    if txt == "":
                        txt = get_item_text(prompt_son)
                    elif txt == "确定":
                        prompt_info.update(confirm_btn=prompt_son)

                # 提示  弹出框, 使用ocr识别
                identify_code = ocr_string_from_hwnd(prompt_info["image"], expand=20)
                win32gui.SendMessage(prompt_info["input"], win32con.WM_SETTEXT, None, identify_code)
                win32api.PostMessage(prompt_info["confirm_btn"], win32con.WM_LBUTTONDOWN, None, None)
                win32api.PostMessage(prompt_info["confirm_btn"], win32con.WM_LBUTTONUP, None, None)


if __name__ == '__main__':
    hwnd = win32gui.FindWindow("#32770", "Save As")
    win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
    win32gui.SetForegroundWindow(hwnd)

    win32gui.PostMessage(hwnd, win32con.WM_SYSKEYDOWN, win32con.VK_MENU, 0x20380001)
    # win32gui.PostMessage(hwnd, win32con.WM_SYSKEYDOWN, win32api.VkKeyScan('s'), 1 << 29)
    win32gui.PostMessage(hwnd, win32con.WM_SYSKEYDOWN, win32api.VkKeyScan('s'), 0x20200001)
    win32gui.PostMessage(hwnd, win32con.WM_SYSCHAR, 0x76, 0x20200001)
    time.sleep(0.05)
    win32gui.PostMessage(hwnd, win32con.WM_SYSKEYUP, win32api.VkKeyScan('s'), 0xE0200001)
    win32gui.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_MENU, 0xC0380001)

    pass
