import tkinter as tk
import json
from tkinter import filedialog
import subprocess
import os
import time
import sqlite3

def browse_folder(entry):
    folder_path = filedialog.askdirectory()
    folder_path = folder_path.replace("/", "//")
    folder_path = folder_path + r"//"
    if folder_path:
        entry.delete(0, tk.END)
        entry.insert(0, folder_path)

#用于登录adb的函数
def adb_login():
    proc = subprocess.Popen("adb shell auth", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    command_output, error = proc.communicate(input=b"CherryYoudao\n")
    print("command=",command_output,",error=",error)
    if 'login with "adb shell auth" to continue.' in str(command_output) or 'login with "adb shell auth" to continue.' in str(error):
        return 0
    elif 'adb.exe: more than one device/emulator' in str(command_output) or 'adb.exe: more than one device/emulator' in str(error):
        return 1
    elif 'adb.exe: no devices/emulators found' in str(command_output) or 'adb.exe: no devices/emulators found' in str(error):
        return 2
    elif 'password incorrect!' in str(command_output) or 'password incorrect!' in str(error):
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

def custom_action():
    #检查设备是否处于OK状态
    check_devices_okay()
    current_time = time.localtime()
    #生成exerciseFavorite.db的文件名称，方便出现问题及时回溯
    exerciseFavorite_name = "exerciseFavorite_" + "{:02d}{:02d}{:02d}{:02d}{:02d}{:02d}".format(current_time.tm_year, current_time.tm_mon, current_time.tm_mday, current_time.tm_hour, current_time.tm_min, current_time.tm_sec) + ".db"
    #生成并执行pull命令
    exerciseFavorite_pull_command = "adb pull /userdisk/math/exerciseFav/exerciseFavorite.db " + exerciseFavorite_name
    os.system(exerciseFavorite_pull_command) 

    conn = sqlite3.connect(exerciseFavorite_name)
    cursor = conn.cursor()

    # 获取数据库中所有表的名称
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    # 遍历所有表，找到以 'table_mathexercise_urs' 开头的表
    for table in tables:
        if table[0].startswith('table_mathexercise_urs'):
            table_name = table[0]
            break

    # 关闭连接
    cursor.close()
    conn.close()

    values[0].delete(0, tk.END)  # 清空第一个输入框的内容
    values[0].insert(0, table_name)  # 将"123"填入第一个输入框



def save_config():
    new_data = {key: value.get() for key, value in zip(data.keys(), values)}
    with open('config.json', 'w') as f:
        json.dump(new_data, f, indent=4)
    print("配置文件成功修改，请等待脚本加载")
    os.system('start cmd /c "py main.py"')

def help_choose_path():
    new_window = tk.Toplevel(root)
    # 设置窗口的标题和大小
    new_window.title("帮助")
    new_window.geometry("200x100")


root = tk.Tk()
root.title("JSON Config Editor")

# Load config data from config.json
with open('config.json', 'r') as f:
    data = json.load(f)

values = []

# Add a label at the top
tk.Label(root, text="请修改您需要的参数，然后点击“确定并启动”按钮来启动脚本\n默认情况下，不建议随便更改陌生的数值。", font=("Helvetica", 10)).grid(row=0, column=0, columnspan=2)

for i, (key, val) in enumerate(data.items()):
    tk.Label(root, text=key).grid(row=i+1, column=0)
    
    values.append(tk.Entry(root, width=100)) 
    values[-1].insert(0, val)
    values[-1].grid(row=i+1, column=1)
    
    if i == 0:
        browse_button = tk.Button(root, text="填充", command=custom_action)
    elif i == 3:
         browse_button = tk.Button(root, text="帮助", command=help_choose_path)
    else:
        browse_button = tk.Button(root, text="浏览", command=lambda entry=values[i]: browse_folder(entry))

    browse_button.grid(row=i+1, column=2)

# browse_button.grid_remove()

tk.Button(root, text="确定", command=save_config).grid(row=len(data)+1, column=0, columnspan=3)

root.mainloop()
