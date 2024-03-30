from PIL import Image, ImageDraw, ImageFont

# 设置图片宽度、行间距、字间距和行距
width, line_height, letter_spacing, line_spacing = 800, 5, 20, 20

# 字符串内容
text = "123\n456666666666666666661111111111111111111111111111111111111111111111111111111111111111111111111111111111111\n479\n123"

# 字体和字号
font = ImageFont.truetype("msyh.ttc", 25)

# 创建图片
img = Image.new("RGB", (width, 1), "black")
draw = ImageDraw.Draw(img)

# 拆分文本为行（自动换行）
lines = []
for line in text.split("\n"):
    words = line.split()
    if not words:
        lines.append('')
    else:
        current_line = words.pop(0)
        for word in words:
            test_line = current_line + ' ' + word
            if draw.textbbox((0, 0), test_line, font=font, align='left')[2] <= width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)

# 计算图片高度
total_height = sum(draw.textbbox((0, 0), line, font=font, align='left')[3] - draw.textbbox((0, 0), line, font=font, align='left')[1] + line_height + line_spacing for line in lines)

# 增加额外高度
total_height += 20

# 调整图片高度
img = Image.new("RGB", (width, total_height), "black")
draw = ImageDraw.Draw(img)

# 绘制文本
y = 10  # 调整起始位置
for line in lines:
    bbox = draw.textbbox((0, 0), line, font=font, align='left')
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    # 绘制文本（左对齐）
    x = 0
    draw.text((x, y), line, font=font, fill="white")
    
    y += h + line_height + line_spacing

img.save("generated_image.png")
