import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import psutil
import subprocess
import threading
import sys
import os
import socket

class PortManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Windows 端口管理面板")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)
        
        # 检查管理员权限
        self.is_admin = self.check_admin()
        
        # 存储端口数据
        self.port_data = []
        self.selected_items = []
        
        self.setup_ui()
        self.refresh_ports()
    
    def check_admin(self):
        """检查是否以管理员身份运行"""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def setup_ui(self):
        """设置界面"""
        # 顶部工具栏
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="🔄 刷新列表", command=self.refresh_ports).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔍 搜索", command=self.search_port).pack(side=tk.LEFT, padx=2)
        
        # 使用 tk.Button 而不是 ttk.Button 来支持 bg 参数
        tk.Button(toolbar, text="❌ 结束选中", command=self.kill_selected, 
                 bg="#ff6b6b", fg="white", activebackground="#ff4757",
                 relief=tk.RAISED, bd=2).pack(side=tk.LEFT, padx=2)
        
        tk.Button(toolbar, text="💀 批量结束", command=self.batch_kill, 
                 bg="#ee5a6f", fg="white", activebackground="#ff4757",
                 relief=tk.RAISED, bd=2).pack(side=tk.LEFT, padx=2)
        
        # 端口过滤输入框
        ttk.Label(toolbar, text="  端口过滤:").pack(side=tk.LEFT, padx=(20, 0))
        self.filter_var = tk.StringVar()
        self.filter_entry = ttk.Entry(toolbar, textvariable=self.filter_var, width=15)
        self.filter_entry.pack(side=tk.LEFT, padx=2)
        self.filter_entry.bind('<Return>', lambda e: self.search_port())
        ttk.Button(toolbar, text="清除", command=self.clear_filter).pack(side=tk.LEFT, padx=2)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        if not self.is_admin:
            self.status_var.set("⚠️ 当前未以管理员身份运行，可能无法结束某些系统进程")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # 主内容区（Treeview + 滚动条）
        columns = ("protocol", "local_addr", "port", "pid", "process", "status")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", selectmode="extended")
        
        # 设置列标题
        self.tree.heading("protocol", text="协议", command=lambda: self.sort_column("protocol", False))
        self.tree.heading("local_addr", text="本地地址", command=lambda: self.sort_column("local_addr", False))
        self.tree.heading("port", text="端口", command=lambda: self.sort_column("port", True))
        self.tree.heading("pid", text="PID", command=lambda: self.sort_column("pid", True))
        self.tree.heading("process", text="进程名称", command=lambda: self.sort_column("process", False))
        self.tree.heading("status", text="状态", command=lambda: self.sort_column("status", False))
        
        # 设置列宽
        self.tree.column("protocol", width=60, anchor="center")
        self.tree.column("local_addr", width=150)
        self.tree.column("port", width=80, anchor="center")
        self.tree.column("pid", width=80, anchor="center")
        self.tree.column("process", width=200)
        self.tree.column("status", width=100, anchor="center")
        
        # 滚动条
        scrollbar_y = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(self.root, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        scrollbar_y.pack(fill=tk.Y, side=tk.RIGHT)
        scrollbar_x.pack(fill=tk.X, side=tk.BOTTOM)
        
        # 右键菜单
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="结束该进程", command=self.kill_selected)
        self.context_menu.add_command(label="复制端口", command=self.copy_port)
        self.context_menu.add_command(label="查看详情", command=self.view_details)
        
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", lambda e: self.view_details())
        
        # 绑定多选事件
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        
        # 勾选框样式（实际使用 tag 实现行选中高亮）
        self.tree.tag_configure("selected", background="#e1f5fe")
    
    def refresh_ports(self):
        """刷新端口列表"""
        self.status_var.set("正在扫描端口...")
        self.root.update()
        
        # 清空现有数据
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.port_data.clear()
        
        try:
            # 获取网络连接
            connections = psutil.net_connections(kind='inet')
            
            for conn in connections:
                if conn.status == 'LISTEN' or conn.laddr:
                    try:
                        protocol = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"
                        ip = conn.laddr.ip if conn.laddr else ""
                        port = conn.laddr.port if conn.laddr else ""
                        pid = conn.pid or ""
                        
                        # 获取进程名
                        process_name = ""
                        if pid:
                            try:
                                proc = psutil.Process(pid)
                                process_name = proc.name()
                            except:
                                process_name = "Unknown"
                        
                        status = conn.status if conn.status else ""
                        
                        # 插入到表格
                        item = self.tree.insert("", tk.END, values=(
                            protocol, ip, port, pid, process_name, status
                        ))
                        
                        self.port_data.append({
                            'item_id': item,
                            'protocol': protocol,
                            'ip': ip,
                            'port': port,
                            'pid': pid,
                            'process': process_name,
                            'status': status
                        })
                    except Exception as e:
                        continue
            
            count = len(self.port_data)
            self.status_var.set(f"共找到 {count} 个端口监听（选中 0 个）")
            
        except Exception as e:
            messagebox.showerror("错误", f"获取端口信息失败: {str(e)}")
            self.status_var.set("获取端口信息失败")
    
    def search_port(self):
        """根据端口或进程名过滤"""
        keyword = self.filter_var.get().lower()
        if not keyword:
            return
        
        # 清除之前的选择
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        filtered_count = 0
        for data in self.port_data:
            if (keyword in str(data['port']).lower() or 
                keyword in data['process'].lower() or
                keyword in str(data['pid']).lower()):
                self.tree.insert("", tk.END, values=(
                    data['protocol'], data['ip'], data['port'], 
                    data['pid'], data['process'], data['status']
                ))
                filtered_count += 1
        
        self.status_var.set(f"过滤结果: {filtered_count} 个匹配 '{keyword}' 的端口")
    
    def clear_filter(self):
        """清除过滤器"""
        self.filter_var.set("")
        self.refresh_ports()
    
    def on_select(self, event):
        """处理选择变化"""
        selection = self.tree.selection()
        count = len(selection)
        if count > 0:
            self.selected_items = []
            for item in selection:
                values = self.tree.item(item, "values")
                self.selected_items.append({
                    'port': values[2],
                    'pid': values[3],
                    'process': values[4]
                })
            self.status_var.set(f"已选中 {count} 个端口")
    
    def kill_selected(self):
        """结束选中的进程"""
        if not self.selected_items:
            messagebox.showwarning("提示", "请先选择要结束的端口")
            return
        
        item = self.selected_items[0]
        pid = item['pid']
        port = item['port']
        process = item['process']
        
        if not pid:
            messagebox.showerror("错误", "无法获取进程PID")
            return
        
        if messagebox.askyesno("确认", f"确定要结束进程吗？\n\n端口: {port}\n进程: {process}\nPID: {pid}"):
            self.kill_process(pid, port)
    
    def batch_kill(self):
        """批量结束进程"""
        if not self.selected_items:
            messagebox.showwarning("提示", "请先选择要结束的端口（按住Ctrl可多选）")
            return
        
        if len(self.selected_items) == 1:
            self.kill_selected()
            return
        
        info = "\n".join([f"端口: {item['port']} | PID: {item['pid']} | {item['process']}" 
                         for item in self.selected_items[:10]])
        if len(self.selected_items) > 10:
            info += f"\n... 还有 {len(self.selected_items)-10} 个 ..."
        
        if messagebox.askyesno("确认批量结束", f"确定要结束以下 {len(self.selected_items)} 个进程吗？\n\n{info}"):
            success_count = 0
            fail_count = 0
            
            for item in self.selected_items:
                if self.kill_process(item['pid'], item['port'], silent=True):
                    success_count += 1
                else:
                    fail_count += 1
            
            messagebox.showinfo("结果", f"批量结束完成\n成功: {success_count}\n失败: {fail_count}")
            self.refresh_ports()
    
    def kill_process(self, pid, port, silent=False):
        """结束指定进程"""
        try:
            pid = int(pid)
            proc = psutil.Process(pid)
            proc_name = proc.name()
            
            # 尝试优雅终止
            proc.terminate()
            proc.wait(timeout=3)
            
            if not silent:
                messagebox.showinfo("成功", f"已结束进程\n端口: {port}\n进程: {proc_name}\nPID: {pid}")
                self.refresh_ports()
            return True
            
        except psutil.NoSuchProcess:
            if not silent:
                messagebox.showerror("错误", "进程不存在或已结束")
            return False
        except psutil.AccessDenied:
            try:
                # 如果优雅终止失败，尝试强制结束
                subprocess.run(f"taskkill /F /PID {pid}", shell=True, check=True)
                if not silent:
                    messagebox.showinfo("成功", f"已强制结束进程\n端口: {port}\nPID: {pid}")
                    self.refresh_ports()
                return True
            except:
                if not silent:
                    messagebox.showerror("权限不足", "无法结束该进程，请尝试以管理员身份运行程序")
                return False
        except Exception as e:
            if not silent:
                messagebox.showerror("错误", str(e))
            return False
    
    def view_details(self):
        """查看详细信息"""
        if not self.selected_items:
            return
        
        item = self.selected_items[0]
        pid = item['pid']
        
        if not pid:
            messagebox.showinfo("详情", "无法获取详细信息（无PID）")
            return
        
        try:
            proc = psutil.Process(int(pid))
            info = f"""
进程详情:
─────────────────
PID: {pid}
名称: {proc.name()}
路径: {proc.exe()}
创建时间: {proc.create_time()}
内存使用: {proc.memory_info().rss / 1024 / 1024:.2f} MB
CPU使用率: {proc.cpu_percent()}%
状态: {proc.status()}
            
命令行: {proc.cmdline()}
            """
            messagebox.showinfo("进程详情", info)
        except Exception as e:
            messagebox.showerror("错误", f"获取详情失败: {str(e)}")
    
    def copy_port(self):
        """复制端口到剪贴板"""
        if self.selected_items:
            port = self.selected_items[0]['port']
            self.root.clipboard_clear()
            self.root.clipboard_append(str(port))
            self.status_var.set(f"已复制端口 {port} 到剪贴板")
    
    def show_context_menu(self, event):
        """显示右键菜单"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def sort_column(self, col, reverse):
        """排序功能"""
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children()]
        
        # 尝试数字排序
        try:
            data = [(int(x[0]), x[1]) for x in data]
        except ValueError:
            pass
        
        data.sort(reverse=reverse)
        
        for index, (_, child) in enumerate(data):
            self.tree.move(child, '', index)
        
        # 切换排序方向
        self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))

def run_as_admin():
    """尝试以管理员身份重新运行"""
    try:
        if sys.platform == 'win32':
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
                sys.exit()
    except:
        pass

if __name__ == "__main__":
    # 如需强制管理员权限，取消下面这行注释
    # run_as_admin()
    
    root = tk.Tk()
    app = PortManager(root)
    root.mainloop()
