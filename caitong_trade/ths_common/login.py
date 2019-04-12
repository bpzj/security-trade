import json
import os
import time
import win32api
import win32gui
import win32con


def find_login_win():
    hwnd_list = []
    win32gui.EnumWindows(lambda handle, param: param.append(handle), hwnd_list)
    for hwnd in hwnd_list:
        if win32gui.GetClassName(hwnd) == "#32770" and win32gui.GetParent(hwnd) and \
                win32gui.GetWindowText(win32gui.GetParent(hwnd)) == "网上股票交易系统5.0":
            return hwnd
    return None


def open_login_windows(exe_path=None):
        if find_login_win():
            return
        else:
            default_path = "D:\\Program Files (x86)\\CaiTongZhengQuan\\xiadan.exe"
            win32api.WinExec(exe_path or default_path, win32con.SW_SHOWNORMAL)
            time.sleep(6)


def __call_back(hwnd, extra):
    cls_name = win32gui.GetClassName(hwnd)
    if cls_name == "Edit" or cls_name == "Button" or cls_name == "Static":
        extra.append(hwnd)


def __get_useful_position(login_hwnd):
    pos_dic = {}
    left, top, right, bottom = win32gui.GetWindowRect(login_hwnd)
    horizontal = left + (right - left)*0.78
    vertical_1 = top + (bottom-top)*0.3511
    vertical_2 = top + (bottom-top)*0.4382
    vertical_3 = top + (bottom-top)*0.6292
    # 输入账号框的位置中心
    pos_dic.update(username_pos=(horizontal, vertical_1))
    # 输入交易密码的位置中心
    pos_dic.update(password_pos=(horizontal, vertical_2))
    # 登录按钮 的位置中心
    pos_dic.update(login_btn_pos=(horizontal, vertical_3))

    return pos_dic


def pos_in_window_rect(position, window_rect):
    if window_rect[0] < position[0] < window_rect[2] and window_rect[1] < position[1] < window_rect[3]:
        return True
    else:
        return False


def get_useful_handle(login_hwnd):
    child_list = []
    win32gui.EnumChildWindows(login_hwnd, lambda hwnd, param: param.append(hwnd), child_list)
    pos_dic = __get_useful_position(login_hwnd)
    handles = {}
    for child in child_list:
        window_rect = win32gui.GetWindowRect(child)
        if win32gui.GetClassName(child) == "Edit":
            if pos_in_window_rect(pos_dic["username_pos"], window_rect):
                handles.update(username_hwnd=child)
            elif pos_in_window_rect(pos_dic["password_pos"], window_rect):
                handles.update(password_hwnd=child)
        elif win32gui.GetClassName(child) == "Button":
            if pos_in_window_rect(pos_dic["login_btn_pos"], window_rect):
                handles.update(login_btn_hwnd=child)
    return handles


def login(username=None, password=None, config=None):
    if config is None:
        conf_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        with open(conf_path,  encoding='UTF-8') as f:
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
    login_hwnd = find_login_win()
    handles = get_useful_handle(login_hwnd)

    # 使用 windows 消息机制 登录
    win32gui.SendMessage(handles["username_hwnd"], win32con.WM_SETTEXT, None, username)
    win32gui.SendMessage(handles["password_hwnd"], win32con.WM_SETTEXT, None, password)
    win32gui.SendMessage(handles["login_btn_hwnd"], win32con.WM_LBUTTONDOWN, None, None)
    win32gui.SendMessage(handles["login_btn_hwnd"], win32con.WM_LBUTTONUP, None, None)
    time.sleep(6)


if __name__ == '__main__':
    login()

