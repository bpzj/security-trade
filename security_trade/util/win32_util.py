import ctypes
from enum import Enum

import win32api
import win32con
import win32gui
import pywintypes
import win32print


def get_scale():
    h_dc = win32gui.GetDC(0)
    # 系统向显示器输出的分辨率
    width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
    # 显示器的分辨率
    HORZRES = win32print.GetDeviceCaps(h_dc, win32con.DESKTOPHORZRES)
    # 纵向分辨率
    # VERTRES = win32print.GetDeviceCaps(h_dc, win32con.DESKTOPVERTRES)

    return HORZRES / width


scale = get_scale()


class HwndType(Enum):
    #
    Edit = "Edit"
    Static = "Static"
    Button = "Button"
    ComboBox = "ComboBox"


class GuiPosition:
    # 父控件
    # ┏━━━━━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━━━━
    # ┃               y_space
    # ┃           ┏━━━━━━┷━━━━━━━┱┄┄┄┄┄┬┄
    # ┠┄ x_space ┄┨              ┃   y_height
    # ┃           ┠┄┄ x_length ┄┄┨     ┆
    # ┃           ┗━━━━━━━━━━━━━━┹┄┄┄┄┄┴┄
    # ┃             子控件
    # 这里是屏幕没有缩放时的大小
    def __init__(self, gui_type: HwndType, x_space: float, y_space: float, x_length: float, y_height: float):
        self.gui_type = gui_type
        self.x_space = x_space
        self.y_space = y_space
        self.x_length = x_length
        self.y_height = y_height


def pos_in_window_rect(pos_scale: GuiPosition, parent_rect, fit_rect_hwnd):
    left, top, right, bottom = win32gui.GetWindowRect(fit_rect_hwnd)
    left_real = parent_rect[0] + pos_scale.x_space
    right_real = left_real + pos_scale.x_length
    top_real = parent_rect[1] + pos_scale.y_space
    bottom_real = top_real + pos_scale.y_height

    # 调试: 打印出所需参数，使用 spy++ 找到定位到句柄，从打印出的参数里根据句柄值搜索
    # print('{:08X}'.format(fit_rect_hwnd))
    # print(win32gui.GetClassName(fit_rect_hwnd))
    # print(get_item_text(fit_rect_hwnd))
    # x_space = left - parent_rect[0]
    # y_space = top - parent_rect[1]
    # x_length = right - left
    # y_length = bottom - top
    # print(x_space, ',', y_space, ',', x_length, ',', y_length)

    if win32gui.GetClassName(fit_rect_hwnd) == pos_scale.gui_type.value:
        return left_real == left and right_real == right and top == top_real and bottom == bottom_real
    return False


def get_item_text(hwnd, max_len=4):
    while True:
        # 创建char[]
        buf = ctypes.create_string_buffer(max_len)
        # 获取内容
        if win32gui.SendMessage(hwnd, win32con.WM_GETTEXT, max_len // 2, buf) == 0:
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
