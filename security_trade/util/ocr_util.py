import os
import win32gui
import win32ui
import win32con
from aip import AipOcr
import json


def cap_img(hwnd=None, expand=0):
    # 获取句柄窗口的大小信息
    # 可以通过修改该位置实现自定义大小截图
    left, top, right, bot = win32gui.GetWindowRect(hwnd)
    w = right - left + expand
    h = bot - top

    # 返回句柄窗口的设备环境、覆盖整个窗口，包括非客户区，标题栏，菜单，边框
    hwndDC = win32gui.GetWindowDC(hwnd)
    # 创建设备描述表
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    # 创建内存设备描述表
    saveDC = mfcDC.CreateCompatibleDC()

    #
    # 创建位图对象
    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)
    saveDC.SelectObject(saveBitMap)

    #
    # 截图至内存设备描述表
    img_dc = mfcDC
    mem_dc = saveDC
    mem_dc.BitBlt((0, 0), (w, h), img_dc, (0, 0), win32con.SRCCOPY)
    # 将截图保存到文件中
    saveBitMap.SaveBitmapFile(mem_dc, 'screen.bmp')

    # 改变下行决定是否截图整个窗口，可以自己测试下
    # result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 1)
    # result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 0)
    # 获取位图信息
    # bmpinfo = saveBitMap.GetInfo()
    # bmpstr = saveBitMap.GetBitmapBits(True)
    # 生成图像
    # im = Image.frombuffer('RGB',
    #                       (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
    #                       bmpstr, 'raw', 'BGRX', 0, 1)
    # 存储截图
    # if result == 1:
    # PrintWindow Succeeded
    # im.save("test.png")

    #
    # 内存释放
    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwndDC)


class Singleton(object):
    _instance = None

    @staticmethod
    def get_instance():
        cls = __class__

        if cls._instance is None:
            cls._instance = super(cls, cls).__new__(cls)
        return cls._instance


conf_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
with open(conf_path) as f:
    config = json.load(f)
baidu_ocr = config["baidu-ocr-config"]
client = AipOcr(**baidu_ocr)


def img_to_str(image_path):
    with open(image_path, 'rb') as fp:
        image = fp.read()
    result = client.basicGeneral(image)

    if 'words_result' in result:
        return '\n'.join([w['words'] for w in result['words_result']])


def ocr_string_from_hwnd(hwnd, expand=0):
    cap_img(hwnd, expand)
    return img_to_str("screen.bmp")


if __name__ == '__main__':
    print(ocr_string_from_hwnd(0x002008D6))
