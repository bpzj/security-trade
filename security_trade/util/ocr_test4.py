# 图片二值化
from PIL import Image

# 模式 "L" 为灰度图像，每个像素用8个bit表示，0表示黑，255表示白，其他数字表示不同的灰度。
# 模式 "1" 为二值图像，每个像素用 8bit表示，0表示黑，255表示白 (没有其他值)。
img = Image.open('screen.bmp').convert(mode='1').resize((62, 23))

img.save("test1.jpg")
# 获得文字图片的每个像素点
src_strlist = img.load()

#  像素点的坐标如下图所示:
#  (0,0), (1,0), (2,0)
#  (0,1), (1,1)
#  (0,2)
#

for j in range(img.height - 1):
    for i in range(img.width - 1):
        data = src_strlist[i, j]
        if data >= 150:
            print(0, end='')
        else:
            print(1, end='')
    print('')


def get_split_position(image: Image, content_num=4) -> list:
    pre_is_split = False
    pre_split_x_value = []
    content_length_total = 0
    one_split_group = []
    for i in range(image.width - 1):
        total = 0
        for j in range(image.height - 1):
            total = total + src_strlist[i, j]
        #  如果某一列的像素的灰度值基本都是白色, 就认为这一列没有内容, 作为分割线
        if total >= 255 * (image.height - 1):
            one_split_group.append(i)
            pre_is_split = True
        else:
            content_length_total = content_length_total + 1
            if pre_is_split:
                # 当前列像素有内容, 前面的像素列是分割符, 这时候, 说明前面的可以分到一组里
                pre_split_x_value.append(sum(one_split_group) / len(one_split_group))
                one_split_group = []
                pre_is_split = False

    print("每个数字平均长度为", content_length_total / content_num)
    cursor = 0
    real_split_x_value = []
    for split_pos in pre_split_x_value:
        #  分割中心位置 - 上一个分割中心位置 > 每个数字占据的平均长度
        if split_pos - cursor > content_length_total / content_num:
            real_split_x_value.append(int(split_pos))
            cursor = split_pos

    return real_split_x_value


cut_pos = get_split_position(img)
print()

img2 = img.crop((0,0,cut_pos[0],img.height))
img2.save("lena2.jpg")
from numpy import savetxt, asarray
data = asarray(img2)

# 自定义灰度界限，大于这个值为黑色，小于这个值为白色
threshold = 160

table = []
for i in range(256):
    if i < threshold:
        table.append(0)
    else:
        table.append(1)

# 图片二值化
