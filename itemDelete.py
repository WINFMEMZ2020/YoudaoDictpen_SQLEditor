import PySimpleGUI as sg
import json
import os
import subprocess
import sqlite3
import time


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

def extract_data_from_database(db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    data_list = []
    cursor.execute("SELECT code, text FROM table_knowledge")
    rows = cursor.fetchall()
    for row in rows:
        data_dict = {"code": row[0], "text": row[1]}
        data_list.append(data_dict)
    conn.close()
    return data_list
    #ChatGPT帮大忙了

names = []
removed_names = []
lst = sg.Listbox(names, size=(100, 50), font=('Arial Bold', 14), expand_y=True, enable_events=True, key='-LIST-')
layout = [[sg.Text("以下是词典笔里的所有视频\n请选中需要删除的项目然后点击“删除”按钮\u3000\u3000\u3000\u3000",font=('Arial', 14)),
   sg.Button('移除'),
   sg.Button('保存')],
   [lst],
   [sg.Text("", key='-MSG-', font=('Arial Bold', 14), justification='center')]
]

def delete_items(items_name):
    # 打开数据库连接
    conn = sqlite3.connect(exerciseFavorite_name)
    cursor = conn.cursor()

    # 查找result列表，获取code值
    code_to_delete = None
    for item in result:
        if item["text"] == items_name:
            code_to_delete = item["code"]
            break

    if code_to_delete is not None:
        # 删除table_knowledge中匹配code值的项目
        cursor.execute("DELETE FROM table_knowledge WHERE code = ?", (code_to_delete,))
        # 提交数据库
        conn.commit()

        # 删除config_content中匹配knowledgeId与code值相符合的项目
        cursor.execute("DELETE FROM {} WHERE knowledgeId = ?".format(config_content["table_name"]), (code_to_delete,))
        # 提交数据库
        conn.commit()

    # 关闭数据库连接
    conn.close()

check_devices_okay()
current_time = time.localtime()
#生成exerciseFavorite.db的文件名称，方便出现问题及时回溯
exerciseFavorite_name = "exerciseFavorite_" + "{:02d}{:02d}{:02d}{:02d}{:02d}{:02d}".format(current_time.tm_year, current_time.tm_mon, current_time.tm_mday, current_time.tm_hour, current_time.tm_min, current_time.tm_sec) + ".db"
#生成并执行pull命令
exerciseFavorite_pull_command = "adb pull /userdisk/math/exerciseFav/exerciseFavorite.db " + exerciseFavorite_name
os.system(exerciseFavorite_pull_command) 
#数据库执行命令
result = extract_data_from_database(exerciseFavorite_name)

with open("config.json","r",encoding="UTF-8") as file_object:
    config_content = json.load(file_object)

window = sg.Window('Listbox Example', layout, size=(800, 600))
for item_dict in result:
    names.append(item_dict["text"])
window.finalize()

while True:
    event, values = window.read()
    print(event, values)
    if event == sg.WIN_CLOSED:
      break
    elif event == '移除':
        try:
            val = window['-LIST-'].get()[0]
            names.remove(val)
            removed_names.append(val)
            delete_items(val)
            window['-LIST-'].update(names)
        except IndexError:
            pass
    elif event == "保存":
        check_devices_okay()
        os.system("adb push " + exerciseFavorite_name +" /userdisk/math/exerciseFav/exerciseFavorite.db ")
        print("保存成功")

    # elif event == '撤销':
    #     if removed_names:
    #         last_removed_name = removed_names.pop()
    #         names.append(last_removed_name)
    #         window['-LIST-'].update(names)
