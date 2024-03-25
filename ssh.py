import os
import subprocess
import json
####
# 读取config.json文件
with open('config.json', 'r') as f:
    config = json.load(f)

dictpen_password = config.get("dictpen_password","")

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



def is_string_in_file(filename, search_string):#寻找字符串
      try:
            with open(filename, 'r') as file:
                  for line in file:
                        if search_string in line:
                              return True
      except FileNotFoundError:
            print(f"File '{filename}' not found.")
      return False
 
        #用户确认开始操作

print("注意，该过程涉及操作系统文件，有变砖可能\n如果没有错误，按下Enter开始执行脚本\n")
veryfy = input("注意，该过程涉及操作系统文件，有变砖可能，手动操作最佳，若要继续执行，请输入 我已知晓风险\n")
if veryfy == str("我已知晓风险"):
    os.system("pause")
    #检查设备是否处于OK状态
    check_devices_okay()
    rcs_pull_command = "adb pull /etc/init.d/rcS ./rcS_"
    rcs_push_command = "adb push rcS /etc/init.d/rcS"
    start_command = "adb shell sshd_sevice start"
    chmod_command = "adb shell chmod +x /etc/init.d/rcS"
    pwd_command = "adb shell passwd"
    os.system(rcs_pull_command) 

    filename = 'rcS_'
    search_string = '/usr/sbin/dropbear'
    
    if is_string_in_file(filename, search_string):#防止重复开启
        print("已经开启过了，无需再次开启")
        os.system("pause")

    else:
        print("请确认您的参数正确无误。如果发现错误，请退出本程序并修改。\n如果没有错误，按下Enter开始执行脚本\n")
        os.system("pause")
        os.system("cls")
            #检查设备是否处于OK状态
        check_devices_okay()
        print("请输入新的root密码")
        os.system("adb shell passwd") 
        os.system(rcs_push_command) 
        os.system(chmod_command) 
        os.system(start_command)
        print("操作已完成") 
        os.system("pause") 
        exit
else:
    print("按下enter退出")
    os.system("pause")




