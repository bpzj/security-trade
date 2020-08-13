from PIL import Image
# 将一个图片转化为txt
from numpy import savetxt, asarray


def imgToArray():
    #
    wid = 40
    image = Image.open("screen.bmp").convert("1").resize( (int(62/23*wid), wid))
    # 100,100 是像素点的坐标
    src_strlist = image.load()
    for i in range(image.height-1):
        for j in range(image.width-1):
            data = src_strlist[j,i]
            if  data >= 150:
                print(0, end='')
            else:
                print(1, end='')
        print('')
    data = asarray(image)
    # # print(data)
    # savetxt("1_2.txt", data, fmt="%d", delimiter='')

imgToArray()