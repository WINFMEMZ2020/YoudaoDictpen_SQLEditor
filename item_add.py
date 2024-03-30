import sqlite3
import os
import hashlib
import shutil
import time
import json
import subprocess
import colorama
import sys
from PIL import Image, ImageDraw, ImageFont
import base64

####
# 读取config.json文件
with open('config.json', 'r') as f:
    config = json.load(f)

dictpen_password = config.get("dictpen_password","")
copy_video_to_dictpen_state = config.get("copy_video_to_dictpen","")
#####

def restart_program():
    python = sys.executable
    os.execl(python, python, *sys.argv)


#这是用以获取所有后缀是.mp4的文件的函数
def get_mp4_files(directory):
    mp4_files = []  
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".mp4"):
                file_path = os.path.join(root, file)  # 视频文件的绝对路径
                file_name = os.path.basename(file_path)
                mp4_files.append({"path": file_path, "name": file_name})
    return mp4_files



#用于登录adb的函数
def adb_login():
    try:
        proc = subprocess.Popen(["adb", "shell", "auth"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print("Error executing command:", e)
        return 5

    # 获取密码
    global dictpen_password
    password_input = dictpen_password + "\n"

    try:
        # 输入密码并设定超时时间为3秒
        command_output, error = proc.communicate(input=password_input.encode('utf-8'), timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
        print("Command execution timed out!\nWill restart in 1 seconds...")
        time.sleep(1)
        return 6

    print("command=", command_output, ", error=", error)

    if 'login with "adb shell auth" to continue.' in str(command_output) or 'login with "adb shell auth" to continue.' in str(error):
        return 0
    elif 'adb.exe: more than one device/emulator' in str(command_output) or 'adb.exe: more than one device/emulator' in str(error):
        return 1
    elif 'adb.exe: no devices/emulators found' in str(command_output) or 'adb.exe: no devices/emulators found' in str(error):
        return 2
    elif 'password incorrect!' in str(command_output) or 'password incorrect!' in str(error):
        try:
            # 输入新密码并设定超时时间为3秒
            command_output, error = proc.communicate(input=b"x3sbrY1d2@dictpen\n", timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            print("Command execution timed out!\nWill restart in 1 seconds...")
            time.sleep(1)
            
            return 6
        
        if 'password incorrect!' in str(command_output) or 'password incorrect!' in str(error):
            return 5
        else:
            return 3
    elif 'success.' in str(command_output) or 'success.' in str(error):
        return 4
    else:
        return 5
#用来确保adb连接OK的函数
def check_devices_okay():
    print("\n以下是已连接的设备:")
    os.system("adb devices")
    adb_login_state = adb_login()
    
    if adb_login_state == 0:
        print("您没有登录您的词典笔，请先登录。")
        os.system("adb shell auth")
        check_devices_okay()
    elif adb_login_state == 1:
        print("您有超过一台设备连接到了电脑上，请断开除词典笔外其它设备，然后按下Enter。")
        os.system("pause")
        check_devices_okay()
    elif adb_login_state == 2:
        print("您没有已连接的设备，请检查词典笔是否连接到电脑，词典笔是否启用adb，然后按下Enter。")
        os.system("pause")
        check_devices_okay()
    elif adb_login_state == 3:
        print("adb的密码不正确。您的词典笔可能不适合本脚本，请尝试使用另一版本的脚本。按下Enter退出此脚本。")
        os.system("pause")
    elif adb_login_state == 4:
        print("\n已成功连接到词典笔。请在脚本执行完成前不要连接其它设备，包括物理设备（手机、平板等）与虚拟设备（WSA或其它安卓虚拟机等），否则可能导致操作失败。")
        return True
    elif adb_login_state == 5:
        print("无法执行连接命令。您连接设备的可能不是词典笔。请检查您连接的设备，然后按下Enter。")
        os.system("pause")
        check_devices_okay()
    elif adb_login_state == 6:
        restart_program()



def auto_wrap(text, max_chars=40):
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

#用于编码图片的函数
def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_image

#用于生成图片的函数，用于显示在"答案"中
def create_image(text,picname):
    #自动换行
    text = auto_wrap(text)

    # 设置图片宽度、行间距、字间距和行距
    width, line_height, letter_spacing, line_spacing = 694, 5, 20, 20

    # 字体和字号
    font = ImageFont.truetype("msyh.ttc", 25)

    # 创建图片
    img = Image.new("RGB", (width, 1), "black")
    draw = ImageDraw.Draw(img)

    # 拆分文本为行
    lines = []
    for line in text.split("\n"):
        words = line.split()
        if not words:
            lines.append('')
        else:
            current_line = ' '.join(words)
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

    img.save(picname)




#加载各种路径等
json_file_path = 'config.json'
with open(json_file_path, 'r') as json_file:
    loaded_dict = json.load(json_file)

def check_and_correct_path(input_path):
    # 检查路径是否合法
    if input_path.endswith("//"):
        return input_path
    else:
        # 处理路径
        corrected_path = input_path.replace("/", "//")
        corrected_path = os.path.normpath(corrected_path)
        return corrected_path
    
table_name = loaded_dict['table_name']
directory_path = check_and_correct_path(loaded_dict['video_input_path'])
dictpen_video_path = loaded_dict['dictpen_video_path']

#用户确认开始操作
print("请确认您的参数正确无误。如果发现错误，请退出本程序并修改。\n如果没有错误，按下Enter开始执行脚本\n\ntable_name【表table_mathexercise的完整名称】：",table_name,"\nvideo_input_path【输入视频的文件夹路径】：",directory_path,"\ndictpen_video_path【词典笔存放视频的文件夹路径】：",dictpen_video_path)
if copy_video_to_dictpen_state == 1:
    print("已启用：同时将视频文件从电脑拷至词典笔")
    if "file:///userdisk/Music/" in dictpen_video_path:
        print("路径检查：路径合法。")
    else:
        print('路径检查：路径不合法，无法开始操作\n请检查"dictpen_video_path"路径后再尝试启动该脚本。\n原因：路径中必须包含"file:///userdisk/Music/"')
        os.system("pause")
        exit()
else:
    print("已禁用：同时将视频文件从电脑拷至词典笔")
os.system("pause")

#检查设备是否处于OK状态
check_devices_okay()
current_time = time.localtime()
#生成exerciseFavorite.db的文件名称，方便出现问题及时回溯
exerciseFavorite_name = "exerciseFavorite_" + "{:02d}{:02d}{:02d}{:02d}{:02d}{:02d}".format(current_time.tm_year, current_time.tm_mon, current_time.tm_mday, current_time.tm_hour, current_time.tm_min, current_time.tm_sec) + ".db"
#生成并执行pull命令
exerciseFavorite_pull_command = "adb pull /userdisk/math/exerciseFav/exerciseFavorite.db " + exerciseFavorite_name
os.system(exerciseFavorite_pull_command) 
print("已成功导出exerciseFavorite.db")

#连接到数据库
conn = sqlite3.connect(exerciseFavorite_name)
cursor = conn.cursor()

#获取所有code，将结果存储到列表中
column_name = 'code'
cursor.execute(f"SELECT {column_name} FROM {table_name}")
results = cursor.fetchall()
table_math_all_code = [row[0] for row in results]

#获取所有knowledgeId，将结果存储到列表中
column_name = 'knowledgeId'
cursor.execute(f"SELECT {column_name} FROM {table_name}")
results = cursor.fetchall()
table_math_all_knowledgeId = [row[0] for row in results]
table_math_all_knowledgeId = list(filter(None, table_math_all_knowledgeId))

#准备knowledgeId，方法为获取最大的knowledgeId，并每个新项目在此基础上+1
int_table_math_all_knowledgeId = []
for tmp in table_math_all_knowledgeId:
    int_table_math_all_knowledgeId.append(int(tmp))
try:
    max_knowledgeId = max(int_table_math_all_knowledgeId)
except ValueError:
    max_knowledgeId = 0
temp_knowledgeId = str(max_knowledgeId)

#记录运行时的时间戳
now_timestamp = int(time.time() * 1000)

# 获取目录下所有的 .mp4 文件
files_list = get_mp4_files(directory_path)

for file_dict in files_list:
    print(file_dict["path"])

    #意义不明的计算MD5，作为文件名与code的值
    with open(file_dict["path"], 'rb') as f:
        md5 = hashlib.md5(f.read()).hexdigest()
        name = (file_dict["name"])


    #生成knowledgeId
    temp_knowledgeId = str(int(temp_knowledgeId) + 1)
    final_knowledgeID = str(int(temp_knowledgeId) + 1)
 
    #由于实时获取timestamp会导致timestamp重复，反正不重要，就让其+1000ms就好了
    now_timestamp = now_timestamp + 1000

    #生成显示在答案的图片
    ans_content = "视频名称:" + name + "\n视频文件md5值:" + md5 + "\ntimestamp:" + str(now_timestamp)
    create_image(ans_content,md5 + ".jpg")
    base64_text = image_to_base64(md5 + ".jpg")

    os.remove(md5 + ".jpg")

    new_data = (md5,"2",md5,"2",
                base64_text,None,None,"2",base64_text,
                "1",None,None,None,'{"knowId":1164,"knowName":"求比值的方法","knowVideo":"'+ dictpen_video_path + name + '"}',
                None,None,final_knowledgeID,None,
                "[]","dictpen","0","1","1",str(now_timestamp)
                )
    try:
        cursor.execute("INSERT INTO " + table_name + " (code, type, text, ques_body_type, ques_body_content, pattern_type, pattern_content, answer_type, answer_content, analysis_type, analysis_content, scan_image_url, scan_image_local, knowledge, explain_video, point_video, knowledgeId, simQuesList, label, source, newContent, item_state, sync_state, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", new_data)
    except sqlite3.IntegrityError:
        continue 
    #现在table_math的处理完了，接下来去处理table_knowledge
    (final_name_show,extension) = os.path.splitext(os.path.basename(file_dict["path"])) #不考虑运行效率的情况，去掉后缀获取文件名

    knowledge_parents = '[{"knowId": 1164,"knowName": "求比值的方法","knowVideo": "' + dictpen_video_path +  md5 + ".mp4" + '"}]'
    new_knowledge_data = (final_knowledgeID,final_name_show,dictpen_video_path +  md5 + ".mp4",knowledge_parents,"[]","[]","1",now_timestamp)

    cursor.execute("INSERT INTO table_knowledge (code, text, video, parents, children, simQuesList, sync_state, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", new_knowledge_data)

    #拷贝视频文件
    if copy_video_to_dictpen_state == 1:
        video_path = dictpen_video_path.replace("file://", "")
        adb_command = "adb push " + '"' + file_dict["path"] + '" "' + video_path + md5 + ".mp4" + '"'
        os.system(adb_command)

#提交并关闭数据库
conn.commit()
conn.close()

if copy_video_to_dictpen_state == 0:
    print("已完成对数据库的添加。\n请将" + directory_path + "内的视频文件传至词典笔的" + dictpen_video_path + "目录下，\n完成后，按下Enter来将数据库传回词典笔内。\n")
    os.system("pause")
#确保adb连接可用
check_devices_okay()
os.system("adb push " + exerciseFavorite_name +" /userdisk/math/exerciseFav/exerciseFavorite.db ")
print("处理完成!")
os.system("pause")