from flask import Flask, render_template, jsonify
import os
import json
from datetime import datetime

app = Flask(__name__)

def read_last_n_lines(file_path, n=60):
    """读取文件最后n行数据"""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            return lines[-n:] if len(lines) > n else lines
    except:
        return []

def parse_disk_io_data(lines):
    """解析磁盘IO数据"""
    data = []
    for line in lines:
        try:
            # 解析时间戳和数据
            parts = line.strip().split(' ')
            timestamp = ' '.join(parts[0:2])
            read_mb = float(parts[3].split(':')[1].replace('MB', ''))
            write_mb = float(parts[5].split(':')[1].replace('MB', ''))
            
            data.append({
                'timestamp': timestamp,
                'read_mb': read_mb,
                'write_mb': write_mb
            })
        except:
            continue
    return data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/logs')
def logs():
    result_dir = './result'
    
    # 读取内核日志
    kernel_log = read_last_n_lines(os.path.join(result_dir, 'kernel.txt'), n=100)
    
    # 读取指定的日志文件
    specified_logs = {}
    try:
        with open('./config/collect_files.conf', 'r') as f:
            collect_files = [line.strip() for line in f if line.strip()]
            
        for file_path in collect_files:
            file_name = os.path.basename(file_path)
            log_path = os.path.join(result_dir, f"{file_name}.txt")
            if os.path.exists(log_path):
                specified_logs[file_name] = read_last_n_lines(log_path, n=100)
    except Exception as e:
        print(f"Error reading log files: {e}")
    
    return render_template('logs.html', 
                         kernel_log=kernel_log,
                         specified_logs=specified_logs)

@app.route('/api/system_data')
def get_system_data():
    result_dir = './result'
    
    # 读取各项系统数据
    cpu_data = read_last_n_lines(os.path.join(result_dir, 'cpu.txt'))
    memory_data = read_last_n_lines(os.path.join(result_dir, 'memory.txt'))
    disk_data = read_last_n_lines(os.path.join(result_dir, 'disk.txt'))
    network_data = read_last_n_lines(os.path.join(result_dir, 'network.txt'))
    disk_io_data = parse_disk_io_data(read_last_n_lines(os.path.join(result_dir, 'disk_io.txt')))
    
    return jsonify({
        'cpu': cpu_data,
        'memory': memory_data,
        'disk': disk_data,
        'network': network_data,
        'disk_io': disk_io_data
    })

@app.route('/api/logs')
def get_logs():
    result_dir = './result'
    
    # 读取内核日志
    kernel_logs = read_last_n_lines(os.path.join(result_dir, 'kernel.txt'), n=100)
    
    # 读取指定的日志文件
    specified_logs = {}
    try:
        with open('./config/collect_files.conf', 'r') as f:
            collect_files = [line.strip() for line in f if line.strip()]
            
        for file_path in collect_files:
            file_name = os.path.basename(file_path)
            log_path = os.path.join(result_dir, f"{file_name}.txt")
            if os.path.exists(log_path):
                specified_logs[file_name] = read_last_n_lines(log_path, n=100)
    except Exception as e:
        print(f"Error reading log files: {e}")
    
    return jsonify({
        'kernel_logs': kernel_logs,
        'specified_logs': specified_logs
    })

@app.route('/processes')
def processes():
    return render_template('processes.html')

@app.route('/api/processes')
def get_processes():
    result_dir = './result'
    
    # 读取各类进程信息
    cpu_top = read_last_n_lines(os.path.join(result_dir, 'cpu_top10.pids'), n=11)  # 多读一行因为有空行
    memory_top = read_last_n_lines(os.path.join(result_dir, 'memory_top10.pids'), n=11)
    disk_top = read_last_n_lines(os.path.join(result_dir, 'disk_top10.pids'), n=11)
    network_top = read_last_n_lines(os.path.join(result_dir, 'network_top10.pids'), n=11)
    process_exist = read_last_n_lines(os.path.join(result_dir, 'process_exist.txt'), n=100)
    
    return jsonify({
        'cpu_top': cpu_top,
        'memory_top': memory_top,
        'disk_top': disk_top,
        'network_top': network_top,
        'process_exist': process_exist
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
