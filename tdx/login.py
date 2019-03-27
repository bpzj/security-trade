import json
import os
import time
import win32api
import win32gui
import win32con
from ocr_util import ocr_string_from_hwnd


def open_login_windows(exe_path=None):
    login_hwnd = win32gui.FindWindow("#32770", "财通证券财路通V6.49")
    if login_hwnd <= 0:
        if exe_path is None:
            win32api.WinExec("D:\\Program Files (x86)\\CaiTong-TongDaXin\\TdxW.exe", win32con.SW_SHOWNORMAL)
        else:
            win32api.WinExec(exe_path, win32con.SW_SHOWNORMAL)
        time.sleep(8)


def __call_back(hwnd, extra):
    cls_name = win32gui.GetClassName(hwnd)
    if cls_name == "Edit" or cls_name == "Button" or cls_name == "Static":
        extra.append(hwnd)


def __get_useful_position(login_hwnd):
    pos_dic = {}
    left, top, right, bottom = win32gui.GetWindowRect(login_hwnd)
    horizontal = right - left
    vertical = bottom-top
    # 登录模式: 独立交易 按钮
    pos_dic.update(only_trade_pos=(horizontal*0.7953 + left, vertical*0.219 + top))
    # 输入账号框的位置中心
    pos_dic.update(username_pos=(horizontal*0.5 + left, vertical*0.4353 + top))
    # 输入交易密码的位置中心
    pos_dic.update(password_pos=(horizontal*0.5 + left, vertical*0.5198 + top))
    # 输入验证码的位置中心
    pos_dic.update(identify_pos=(horizontal*0.6174 + left, vertical*0.628 + top))
    # 登录按钮 的位置中心
    pos_dic.update(login_btn_pos=(horizontal*0.3137 + left, vertical*0.7282 + top))

    return pos_dic


def pos_in_window_rect(position, window_rect):
    if window_rect[0] < position[0] < window_rect[2] and window_rect[1] < position[1] < window_rect[3]:
        return True
    else:
        return False


def get_useful_handle(login_hwnd):
    pos_dic = __get_useful_position(login_hwnd)

    def __get_useful_handle(handle, handle_dic):
        window_rect = win32gui.GetWindowRect(handle)
        if win32gui.GetClassName(handle) == "AfxWnd42":
            if pos_in_window_rect(pos_dic["login_btn_pos"], window_rect):
                handle_dic.update(login_btn_hwnd=handle)
            elif pos_in_window_rect(pos_dic["only_trade_pos"], window_rect):
                handle_dic.update(only_trade_hwnd=handle)
        elif win32gui.GetClassName(handle) == "Edit" and pos_in_window_rect(pos_dic["username_pos"], window_rect):
            handle_dic.update(username_hwnd=handle)
        elif win32gui.GetClassName(handle) == "SafeEdit":
            if pos_in_window_rect(pos_dic["password_pos"], window_rect):
                handle_dic.update(password_hwnd=handle)
            elif pos_in_window_rect(pos_dic["identify_pos"], window_rect):
                handle_dic.update(identify_hwnd=handle)
    useful_handles = {}
    win32gui.EnumChildWindows(login_hwnd, __get_useful_handle, useful_handles)

    return useful_handles


def login(username=None, password=None, config=None):
    if config is None:
        conf_path = os.path.join(os.path.dirname(__file__), "config.json")
        with open(conf_path) as f:
            config = json.load(f)
    account = config["account"]
    exe_path = config["exe_path"]

    # 打开登录窗口
    open_login_windows(exe_path)

    if username is None or password is None:
        if account is None:
            exit()
        else:
            username = account["username"]
            password = account["password"]

    # 找到各个句柄
    login_hwnd = win32gui.FindWindow("#32770", "财通证券财路通V6.49")
    handles = get_useful_handle(login_hwnd)

    # 使用 windows 消息机制 登录

    win32gui.SendMessage(handles["username_hwnd"], win32con.WM_SETTEXT, None, username)
    for i in range(0, 10):
        win32api.PostMessage(handles["password_hwnd"], win32con.WM_CHAR, win32con.VK_BACK, 0)
    for char in list(password):
        win32api.PostMessage(handles["password_hwnd"], win32con.WM_CHAR, ord(char), 0)
    # win32gui.SendMessage(handles["password_hwnd"], win32con.WM_SETTEXT, None, password)
    identify_code = ocr_string_from_hwnd(login_hwnd)
    # win32gui.SendMessage(handles["identify_hwnd"], win32con.WM_SETTEXT, None, identify_code)
    for char in list(identify_code):
        win32api.PostMessage(handles["identify_hwnd"], win32con.WM_CHAR, ord(char), 0)
    time.sleep(0.5)

    win32api.PostMessage(login_hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, None)
    win32api.PostMessage(login_hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, None)
    time.sleep(5)


if __name__ == '__main__':
    login()

