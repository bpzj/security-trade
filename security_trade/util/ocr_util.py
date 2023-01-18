import os
import win32gui
import win32ui
import win32con
import json
import requests
import base64

# 保证兼容python2以及python3
from urllib.request import urlopen
from urllib.request import Request
from urllib.error import URLError
from urllib.parse import urlencode

import ssl

from cnocr import CnOcr


def fetch_token():
    """获取token"""
    # 防止https证书校验不正确
    ssl._create_default_https_context = ssl._create_unverified_context
    API_KEY = 'y1IYSpwIdNjHoiYHOAcp93QX'
    SECRET_KEY = 'TneWvhXl92p95zndwpBa872RXalZuBZk'
    OCR_URL = "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic"
    TOKEN_URL = 'https://aip.baidubce.com/oauth/2.0/token'
    params = {'grant_type': 'client_credentials', 'client_id': API_KEY, 'client_secret': SECRET_KEY}
    post_data = urlencode(params)
    post_data = post_data.encode('utf-8')
    req = Request(TOKEN_URL, post_data)
    try:
        f = urlopen(req, timeout=5)
        result_str = f.read()
    except URLError as err:
        print(err)
    result_str = result_str.decode()

    result = json.loads(result_str)

    if ('access_token' in result.keys() and 'scope' in result.keys()):
        if not 'brain_all_scope' in result['scope'].split(' '):
            print('please ensure has check the  ability')
            exit()
        return result['access_token']
    else:
        print('please overwrite the correct API_KEY and SECRET_KEY')
        exit()


def cap_img(hwnd=None, expand=0):
    # 获取句柄窗口的大小信息
    # 可以通过修改该位置实现自定义大小截图
    left, top, right, bot = win32gui.GetWindowRect(hwnd)
    w = right - left + expand + 10
    h = bot - top + expand + 5

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


conf_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")


# client_id 为官网获取的AK， client_secret 为官网获取的SK
# 百度ocr 数字识别  https://cloud.baidu.com/doc/OCR/s/Ok3h7y1vo

# 二进制方式打开图片文件


def img_to_str(image_path):
    f = open(image_path, 'rb')
    img = base64.b64encode(f.read())
    f.close()

    request_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/numbers"
    params = {"image": img}
    access_token = fetch_token()
    request_url = request_url + "?access_token=" + access_token
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    response = requests.post(request_url, data=params, headers=headers)
    if response:
        print(response.json())
        return '\n'.join([w['words'] for w in response.json()['words_result']])


def img_to_str_local(image_path):
    ocr = CnOcr(rec_model_name='densenet_lite_136-fc', det_model_name='naive_det', cand_alphabet='0123456789')
    out = ocr.ocr(image_path)
    if len(out) == 1:
        return out[0].get('text')


def ocr_string_from_hwnd(hwnd, expand=0):
    cap_img(hwnd, expand)
    return img_to_str_local("screen.bmp")


if __name__ == '__main__':
    cap_img(0x00070CA8, 0)
    # print(img_to_str('C:\\Users\\Administrator\\Desktop\\code\\security-trade\\security_trade\\screen.bmp'))
    # print(ocr_string_from_hwnd(0x002008D6))
