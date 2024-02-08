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


def initialize():
    # 读取config.json文件
    with open('config.json', 'r') as f:
        config = json.load(f)

    table_name = config.get("table_name","")
    video_input_path = config.get('video_input_path', '')
    video_output_path = config.get("video_output_path","")
    dictpen_video_path = config.get("dictpen_video_path","")

    layout = [
        [sg.Text("请修改您需要的参数，然后点击“确定并启动”按钮来启动脚本\n默认情况下，不建议随便更改陌生的数值。", font={'family': 'SimHei', 'size': 20, 'weight': 'bold'})],
        [sg.Text("table_name【表table_mathexercise的完整名称】："),sg.In(key='table_name_input', default_text=table_name), sg.Button("自动填充")],
        [sg.Text("video_input_path【输入视频的文件夹路径】："),sg.In(key='video_input_path_input', default_text=video_input_path), sg.FolderBrowse(button_text="选择文件夹", target='video_input_path_input')],
        [sg.Text("video_output_path【输出处理完的视频的文件夹路径】："),sg.In(key='video_output_path_input', default_text=video_output_path), sg.FolderBrowse(button_text="选择文件夹", target='video_output_path_input')],
        [sg.Text("dictpen_video_path【词典笔存放视频的文件夹路径】："),sg.In(key='dictpen_video_path_input', default_text=dictpen_video_path)],
        [sg.Button("保存并启动删除脚本"), sg.Button("保存并启动添加脚本")]
    ]

    

    window = sg.Window('脚本启动器 ver1.0', layout, size=(800, 400))
    return window, config

def main():
    window, config = initialize()

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        elif event == "自动填充":
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
                    window['table_name_input'].update(table_name)
                    break

            # 关闭连接
            cursor.close()
            conn.close()
        elif event == "保存并启动添加脚本":
            table_name_to_save = values["table_name_input"]
            video_input_path_to_save = values["video_input_path_input"]
            video_output_path_to_save = values["video_output_path_input"]
            vdictpen_video_path_to_save = values["dictpen_video_path_input"]

            data = {
                "table_name": table_name_to_save,
                "video_input_path": video_input_path_to_save,
                "video_output_path": video_output_path_to_save,
                "dictpen_video_path": vdictpen_video_path_to_save
            }

            with open("config.json", "w", encoding="UTF-8") as file_object:
                json.dump(data, file_object)

            os.system('start item_add.exe')
        elif event == "保存并启动删除脚本":
            table_name_to_save = values["table_name_input"]
            video_input_path_to_save = values["video_input_path_input"]
            video_output_path_to_save = values["video_output_path_input"]
            vdictpen_video_path_to_save = values["dictpen_video_path_input"]

            data = {
                "table_name": table_name_to_save,
                "video_input_path": video_input_path_to_save,
                "video_output_path": video_output_path_to_save,
                "dictpen_video_path": vdictpen_video_path_to_save
            }

            with open("config.json", "w", encoding="UTF-8") as file_object:
                json.dump(data, file_object)
            os.system('start item_remove.exe')
    window.close()

if __name__ == "__main__":
    main()
