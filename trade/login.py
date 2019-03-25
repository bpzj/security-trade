import json
import time
import win32api
import win32gui

import win32con
from util import ocr_string_from_hwnd


def open_login_win(exe_path=None):
    login_hwnd = win32gui.FindWindow("#32770", "用户登录")
    if login_hwnd <= 0:
        if exe_path is None:
            win32api.WinExec("D:\\Program Files (x86)\\CaiTongZhengQuan\\xiadan.exe", win32con.SW_SHOWNORMAL)
        else:
            win32api.WinExec(exe_path, win32con.SW_SHOWNORMAL)
        time.sleep(8)


def call_back(hwnd, extra):
    cls_name = win32gui.GetClassName(hwnd)
    if cls_name == "Edit" or cls_name == "Button" or cls_name == "Static":
        extra.append(hwnd)


def get_useful_position(login_hwnd):
    pos_dic = {}
    left, top, right, bottom = win32gui.GetWindowRect(login_hwnd)
    horizontal_1 = left + (right - left)*0.7
    vertical_1 = top + (bottom-top)*0.41
    space_1 = (bottom-top)*0.1166
    # 输入账号框的位置中心
    pos_dic.update(username_pos=(horizontal_1, vertical_1))
    # 输入交易密码的位置中心
    pos_dic.update(password_pos=(horizontal_1, vertical_1 + space_1))
    # 输入验证码的位置中心
    pos_dic.update(identify_pos=(horizontal_1, vertical_1 + space_1*2))
    # 验证码图片 的位置中心
    horizontal_2 = left + (right - left)*0.8973
    pos_dic.update(identify_img=(horizontal_2, vertical_1 + space_1 * 2))

    # 选择登录模式的位置中心
    pos_dic.update(mode_pos=(horizontal_1, vertical_1 + space_1*3))
    # 登录按钮 的位置中心
    space_2 = (bottom-top)*0.9028
    pos_dic.update(login_btn_pos=(horizontal_1, top + space_2))

    return pos_dic


def pos_in_window_rect(position, window_rect):
    if window_rect[0] < position[0] < window_rect[2] and window_rect[1] < position[1] < window_rect[3]:
        return True
    else:
        return False


def get_useful_handle(login_hwnd):
    child_list = []
    win32gui.EnumChildWindows(login_hwnd, lambda hwnd, param: param.append(hwnd), child_list)
    pos_dic = get_useful_position(login_hwnd)
    handles = {}
    for child in child_list:
        window_rect = win32gui.GetWindowRect(child)
        if win32gui.GetClassName(child) == "Edit":
            if pos_in_window_rect(pos_dic["username_pos"], window_rect):
                handles.update(username_hwnd=child)
            elif pos_in_window_rect(pos_dic["password_pos"], window_rect):
                handles.update(password_hwnd=child)
            elif pos_in_window_rect(pos_dic["identify_pos"], window_rect):
                handles.update(identify_hwnd=child)
        elif win32gui.GetClassName(child) == "ComboBox":
            if pos_in_window_rect(pos_dic["mode_pos"], window_rect):
                handles.update(mode_hwnd=child)
        elif win32gui.GetClassName(child) == "Static":
            if pos_in_window_rect(pos_dic["identify_img"], window_rect):
                handles.update(identify_img_hwnd=child)
        elif win32gui.GetClassName(child) == "Button":
            if pos_in_window_rect(pos_dic["login_btn_pos"], window_rect):
                handles.update(login_btn_hwnd=child)
    return handles


def login(username=None, password=None):
    if username is None or password is None:
        with open('config.json') as f:
            data = json.load(f)
        account = data["account"]
        if account is None:
            exit()
        else:
            username = account["username"]
            password = account["password"]
    login_hwnd = win32gui.FindWindow("#32770", "用户登录")
    handles = get_useful_handle(login_hwnd)
    win32gui.SendMessage(handles["username_hwnd"], win32con.WM_SETTEXT, None, username)
    win32gui.SendMessage(handles["password_hwnd"], win32con.WM_SETTEXT, None, password)
    identify_code = ocr_string_from_hwnd(handles["identify_img_hwnd"])
    win32gui.SendMessage(handles["identify_hwnd"], win32con.WM_SETTEXT, None, identify_code)
    win32gui.SendMessage(handles["login_btn_hwnd"], win32con.WM_LBUTTONDOWN, None, None)
    win32gui.SendMessage(handles["login_btn_hwnd"], win32con.WM_LBUTTONUP, None, None)


if __name__ == '__main__':
    open_login_win()
    login()

