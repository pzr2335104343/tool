import os
import pandas as pd
from openpyxl import load_workbook
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl.reader.drawings")

def replace_string_in_excel(folder_path, old_str, new_str, save_backup=True):
    """
    替换文件夹中所有Excel文件里的指定字符串
    
    参数:
    folder_path (str): Excel文件所在文件夹路径
    old_str (str): 需要替换的旧字符串
    new_str (str): 用于替换的新字符串
    save_backup (bool): 是否保存备份文件
    """
    # 遍历文件夹中的所有文件
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # 检查文件是否为Excel文件
            if file.endswith(('.xlsx', '.xls')):
                file_path = os.path.join(root, file)
                print(f"正在处理文件: {file_path}")
                
                try:
                    # 处理.xlsx文件（使用openpyxl）
                    if file.endswith('.xlsx'):
                        # 加载工作簿
                        wb = load_workbook(file_path)
                        
                        # 遍历所有表
                        for sheet in wb:
                            # 遍历所有行和列
                            for row in sheet.iter_rows():
                                for cell in row:
                                    # 检查单元格值是否为字符串且包含旧字符串
                                    if isinstance(cell.value, str) and old_str in cell.value:
                                        # 替换字符串
                                        cell.value = cell.value.replace(old_str, new_str)
                        
                        # 保存修改前先备份
                        if save_backup:
                            backup_path = file_path + '.bak'
                            wb.save(backup_path)
                            print(f"已保存备份文件: {backup_path}")
                        
                        # 保存修改后的文件
                        wb.save(file_path)
                        print(f"已成功处理文件: {file_path}")
                    
                    # 处理.xls文件（使用pandas）
                    elif file.endswith('.xls'):
                        # 读取Excel文件
                        xls = pd.ExcelFile(file_path)
                        
                        # 获取所有表名
                        sheet_names = xls.sheet_names
                        
                        # 创建一个字典存储所有表的数据
                        dfs = {}
                        
                        # 遍历所有表
                        for sheet_name in sheet_names:
                            # 获取当前表的数据
                            df = xls.parse(sheet_name)
                            
                            # 将所有字符串类型的单元格中的旧字符串替换为新字符串
                            df = df.applymap(lambda x: x.replace(old_str, new_str) if isinstance(x, str) else x)
                            
                            # 存储处理后的数据
                            dfs[sheet_name] = df
                        
                        # 保存修改前先备份
                        if save_backup:
                            backup_path = file_path + '.bak'
                            os.replace(file_path, backup_path)
                            print(f"已保存备份文件: {backup_path}")
                        
                        # 将处理后的数据写回Excel文件
                        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                            for sheet_name, df in dfs.items():
                                df.to_excel(writer, sheet_name=sheet_name, index=False)
                        
                        print(f"已成功处理文件: {file_path}")
                
                except Exception as e:
                    print(f"处理文件 {file_path} 时出错: {e}")

if __name__ == "__main__":
    # 设置文件夹路径
    folder_path = input("请输入Excel文件所在文件夹路径: ")
    
    # 设置需要替换的字符串
    old_str = input("请输入需要替换的字符串: ")
    new_str = input("请输入替换后的字符串: ")
    
    # 设置是否保存备份
    save_backup_input = input("是否保存备份文件？(y/n): ").lower()
    save_backup = save_backup_input == 'y' or save_backup_input == 'yes'
    
    # 执行替换操作
    replace_string_in_excel(folder_path, old_str, new_str, save_backup)    
