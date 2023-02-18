import time

import win32api
import win32con
import win32gui

from security_trade.util.ocr_util import ocr_string_from_hwnd
from security_trade.util.win32_util import GuiPosition, HwndType, pos_in_window_rect, get_item_text


def handle_verify(parent_trade_hwnd, hold_panel_hwnd, data_grid_hwnd):
    # TODO 解决获取不到验证码对话框的 hwnd句柄的问题
    def call_back(handle, dialog_l):
        dialog_l.append(handle) if win_is_verify_code(handle, parent_trade_hwnd) else None

    # todo
    """ 下单 时不论成功失败，肯定在最后有一个 提示 弹框 """
    while True:
        dialog_list = []  # 对话框的长度
        win32gui.EnumWindows(call_back, dialog_list)
        # 获得 每个 dialog 句柄的子句柄，判断出是 提示 弹出窗

        # 如果提示窗口过多,表示有错误;  如果没有提示信息窗口，等待弹出窗口
        if len(dialog_list) > 1:
            # todo 关闭所有，并重新发送 ctrl c
            exit(-1)
        if len(dialog_list) == 0:
            time.sleep(0.1)
            continue

        if len(dialog_list) == 1:
            dialog_hwnd, pic_hwnd, input_hwnd, button_hwnd = dialog_list[0], -1, -1, -1
            dialog_sons = []
            win32gui.EnumChildWindows(dialog_hwnd, lambda handle, param: param.append(handle), dialog_sons)
            dialog_rect = win32gui.GetWindowRect(dialog_hwnd)
            pic = GuiPosition(HwndType.Static, 186, 89, 81, 23)
            input_box = GuiPosition(HwndType.Edit,  93, 89, 87, 21)
            button = GuiPosition(HwndType.Button, 96, 149, 60, 24)
            for dialog in dialog_sons:
                if pos_in_window_rect(pic, dialog_rect, dialog):
                    pic_hwnd = dialog
                elif pos_in_window_rect(input_box, dialog_rect, dialog):
                    input_hwnd = dialog
                elif pos_in_window_rect(button, dialog_rect, dialog):
                    button_hwnd = dialog

            # todo 验证码弹框, 使用ocr识别
            identify_code = ocr_string_from_hwnd(pic_hwnd, expand=10)
            print(identify_code)
            win32gui.SendMessage(input_hwnd, win32con.WM_SETTEXT, None, identify_code)
            win32api.PostMessage(button_hwnd, win32con.WM_LBUTTONDOWN, None, None)
            win32api.PostMessage(button_hwnd, win32con.WM_LBUTTONUP, None, None)
            time.sleep(0.2)
        dialog_list = []  # 对话框的长度
        win32gui.EnumWindows(call_back, dialog_list)
        if len(dialog_list) == 0:
            return
        else:
            time.sleep(0.1)

        # 判断窗口是不是提示窗口，是，就返回true


def win_is_verify_code(hand, parent_trade_hwnd) -> bool:
    if win32gui.GetClassName(hand) != "#32770" or win32gui.GetWindow(hand, win32con.GW_OWNER) != parent_trade_hwnd:
        return False
    text = ""
    sons = []
    win32gui.EnumChildWindows(hand, lambda handle, param: param.append(handle), sons)
    for son in sons:
        if win32gui.GetClassName(son) in ["Static", "Button"]:
            t = get_item_text(son)
            if t:
                text = text + t
    return '检测到您正在拷贝数据' in text and "提示" in text and '确定' in text


if __name__ == '__main__':
    dialog_hwnd, pic_hwnd, input_hwnd, button_hwnd = 0x00050678 , -1, -1, -1
    dialog_sons = []
    win32gui.EnumChildWindows(dialog_hwnd, lambda handle, param: param.append(handle), dialog_sons)
    dialog_rect = win32gui.GetWindowRect(dialog_hwnd)
    pic = GuiPosition(HwndType.Static, 186, 89, 81, 23)
    input_box = GuiPosition(HwndType.Edit, 93, 89, 87, 21)
    button = GuiPosition(HwndType.Button, 96, 149, 60, 24)
    for dialog in dialog_sons:
        if pos_in_window_rect(input_box, dialog_rect, dialog):
            input_hwnd = dialog
    print(input_hwnd)
