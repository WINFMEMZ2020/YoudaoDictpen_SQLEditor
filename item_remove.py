import PySimpleGUI as sg
import json
import os
import subprocess
import sqlite3
import time

####
# 读取config.json文件
with open('config.json', 'r') as f:
    config = json.load(f)

dictpen_password = config.get("dictpen_password","")
delete_video_from_dictpen_state = config.get("delete_video_from_dictpen","")
#####

#用于登录adb的函数
def adb_login():
    proc = subprocess.Popen("adb shell auth", shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #获取密码
    global dictpen_password
    password_input = dictpen_password + "\n"
    command_output, error = proc.communicate(input=password_input.encode('utf-8'))

    print("command=",command_output,",error=",error)
    if 'login with "adb shell auth" to continue.' in str(command_output) or 'login with "adb shell auth" to continue.' in str(error):
        return 0
    elif 'adb.exe: more than one device/emulator' in str(command_output) or 'adb.exe: more than one device/emulator' in str(error):
        return 1
    elif 'adb.exe: no devices/emulators found' in str(command_output) or 'adb.exe: no devices/emulators found' in str(error):
        return 2
    elif 'password incorrect!' in str(command_output) or 'password incorrect!' in str(error):        
        command_output, error = proc.communicate(input=b"x3sbrY1d2@dictpen\n")
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

#2024.03.24 移动代码
check_devices_okay()
current_time = time.localtime()
#生成exerciseFavorite.db的文件名称，方便出现问题及时回溯
exerciseFavorite_name = "exerciseFavorite_" + "{:02d}{:02d}{:02d}{:02d}{:02d}{:02d}".format(current_time.tm_year, current_time.tm_mon, current_time.tm_mday, current_time.tm_hour, current_time.tm_min, current_time.tm_sec) + ".db"
#生成并执行pull命令
exerciseFavorite_pull_command = "adb pull /userdisk/math/exerciseFav/exerciseFavorite.db " + exerciseFavorite_name
os.system(exerciseFavorite_pull_command) 
#数据库执行命令
result = extract_data_from_database(exerciseFavorite_name)

item_to_delete = []#要删除的视频的列表


names = []
removed_names = []
lst = sg.Listbox(names, size=(100, 50), font=('Arial Bold', 14), expand_y=True, enable_events=True, key='-LIST-')
data = [[item['code'], item['text']] for item in result]
# 调整Table的宽度和高度
table_width = 300
table_height = min(10, len(result)) * 40

if delete_video_from_dictpen_state == 0:
    layout = [[sg.Text('以下是词典笔里的所有视频\n请选中需要删除的项目然后点击“删除”按钮\u3000\u3000\u3000\u3000\n\n',font=('Arial', 14)),
    sg.Button('移除'),
    sg.Button('保存')],
    [sg.Table(values=data, headings=['code', 'name'], auto_size_columns=True, max_col_width=80,
              display_row_numbers=False, justification='left', num_rows=30, key='-TABLE-')],
    [sg.Text("", key='-MSG-', font=('Arial Bold', 14), justification='center')]
    ]
else:
    layout = [[sg.Text('以下是词典笔里的所有视频\n请选中需要删除的项目然后点击“删除”按钮\u3000\u3000\u3000\u3000\n\n请注意：您目前开启了"同时删除词典笔上的视频文件"选项，删除项目后\n保存的同时会删除词典笔上的对应视频',font=('Arial', 14)),
    sg.Button('移除'),
    sg.Button('保存')],
    [sg.Table(values=data, headings=['code', 'name'], auto_size_columns=True, max_col_width=80,
              display_row_numbers=False, justification='left', num_rows=30, key='-TABLE-')],
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


with open("config.json","r",encoding="UTF-8") as file_object:
    config_content = json.load(file_object)

window = sg.Window('删除词典笔上的项目', layout, size=(800, 600))
#print("result=",result)

#for item_dict in result:
#    names.append(item_dict["text"])
window.finalize()


while True:
    event, values = window.read()
    #print(event, values)#values:{'-LIST-': ['text']}

    #print(video_name_to_delete)
    if event == sg.WIN_CLOSED:
      break
    elif event == '移除':
        selected_row = values['-TABLE-'][0]
        selected_item = {"code": data[selected_row][0], "text": data[selected_row][1]}
        #print(selected_item)
        item_to_delete.append(selected_item)
        data.pop(selected_row)
        window['-TABLE-'].update(values=data)
    elif event == "保存":

        #保存数据库修改
        conn = sqlite3.connect(exerciseFavorite_name)
        cursor = conn.cursor()

        if delete_video_from_dictpen_state == 1:#删除视频
            popout_layout = [
                [sg.Text("请等待脚本完成文件的删除。\n中途脚本可能会出现未响应的情况，请不要进行操作")],
                [sg.Text("正在删除：\n",key="delete_text")]
            ]
            
            # 创建弹出窗口
            popout_window = sg.Window("进程", layout=popout_layout, finalize=True)

            #print(item_to_delete)
            for for_item_to_delete in item_to_delete:
                cursor.execute("SELECT video FROM table_knowledge WHERE code = ?", (for_item_to_delete["code"],))
                row = cursor.fetchone()
                if row:
                    video_content = row[0]
                    video_path_to_delete = video_content.replace("file://", "")
                    delete_command = 'adb shell rm "' + video_path_to_delete + '"'
                    if "/userdisk/Music/" in video_path_to_delete:
                        print("路径检查：路径合法，可以删除")
                        delete_text = "正在删除：\n" + video_path_to_delete
                        os.system(delete_command)
                        popout_window["delete_text"].update(delete_text)
                        popout_window.refresh()
                    else:
                        print("路径不合法，无法删除此文件")
                else:
                    print("No matching row found for code: {}".format(for_item_to_delete["code"]))

        # 遍历item_to_delete列表并删除相应项目
        for item in item_to_delete:
            code_to_delete = item["code"]
            
            # 删除表table_knowledge中匹配的项目
            cursor.execute("DELETE FROM table_knowledge WHERE code = ?", (code_to_delete,))
            
            # 删除表config_content["table_name"]中匹配的项目
            cursor.execute(f"DELETE FROM {config_content['table_name']} WHERE knowledgeId = ?", (code_to_delete,))

        # 提交更改并关闭连接
        conn.commit()
        conn.close()


        check_devices_okay()
        os.system("adb push " + exerciseFavorite_name +" /userdisk/math/exerciseFav/exerciseFavorite.db ")


        if delete_video_from_dictpen_state == 1:
            delete_text = "已全部删除完成，可以关闭该脚本\n删除操作可能需要重新启动词典笔才能看到效果"
            popout_window["delete_text"].update(delete_text)
            popout_window.refresh()

        print("保存成功")
        os.system("pause")

    # elif event == '撤销':
    #     if removed_names:
    #         last_removed_name = removed_names.pop()
    #         names.append(last_removed_name)
    #         window['-LIST-'].update(names)
