# 比如要裁剪第一个字符:
import json

from PIL import Image

# 转为灰度图像, 参数L，代表灰度
image = Image.open("screen.bmp").convert("L")

# cropped_image = image.crop((left, upper, right, lower))
cropped_image = image.crop((0, 0, 19, 23))

cropped_image.save("cropped_image.png")

pixel_matrix = cropped_image.load()

for col in range(0, cropped_image.height):
    for row in range(0, cropped_image.width):
        if pixel_matrix[row, col] != 0:
            pixel_matrix[row, col] = 255

image.save("thresholded_image.png")

characters = "0123456789"
captcha = ""

with open("bitmaps.json", "r") as f:
    bitmap = json.load(f)

char_matrix = cropped_image.load()
matches = {}

png6 = Image.open("6.png").convert("L")

for char in characters:
    match = 0
    black = 0
    bitmap_matrix = png6
    for col in range(0, cropped_image.height):
        for row in range(0, cropped_image.width):
            if pixel_matrix[row, col] != 0:
                pixel_matrix[row, col] = 255

# for i in range(int(image.width / 6), image.width+1, int(image.width/6) ):
#     char_img = image.crop()