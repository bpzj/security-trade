import win32api
import win32con
import win32gui
import win32print
from util.win32_util import scale, pos_in_window_rect, GuiPosition, HwndType

trade_hwnd = win32gui.FindWindow('Afx:400000:b:10003:6:16d80cbf', '网上股票交易系统5.0')

li = []
win32gui.EnumWindows(lambda h, p: p.append(h) if win32gui.GetClassName(h) == '#32770' and win32gui.GetParent(h) == trade_hwnd else None, li)

child_list = []
win32gui.EnumChildWindows(win32gui.FindWindow("#32770", "用户登录"), lambda hwnd, param: param.append(hwnd), child_list)

username_hwnd = child_list[1]
password_hwnd = child_list[2]
comm_password_hwnd = child_list[4]
login_btn_hwnd = child_list[24]

# (1321, 420)-(1492, 443) 171x23     137, 18

print(scale)
