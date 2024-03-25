import PySimpleGUI as sg
import json
import os
import subprocess
import sqlite3
import time
import paramiko

class SFTP:
    def __init__(self):
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.connection_start_time = None

    def connect(self, ip, username, password):
        self.connection_start_time = time.time()
        try:
            self.ssh_client.connect(ip, username=username, password=password, timeout=10)
        except paramiko.AuthenticationException:
            print("Authentication failed. Please check your credentials.")
        except paramiko.SSHException as e:
            end_time = time.time()
            wait_time = int(end_time - self.connection_start_time)
            print(f"Connection failed after {wait_time} seconds: {e}")
        except Exception as e:
            end_time = time.time()
            wait_time = int(end_time - self.connection_start_time)
            print(f"Error: {e}")

    def bytes_to_mib(self, bytes_value):
        mib_value = bytes_value / (1024 * 1024)
        return mib_value

    def _execute_sftp(self, local_files, remote_path):
        # 连接SSH服务器
        if not self.ssh_client.get_transport() or not self.ssh_client.get_transport().is_active():
            print("SSH connection is not active.")
            print("连接失败，请检查连接，按enter退出")
            os.system("pause")
            os._exit(1)

        # 创建 SFTP 客户端
        sftp_client = self.ssh_client.open_sftp()

        # 上传文件到远程服务器
        for file_info in local_files:
            local_file_path = file_info["path"]
            remote_file_path = os.path.join(remote_path, file_info["name"])
            total_bytes = os.path.getsize(local_file_path)

            # 检查远程文件是否存在，并获取已传输的大小
            try:
                remote_file_size = sftp_client.stat(remote_file_path).st_size
            except FileNotFoundError:
                remote_file_size = 0

            # 定义进度回调函数
            def progress_callback(bytes_transferred, file_size):
                bytes_transferred_mib = self.bytes_to_mib(bytes_transferred)
                file_size_mib = self.bytes_to_mib(file_size)
                progress = int(bytes_transferred_mib / file_size_mib * 100)
                print(f"\rProgress: {progress}% ({bytes_transferred_mib:.2f} MiB / {file_size_mib:.2f} MiB) - Uploading: {file_info['name']} - Elapsed Time: {self.get_elapsed_time()}", end='', flush=True)

                # 判断是否上传完成
                if bytes_transferred == file_size:
                    print(f"\nUpload complete: {file_info['name']}")

            # 上传文件
            retries = 3  # 设置重试次数
            for attempt in range(retries):
                try:
                    with open(local_file_path, 'rb') as local_file:
                        # 移动文件指针至已传输的位置
                        local_file.seek(remote_file_size)
                        # 从已传输位置开始上传文件，并传入进度回调函数
                        sftp_client.putfo(local_file, remote_file_path, callback=lambda x, y: progress_callback(x + remote_file_size, total_bytes), file_size=total_bytes)
                    break  # 上传成功，跳出重试循环
                except paramiko.SSHException as e:
                    print(f"SSHException occurred during upload: {e}")
                    if attempt < retries - 1:
                        print("Retrying upload...")
                        time.sleep(5)  # 等待一段时间后重试
                    else:
                        print("Upload failed after retries.")
                        raise  # 上传失败，抛出异常

        # 关闭连接
        sftp_client.close()

        print("\nAll files uploaded.")

        # 返回上传完成信息
        return "All files uploaded."

    
    def execute_sftp(self, local_files, remote_path):
        if not self.ssh_client.get_transport() or not self.ssh_client.get_transport().is_active():
            print("SSH connection is not active.")
            print("连接失败，请检查连接，按enter退出")
            os.system("pause")
            os._exit(1)
        sftp_client = self.ssh_client.open_sftp()
        local_file_path = local_files
        remote_file_path = remote_path
        total_bytes = os.path.getsize(local_file_path)
        with open(local_file_path, 'rb') as local_file:
            sftp_client.putfo(local_file, remote_file_path)
        sftp_client.close()
        print("\nAll files uploaded.")
        return "All files uploaded."


    def get_elapsed_time(self):
        if self.connection_start_time is not None:
            elapsed_time = int(time.time() - self.connection_start_time)
            return f"{elapsed_time} seconds"
        else:
            return "N/A"

    def pull_file(self, remote_path, local_path):
        if not self.ssh_client.get_transport() or not self.ssh_client.get_transport().is_active():
            print("SSH connection is not active.")
            print("连接失败，请检查连接，按enter退出")
            os.system("pause") 
            os._exit(1)
        # 创建 SFTP 客户端
        sftp_client = self.ssh_client.open_sftp()

        # 下载文件
        try:
            sftp_client.get(remote_path, local_path)
            print(f"File downloaded successfully to {local_path}")
        except Exception as e:
            print(f"Error downloading file: {e}")

        # 关闭连接
        sftp_client.close()

sftp = SFTP()


####
# 读取config.json文件
with open('config.json', 'r') as f:
    config = json.load(f)

dictpen_password = config.get("dictpen_password","")
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


def initialize():
    # 读取config.json文件
    with open('config.json', 'r') as f:
        config = json.load(f)

    table_name = config.get("table_name","")
    video_input_path = config.get('video_input_path', '')
    dictpen_video_path = config.get("dictpen_video_path","")
    dictpen_password = config.get("dictpen_password","")
    copy_video_to_dictpen = config.get("copy_video_to_dictpen","")
    delete_video_from_dictpen = config.get("delete_video_from_dictpen","")
    remote_copy_video_to_dictpen = config.get("remote_copy_video_to_dictpen","")
    ip_address = config.get("ip_address","")
    dictpen_root = config.get("dictpen_root","")

    layout = [
        [sg.Text("请修改您需要的参数，然后点击“确定并启动”按钮来启动脚本\n默认情况下，不建议随便更改陌生的数值。", font={'family': 'SimHei', 'size': 20, 'weight': 'bold'})],
        [sg.Text("dictpen_password【词典笔的adb密码，请先填入此项】："),sg.In(key='dictpen_password_input', default_text=dictpen_password),sg.Button("密码帮助")],
        [sg.Text("dictpen_ip【词典笔的ip地址，线传非必填，当使用远程传输时必须填写此项】："),sg.In(key='dictpen_ip_input', default_text=ip_address)],
        [sg.Text("dictpen_root【词典笔的root密码，线传非必填，当使用远程传输时必须填写此项】："),sg.In(key='dictpen_root_input',default_text=dictpen_root)],
        [sg.Text("table_name【表table_mathexercise的完整名称】："),sg.In(key='table_name_input', default_text=table_name), sg.Button("自动填充")],
        [sg.Text("video_input_path【输入视频的文件夹路径】："),sg.In(key='video_input_path_input', default_text=video_input_path), sg.FolderBrowse(button_text="选择文件夹", target='video_input_path_input')],
        [sg.Text("dictpen_video_path【词典笔存放视频的文件夹路径】："),sg.In(key='dictpen_video_path_input', default_text=dictpen_video_path),sg.Button("帮助")],
        [sg.Checkbox("在删除脚本中，将项目从词典笔删除时，同时删除词典笔上的视频文件（即执行rm）",default=copy_video_to_dictpen == 1, key="delete_video_from_dictpen_checkbox")],
        [sg.Checkbox("在添加脚本中，将项目添加到词典笔时，同时拷入电脑上的视频文件（即执行adb push）",default=delete_video_from_dictpen == 1, key="copy_video_to_dictpen_checkbox")],
        [sg.Checkbox("远程进行操作（即利用ssh）",default=remote_copy_video_to_dictpen == 0, key="remote_copy_video_to_dictpen_checkbox")],
        [sg.Button("保存并启动删除脚本"), sg.Button("保存并启动添加脚本"),sg.Button("设置开机自启ssh")]
    ]




    window = sg.Window('脚本启动器 ver1.3', layout, size=(800, 400))
    return window, config

def main():
    window, config = initialize()

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        elif event == "自动填充":
            #先保存adb密码
            table_name_to_save = values["table_name_input"]
            video_input_path_to_save = values["video_input_path_input"]
            vdictpen_video_path_to_save = values["dictpen_video_path_input"]
            vdictpen_password = values["dictpen_password_input"]
            ip_address = values["dictpen_ip_input"]
            dictpen_root = values["dictpen_root_input"]
            copy_video_to_dictpen = 1 if values["copy_video_to_dictpen_checkbox"] else 0
            delete_video_from_dictpen = 1 if values["delete_video_from_dictpen_checkbox"] else 0
            remote_copy_video_to_dictpen = 1 if values["remote_copy_video_to_dictpen_checkbox"] else 0
            data = {
                "table_name": table_name_to_save,
                "video_input_path": video_input_path_to_save,
                "dictpen_video_path": vdictpen_video_path_to_save,
                "dictpen_password":vdictpen_password,
                "copy_video_to_dictpen": copy_video_to_dictpen,
                "delete_video_from_dictpen": delete_video_from_dictpen,
                "remote_copy_video_to_dictpen": remote_copy_video_to_dictpen,
                "dictpen_root": dictpen_root,
                "ip_address": ip_address
            }

            with open("config.json", "w", encoding="UTF-8") as file_object:
                json.dump(data, file_object)
            remote_copy_status = remote_copy_video_to_dictpen
            current_time = time.localtime()
            exerciseFavorite_name = "exerciseFavorite_" + "{:02d}{:02d}{:02d}{:02d}{:02d}{:02d}".format(current_time.tm_year, current_time.tm_mon, current_time.tm_mday, current_time.tm_hour, current_time.tm_min, current_time.tm_sec) + ".db"
            if remote_copy_status == 1:
                sftp.connect(ip_address, "root", dictpen_root)
                local_file_path = './' + exerciseFavorite_name  # 当前目录
                sftp.pull_file("/userdisk/math/exerciseFav/exerciseFavorite.db", local_file_path) 
            #检查设备是否处于OK状态
            else:
                check_devices_okay()
                #生成exerciseFavorite.db的文件名称，方便出现问题及时回溯
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
                if not table[0].startswith('table_mathexercise_anonymous') and not table[0].startswith('table_knowledge'):
                    table_name = table[0]
                    window['table_name_input'].update(table_name)
                    break

            # 关闭连接
            cursor.close()
            conn.close()
        elif event == "保存并启动添加脚本":

            table_name_to_save = values["table_name_input"]
            video_input_path_to_save = values["video_input_path_input"]
            vdictpen_video_path_to_save = values["dictpen_video_path_input"]
            vdictpen_password = values["dictpen_password_input"]
            ip_address = values["dictpen_ip_input"]
            dictpen_root = values["dictpen_root_input"]
            copy_video_to_dictpen = 1 if values["copy_video_to_dictpen_checkbox"] else 0
            delete_video_from_dictpen = 1 if values["delete_video_from_dictpen_checkbox"] else 0
            remote_copy_video_to_dictpen = 1 if values["remote_copy_video_to_dictpen_checkbox"] else 0
            data = {
                "table_name": table_name_to_save,
                "video_input_path": video_input_path_to_save,
                "dictpen_video_path": vdictpen_video_path_to_save,
                "dictpen_password":vdictpen_password,
                "copy_video_to_dictpen": copy_video_to_dictpen,
                "delete_video_from_dictpen": delete_video_from_dictpen,
                "remote_copy_video_to_dictpen": remote_copy_video_to_dictpen,
                "dictpen_root": dictpen_root,
                "ip_address": ip_address
            }

            with open("config.json", "w", encoding="UTF-8") as file_object:
                json.dump(data, file_object)

            os.system('item_add.py')

        elif event == "设置开机自启ssh":
            table_name_to_save = values["table_name_input"]
            video_input_path_to_save = values["video_input_path_input"]
            vdictpen_video_path_to_save = values["dictpen_video_path_input"]
            vdictpen_password = values["dictpen_password_input"]
            ip_address = values["dictpen_ip_input"]
            dictpen_root = values["dictpen_root_input"]
            copy_video_to_dictpen = 1 if values["copy_video_to_dictpen_checkbox"] else 0
            delete_video_from_dictpen = 1 if values["delete_video_from_dictpen_checkbox"] else 0
            remote_copy_video_to_dictpen = 1 if values["remote_copy_video_to_dictpen_checkbox"] else 0
            data = {
                "table_name": table_name_to_save,
                "video_input_path": video_input_path_to_save,
                "dictpen_video_path": vdictpen_video_path_to_save,
                "dictpen_password":vdictpen_password,
                "copy_video_to_dictpen": copy_video_to_dictpen,
                "delete_video_from_dictpen": delete_video_from_dictpen,
                "remote_copy_video_to_dictpen": remote_copy_video_to_dictpen,
                "dictpen_root": dictpen_root,
                "ip_address": ip_address
            }
            with open("config.json", "w", encoding="UTF-8") as file_object:
                json.dump(data, file_object)
                            
            os.system('start ssh.py')

        elif event == "保存并启动删除脚本":
            #先保存adb密码
            table_name_to_save = values["table_name_input"]
            video_input_path_to_save = values["video_input_path_input"]
            vdictpen_video_path_to_save = values["dictpen_video_path_input"]
            vdictpen_password = values["dictpen_password_input"]
            ip_address = values["dictpen_ip_input"]
            dictpen_root = values["dictpen_root_input"]
            copy_video_to_dictpen = 1 if values["copy_video_to_dictpen_checkbox"] else 0
            delete_video_from_dictpen = 1 if values["delete_video_from_dictpen_checkbox"] else 0
            remote_copy_video_to_dictpen = 1 if values["remote_copy_video_to_dictpen_checkbox"] else 0
            data = {
                "table_name": table_name_to_save,
                "video_input_path": video_input_path_to_save,
                "dictpen_video_path": vdictpen_video_path_to_save,
                "dictpen_password":vdictpen_password,
                "copy_video_to_dictpen": copy_video_to_dictpen,
                "delete_video_from_dictpen": delete_video_from_dictpen,
                "remote_copy_video_to_dictpen": remote_copy_video_to_dictpen,
                "dictpen_root": dictpen_root,
                "ip_address": ip_address
            }

            with open("config.json", "w", encoding="UTF-8") as file_object:
                json.dump(data, file_object)

            os.system('start item_remove.py')
        elif event == "帮助":
            # 定义弹出窗口的布局
            popout_layout = [
                [sg.Text("请选择符合您的条件的选项:\n")],
                [sg.Text("我希望将文件直接存放到词典笔的Music目录下"), sg.Button(" 我符合此条件", key='condition1')],
                [sg.Text("我希望将文件存储到词典笔的Music文件夹下的某个目录中,路径为: /userdisk/Music/"),sg.In(key="path_under_music_input"),sg.Text("/") , sg.Button(" 我符合此条件", key='condition2')],
                [sg.Text('\n\n如果您希望将视频文件直接拷贝到词典笔的MTP磁盘下的Music目录中,请选择第一项"我希望将文件直接存放到词典笔的Music目录下"\n\n如果您希望将视频文件拷贝到词典笔的MTP磁盘下的Music文件夹下的某个目录中,请选择第二项""我希望将文件存储到词典笔的Music文件夹下的\n某个目录中",并在输入框中填入Music文件夹下的拷入视频的文件夹的名称.\n\n\n一般情况下,建议直接选择第一项,并直接将视频文件拷贝到Music目录下即可.\n如果您要选择第二项,那么输入框只能填写Music文件夹下的自己的文件夹的名称,后面不要带"/"或"//"等\n字符.或者可以填写嵌套文件夹的目录,如"Video/2024/files",文件夹之间使用"/"隔开而不是"//"\n')]
            ]

            # 创建弹出窗口
            popout_window = sg.Window("帮助", layout=popout_layout)

            while True:
                popout_event, popout_values = popout_window.read()

                if popout_event == sg.WINDOW_CLOSED:
                    break
                if popout_event == 'condition1':
                    window["dictpen_video_path_input"].update("file:///userdisk/Music/")
                    break
                elif popout_event == 'condition2':
                    path_under_music = popout_values["path_under_music_input"]
                    window["dictpen_video_path_input"].update(f"file:///userdisk/Music/{path_under_music}/")
                    break
            popout_window.close()

        elif event == "密码帮助":
            # 定义弹出窗口的布局
            popout_layout = [
                [sg.Text("请选择符合您的条件的选项:\n")],
                [sg.Text("我的词典笔为三代或三代专业版，如YDP031,密码为CherryYoudao"), sg.Button(" 我符合此条件", key='condition1_t')],
                [sg.Text("我的词典笔为三代极速版或x3s，如YDP038，密码为x3sbrY1d2@dictpen"), sg.Button(" 我符合此条件", key='condition2_t')],
                [sg.Text("我需要自定义一个密码，密码为："),sg.In(key="password_to_input"),sg.Button(" 我符合此条件", key='condition3_t')],
                [sg.Text("\n请注意——adb的密码极其重要，如果您出现添加/删除脚本长时间无响应或提示密码错误的情况，请尝试更换adb密码。")]
                ]

            # 创建弹出窗口
            popout_window = sg.Window("密码帮助", layout=popout_layout)

            while True:
                popout_event, popout_values = popout_window.read()

                if popout_event == sg.WINDOW_CLOSED:
                    break
                if popout_event == 'condition1_t':
                    window["dictpen_password_input"].update("CherryYoudao")
                    break
                elif popout_event == 'condition2_t':
                    window["dictpen_password_input"].update("x3sbrY1d2@dictpen")
                    break
                elif popout_event == 'condition3_t':
                    password_to_input_value = popout_values["password_to_input"]
                    window["dictpen_password_input"].update(f"{password_to_input_value}")
                    break
            popout_window.close()
    window.close()

if __name__ == "__main__":
    main()
