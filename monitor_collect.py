import psutil
import time
import os
from datetime import datetime
import signal
import sys

class SystemMonitor:
    def __init__(self):
        # 创建result目录
        self.result_dir = "./result"
        if not os.path.exists(self.result_dir):
            os.makedirs(self.result_dir)
            
        # 读取配置文件
        self.collect_files = self._read_config("./config/collect_files.conf")
        self.process_names = self._read_config("./config/process_names.conf")
        
        # 记录上次读取的日志位置
        self.log_positions = {}
        
        # 添加运行标志
        self.running = True
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """处理退出信号"""
        print("\n正在优雅退出...")
        self.running = False
        
    def _read_config(self, config_file):
        """读取配置文件"""
        if not os.path.exists(config_file):
            return []
        with open(config_file, 'r') as f:
            return [line.strip() for line in f if line.strip()]
            
    def collect_cpu(self):
        """收集CPU使用率"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cpu_percent = psutil.cpu_percent(interval=1)
        with open(f"{self.result_dir}/cpu.txt", 'a') as f:
            f.write(f"{timestamp} {cpu_percent}%\n")
            
    def collect_memory(self):
        """收集内存使用率"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        mem = psutil.virtual_memory()
        with open(f"{self.result_dir}/memory.txt", 'a') as f:
            f.write(f"{timestamp} {mem.percent}%\n")
            
    def collect_disk(self):
        """收集磁盘容量使用率"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        disk = psutil.disk_usage('/')
        with open(f"{self.result_dir}/disk.txt", 'a') as f:
            f.write(f"{timestamp} 总容量:{disk.total/1024/1024/1024:.1f}GB "
                   f"已用:{disk.used/1024/1024/1024:.1f}GB "
                   f"可用:{disk.free/1024/1024/1024:.1f}GB "
                   f"使用率:{disk.percent}%\n")
            
    def collect_disk_io(self):
        """收集磁盘IO情况"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        disk_io = psutil.disk_io_counters()
        with open(f"{self.result_dir}/disk_io.txt", 'a') as f:
            f.write(f"{timestamp} 读取字节:{disk_io.read_bytes/1024/1024:.1f}MB "
                   f"写入字节:{disk_io.write_bytes/1024/1024:.1f}MB "
                   f"读取次数:{disk_io.read_count} "
                   f"写入次数:{disk_io.write_count}\n")
            
    def collect_network(self):
        """收集网络流量"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        net_io = psutil.net_io_counters()
        with open(f"{self.result_dir}/network.txt", 'a') as f:
            f.write(f"{timestamp} 发送:{net_io.bytes_sent} 接收:{net_io.bytes_recv}\n")
            
    def collect_kernel_log(self):
        """收集内核日志"""
        try:
            # 使用 /dev/kmsg 而不是 /var/log/kern.log
            with open('/dev/kmsg', 'r') as f:
                # 设置非阻塞模式
                import fcntl
                import os
                flags = fcntl.fcntl(f.fileno(), fcntl.F_GETFL)
                fcntl.fcntl(f.fileno(), fcntl.F_SETFL, flags | os.O_NONBLOCK)
                
                try:
                    while True:
                        # 读取新的内核消息
                        line = f.readline()
                        if not line:
                            break
                        
                        # 写入到输出文件
                        with open(f"{self.result_dir}/kernel.txt", 'a') as out:
                            out.write(line)
                except IOError:
                    # 没有更多数据可读时会抛出IOError
                    pass
                
        except Exception as e:
            print(f"Error collecting kernel log: {e}")
            
    def collect_specified_files(self):
        """收集指定文件的内容"""
        for file_path in self.collect_files:
            try:
                if not os.path.exists(file_path):
                    continue
                    
                output_file = f"{self.result_dir}/{os.path.basename(file_path)}.txt"
                current_size = os.path.getsize(file_path)
                
                # 如果是首次监控该文件，或文件被重写了
                if file_path not in self.log_positions or current_size < self.log_positions[file_path]:
                    # 读取文件全部内容
                    with open(file_path, 'r') as f:
                        content = f.read()
                        # 如果是首次监控，写入全部内容
                        if file_path not in self.log_positions:
                            with open(output_file, 'w') as out:  # 使用'w'模式覆盖写入
                                out.write(content)
                        # 如果是文件被重写，追加写入新内容
                        else:
                            with open(output_file, 'a') as out:
                                out.write(content)
                        self.log_positions[file_path] = current_size
                # 如果文件有新增内容
                elif current_size > self.log_positions[file_path]:
                    with open(file_path, 'r') as f:
                        f.seek(self.log_positions[file_path])
                        new_content = f.read()
                        if new_content:
                            with open(output_file, 'a') as out:
                                out.write(new_content)
                        self.log_positions[file_path] = f.tell()
                    
            except Exception as e:
                print(f"Error collecting file {file_path}: {e}")
                
    def collect_top_processes(self):
        """收集进程信息"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # CPU TOP 10
        processes = sorted(psutil.process_iter(['pid', 'name', 'cpu_percent']), 
                         key=lambda p: p.info['cpu_percent'], reverse=True)[:10]
        with open(f"{self.result_dir}/cpu_top10.pids", 'a') as f:
            f.write('\n')  # 先打印换行
            f.write(f"{timestamp}\n")
            for proc in processes:
                f.write(f"PID:{proc.info['pid']} Name:{proc.info['name']} CPU:{proc.info['cpu_percent']}%\n")
                
        # Memory TOP 10
        processes = sorted(psutil.process_iter(['pid', 'name', 'memory_percent']), 
                         key=lambda p: p.info['memory_percent'], reverse=True)[:10]
        with open(f"{self.result_dir}/memory_top10.pids", 'a') as f:
            f.write('\n')  # 先打印换行
            f.write(f"{timestamp}\n")
            for proc in processes:
                f.write(f"PID:{proc.info['pid']} Name:{proc.info['name']} MEM:{proc.info['memory_percent']:.1f}%\n")
                
        # Disk TOP 10
        processes_io = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                io_counters = proc.io_counters()
                processes_io.append({
                    'pid': proc.pid,
                    'name': proc.name(),
                    'io_bytes': io_counters.read_bytes + io_counters.write_bytes
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        processes_io.sort(key=lambda x: x['io_bytes'], reverse=True)
        with open(f"{self.result_dir}/disk_top10.pids", 'a') as f:
            f.write('\n')  # 先打印换行
            f.write(f"{timestamp}\n")
            for proc in processes_io[:10]:
                f.write(f"PID:{proc['pid']} Name:{proc['name']} IO:{proc['io_bytes']/1024/1024:.1f}MB\n")
                
        # Network TOP 10
        processes_net = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                connections = proc.connections()
                bytes_total = sum(conn.bytes_sent + conn.bytes_recv 
                                for conn in connections 
                                if hasattr(conn, 'bytes_sent'))
                if bytes_total > 0:
                    processes_net.append({
                        'pid': proc.pid,
                        'name': proc.name(),
                        'bytes_total': bytes_total
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        processes_net.sort(key=lambda x: x['bytes_total'], reverse=True)
        with open(f"{self.result_dir}/network_top10.pids", 'a') as f:
            f.write('\n')  # 先打印换行
            f.write(f"{timestamp}\n")
            for proc in processes_net[:10]:
                f.write(f"PID:{proc['pid']} Name:{proc['name']} "
                       f"流量:{proc['bytes_total']/1024:.1f}KB\n")
                
    def check_process_exist(self):
        """检查指定进程是否存在"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(f"{self.result_dir}/process_exist.txt", 'a') as f:
            f.write('\n')  # 先打印换行
            f.write(f"{timestamp}\n")
            for proc_name in self.process_names:
                exists = False
                for proc in psutil.process_iter(['name']):
                    if proc_name.lower() in proc.info['name'].lower():
                        exists = True
                        break
                f.write(f"{proc_name}: {'存在' if exists else '不存在'}\n")
                
    def run(self):
        """主运行循环"""
        try:
            while self.running:
                try:
                    self.collect_cpu()
                    self.collect_memory()
                    self.collect_disk()
                    self.collect_disk_io()
                    self.collect_network()
                    self.collect_kernel_log()
                    self.collect_specified_files()
                    self.collect_top_processes()
                    self.check_process_exist()
                    time.sleep(1)
                except Exception as e:
                    print(f"Error in main loop: {e}")
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\n正在优雅退出...")
        finally:
            print("监控程序已退出")
            sys.exit(0)

if __name__ == "__main__":
    monitor = SystemMonitor()
    monitor.run()
