import time
import win32api
import win32con
import win32gui
import sys
sys.path.append("..")
from win32_util import get_item_text


class HoldPanel:
    def __init__(self, trade_hwnd):
        self.__parent_trade = trade_hwnd
        self.__handle = None
        self.__hwnd_list = None
        self.__edit_set = {}

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

        # 获取所有 dialog 子句柄
        def call_back(handle, hwnd_list):
            if win32gui.GetClassName(handle) == "CVirtualGridCtrl" and win32gui.GetWindowText(hwnd) == "Custom1" :
                hwnd_list.append(handle)
        hwnd_l = []
        win32gui.EnumChildWindows(self.__parent_trade, call_back, hwnd_l)
        print(hwnd_l)
        for hwnd in hwnd_l:
            print(win32gui.GetWindowText(hwnd))
            print(win32gui.GetWindowRect(hwnd))
            print(hwnd)
            pass
            # 获得 每个 dialog 句柄的子句柄，根据子句柄的内容判断出 dialog 是在 买入界面 或者 卖出界面
            # li = []
            # win32gui.EnumChildWindows(hwnd, lambda handle, param: param.append(handle), li)
            # for l in li:
            #     if win32gui.GetWindowText(l) == "买入股票":
            #         self.__handle = hwnd
            #         self.__hwnd_list = li
            #         break
        # 更新 证券代码，买入价格，买入数量，买入按钮 四个有用的句柄

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

    def get_hold(self):
        self.__init_handle()
        self.__get_hold()
        # return self.__get_order_msg()

    def __get_hold(self):
        # ctrl c
        win32api.keybd_event(win32con.VK_LCONTROL, 0, 0, 0)
        win32gui.SendMessage(0x00020928, win32con.WM_KEYDOWN, win32api.VkKeyScan('c'), 0)
        win32gui.PostMessage(0x00020928, win32con.WM_KEYDOWN, win32api.VkKeyScan('c'), 0)
        win32api.keybd_event(win32con.VK_LCONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
        #  https://blog.csdn.net/SysProgram/article/details/45171493
        # win32gui.SendMessage(0x00020928, win32con.WM_KEYDOWN, win32api.VkKeyScan('c'), 0x001E0001)
        # win32gui.PostMessage(0x00020928, win32con.WM_KEYDOWN, win32api.VkKeyScan('c'), 0xC01E0001)


if __name__ == '__main__':
    pass

