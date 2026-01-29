import os
path = r"C:\Users\Administrator\OneDrive\Desktop" + input(r'输入路径(例：\src\main)：')
if not os.path.exists(path):
    os.makedirs(path)
    print('创建成功')
else:
    print('该文件夹路径已存在')
os.startfile(path)
os.system('pause')
