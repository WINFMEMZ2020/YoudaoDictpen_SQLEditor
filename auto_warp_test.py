def auto_wrap(text, max_chars=10):
    wrapped_lines = []
    
    for line in text.split('\n'):
        current_line = ''
        char_count = 0
        
        for char in line:
            # 判断字符是否为全角字符
            if ord(char) > 12600:
                char_count += 2  # 全角字符算作两个字符宽度
            else:
                char_count += 1  # 半角字符算作一个字符宽度
            
            # 根据不同字符类型限制一行的字符数量
            if char_count <= max_chars:
                current_line += char
            else:
                wrapped_lines.append(current_line)
                current_line = char
                char_count = 1
        
        wrapped_lines.append(current_line)
    
    return '\n'.join(wrapped_lines)

# 输入的字符串
text = "【初音ミク】反转宇宙【ナユタン星人】1234567890123456789012345678901234567890123456789012345678901234567890.mp4"

# 使用微软雅黑字体显示文本
wrapped_text = auto_wrap(text)
print(wrapped_text)
