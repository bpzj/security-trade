import ctypes
import time
import win32api
import win32con
import win32gui
import pywintypes


def get_trade_hwnd():
    hwnd_list = []
    win32gui.EnumWindows(lambda handle, param: param.append(handle), hwnd_list)
    for hwnd in hwnd_list:
        if win32gui.GetWindowText(hwnd) == "网上股票交易系统5.0" and "Afx:400000" in win32gui.GetClassName(hwnd):
            return hwnd
    print("未找到交易页面")


def enter_buy_panel(trade_handle):
    win32gui.PostMessage(trade_handle, win32con.WM_KEYDOWN, win32con.VK_F1, 0)
    win32gui.PostMessage(trade_handle, win32con.WM_KEYUP, win32con.VK_F1, 0)


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


def buy(stock_code, lot_num):
    trade_hwnd = get_trade_hwnd()
    enter_buy_panel(trade_hwnd)


# print(win32gui.GetWindowText(0x101184))
# print(win32gui.GetClassName(0x101184))
# print(get_item_text(0x101184))
# print(get_item_text(0x1F1632))
# print(get_item_text(0xA063E))


if __name__ == '__main__':
    buy("000001", 2)
