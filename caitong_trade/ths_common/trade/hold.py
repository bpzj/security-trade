import win32api
import win32con
import win32gui
import pandas as pd


class HoldPanel:
    def __init__(self, trade_hwnd):
        self.__parent_trade = trade_hwnd
        self.__handle = None
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
                self.available_cash = float(win32gui.GetWindowText(li[i+3]))
            elif win32gui.GetClassName(li[i]) == "CVirtualGridCtrl":
                self.__data_grid_hwnd = li[i]

    def get_hold(self):
        self.__init_handle()
        # ctrl c
        win32api.keybd_event(win32con.VK_LCONTROL, 0, 0, 0)
        win32gui.SendMessage(self.__data_grid_hwnd, win32con.WM_KEYDOWN, win32api.VkKeyScan('c'), 0)
        win32gui.PostMessage(self.__data_grid_hwnd, win32con.WM_KEYDOWN, win32api.VkKeyScan('c'), 0)
        win32api.keybd_event(win32con.VK_LCONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
        #  https://blog.csdn.net/SysProgram/article/details/45171493
        # win32gui.SendMessage(0x00020928, win32con.WM_KEYDOWN, win32api.VkKeyScan('c'), 0x001E0001)
        # win32gui.PostMessage(0x00020928, win32con.WM_KEYDOWN, win32api.VkKeyScan('c'), 0xC01E0001)
        pd.read_clipboard(converters={'证券代码': str})


if __name__ == '__main__':
    pass

