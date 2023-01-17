import time
from multiprocessing import Process

import pandas as pd
import win32api
import win32con
import win32gui
from security_trade.util.win32_util import get_item_text, GuiPosition, HwndType
from security_trade.util.ocr_util import ocr_string_from_hwnd
from security_trade.util.win32_util import pos_in_window_rect


class HoldPanel:
    def __init__(self, hold_panel, AfxMDIFrame_hwnd):
        self.__AfxMDIFrame_hwnd = AfxMDIFrame_hwnd
        self.__hold_panel_hwnd = hold_panel
        self.__hwnd_list = None
        # self.__edit_set = {}
        self.__data_grid_hwnd = None
        self.available_cash = None
        self.__set_useful_handle()
        # self.__init_handle()

    def __enter_hold_panel(self):
        """  向主句柄 发送 F4，调出 查询 - 资金股票 界面   """
        win32gui.PostMessage(self.__AfxMDIFrame_hwnd, win32con.WM_KEYDOWN, win32con.VK_F4, 0)
        win32gui.PostMessage(self.__AfxMDIFrame_hwnd, win32con.WM_KEYUP, win32con.VK_F4, 0)

    def __init_handle(self):
        # 发送 F4 , 调出界面
        self.__enter_hold_panel()
        """ 获取 持仓界面的 handle 值
            每点击几次 句柄都会重建，所以先校验 保存的handle 是否有效, 如果有效, 直接使用 保存的handle
        """
        if self.__hold_panel_hwnd:
            son = []
            win32gui.EnumChildWindows(self.__hold_panel_hwnd, lambda handle, param: param.append(win32gui.GetWindowText(handle)) if win32gui.GetWindowText(handle) else None, son)
            if '查询资金股票' in son and '资金余额' in son and '可用金额' in son:
                return

        # todo 如果重建了句柄，也就是上面的句柄失效了，重新根据 __AfxMDIFrame_hwnd 查找 句柄

        # self.__handle = hwnd_l[0]
        # txt = win32gui.GetWindowText(handle)
        # if txt and txt == "资金余额":
        #     hwnd_list.append(win32gui.GetParent(handle))
        #     return

        # 调用
        self.__set_useful_handle()

    def __set_useful_handle(self):
        """
        根据 持仓界面的 handle 获取 可用资金 数值， 持仓
        :return:
        """
        # 获得 根据子句柄
        li = []
        win32gui.EnumChildWindows(self.__hold_panel_hwnd, lambda handle, param: param.append(handle), li)
        for i in range(0, len(li)):
            if win32gui.GetWindowText(li[i]) == "可用金额":
                self.available_cash = float(win32gui.GetWindowText(li[i + 3]))
            elif win32gui.GetClassName(li[i]) == "CVirtualGridCtrl":
                self.__data_grid_hwnd = li[i]

    def get_hold(self):
        # 将窗口调到前台，激活
        self.__init_handle()
        # 另起进程处理输入验证码问题
        confirm_pro = Process(target=handle_verify, args=(self.__AfxMDIFrame_hwnd, self.__hold_panel_hwnd, self.__data_grid_hwnd))
        confirm_pro.start()
        # ctrl c
        win32api.keybd_event(win32con.VK_LCONTROL, 0, 0, 0)
        # 使用 PostMessage 导致客户端退出
        # win32con.HWND_BROADCAST, win32con.WM_SETTINGCHANGE, 0, 'Environment', win32con.SMTO_ABORTIFHUNG, 1000
        # SMTO_ABORTIFHUNG：如果接收进程处于“hung”状态，不等待超时周期结束就返回。
        # SMTO_BLOCK：阻止调用线程处理其他任何请求，直到函数返回。
        # SMTO_NORMAL：调用线程等待函数返回时，不被阻止处理其他请求。
        # SMTO_NOTIMEOUTIFNOTHUNG：Windows 95及更高版本：如果接收线程没被挂起，当超时周期结束时不返回。
        try:
            win32gui.SendMessageTimeout(self.__data_grid_hwnd, win32con.WM_KEYDOWN, win32api.VkKeyScan('c'), 0, win32con.SMTO_NORMAL, 5)
            win32gui.SendMessageTimeout(self.__data_grid_hwnd, win32con.WM_KEYUP, win32api.VkKeyScan('c'), 0, win32con.SMTO_NORMAL, 5)
        except Exception as e:
            pass
        win32api.keybd_event(win32con.VK_LCONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)

        # df = pd.read_clipboard(converters={'证券代码': str}).drop(
        #     columns=['冻结数量', '交易市场', '股东帐户', '汇率', '成本价港币', '成本价港币', '买入成本价港币', '买入在途数量', '卖出在途数量', 'Unnamed: 17', ])
        # 返回持仓数量大于 0 的股票
        # return df[df["股票余额"] > 0]
        # todo return pd.read_clipboard()
        return ''




if __name__ == '__main__':
    print(df)