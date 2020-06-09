# 图片二值化
from PIL import Image

# 模式 "L" 为灰度图像，每个像素用8个bit表示，0表示黑，255表示白，其他数字表示不同的灰度。
# 模式 "1" 为二值图像，每个像素用 8bit表示，0表示黑，255表示白 (没有其他值)。
img = Image.open('screen.bmp').convert(mode='L').resize((62*2, 23*2))

img.save("test1.jpg")
# 获得文字图片的每个像素点
src_strlist = img.load()

#  像素点的坐标如下图所示:
#  (0,0), (1,0), (2,0)
#  (0,1), (1,1)
#  (0,2)
#

for j in range(img.height-1):
    for i in range(img.width-1):
        data = src_strlist[i, j]
        if  data >= 150:
            print(0, end='')
        else:
            print(1, end='')
    print('')
pre_is_split = False
pre_split_x_value = []
num_length_total = 0
one_split_group = []
for i in range(img.width-1):
    total = 0
    for j in range(img.height-1):
        data = src_strlist[i, j]
        total = total + data
        # if  data >= 150:
        #     print(0, end='')
        # else:
        #     print(1, end='')
    if total >= 255 * (img.height - 1):
        print("|",end='')
        one_split_group.append(i)
        pre_is_split = True
    else:
        if pre_is_split:
            pre_split_x_value.append(sum(one_split_group)/len(one_split_group))
            one_split_group = []
            pre_is_split = False
        num_length_total = num_length_total +1
        print(" ",end='')
    # print(sum,end='')

print("每个数字平均长度为", num_length_total/4)
cursor = 0
real_split_x_value = []
for i in pre_split_x_value:
    if  i - cursor > num_length_total /4:
        real_split_x_value.append(int(i))
        cursor = i

print(real_split_x_value)


# 自定义灰度界限，大于这个值为黑色，小于这个值为白色
threshold = 160

table = []
for i in range(256):
    if i < threshold:
        table.append(0)
    else:
        table.append(1)

# 图片二值化
