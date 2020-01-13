from PIL import Image
# 将一个图片转化为txt
from numpy import savetxt, asarray


def imgToArray():
    image = Image.open("1_2.png").convert("1").resize((32, 32))
    data = asarray(image)
    savetxt("1_2.txt", data, fmt="%d", delimiter='')

imgToArray()