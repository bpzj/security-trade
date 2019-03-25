import ctypes
import time
import win32api
import win32gui

import pywintypes
import win32con


def get_item_text(hwnd,max_len=4):
    while True:
        # 创建char[]
        buf=ctypes.create_string_buffer(max_len)
        # 获取内容
        if win32gui.SendMessage(hwnd,win32con.WM_GETTEXT,max_len//2,buf)==0:
            return None
        # 如果以0,0,0,0结尾，说明缓冲区够大
        if (buf.raw[-4],buf.raw[-3],buf.raw[-2],buf.raw[-1])==(0,0,0,0):
            # 转成utf-8
            text=pywintypes.UnicodeFromRaw(buf.raw)
            # 去掉末尾的0就能返回
            return text.strip('\00')
        # 否则把缓冲区扩大一倍重试
        else:
            max_len*=2


trade_hwnd = win32gui.FindWindow("Afx:400000:b:10003:6:1663155f", None)
win32gui.PostMessage(trade_hwnd, win32con.WM_KEYDOWN, win32con.VK_F1, 0)
win32gui.PostMessage(trade_hwnd, win32con.WM_KEYUP, win32con.VK_F1, 0)
if trade_hwnd <= 0:
    print(trade_hwnd)

print(trade_hwnd)
print(win32gui.GetWindowText(0x101184))
print(win32gui.GetClassName(0x101184))
print(get_item_text(0x101184))
