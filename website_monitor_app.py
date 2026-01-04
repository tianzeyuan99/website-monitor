#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国海油企业安全浏览器网站监测工具 - Web界面版本
使用 Flask 创建 Web 界面，展示404链接监测结果
"""

from flask import Flask, render_template, jsonify, request
import json
import os
import threading
import time
from datetime import datetime
import sys
import webbrowser

# 导入监测脚本
try:
    from parse_websites_elements import parse_all_websites, all_results as global_results
except ImportError:
    # 如果导入失败，尝试添加当前目录到路径
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from parse_websites_elements import parse_all_websites, all_results as global_results

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# 全局变量存储监测结果
monitoring_status = {
    'is_running': False,
    'progress': 0,
    'total': 16,
    'current_website': '',
    'completed': False,
    'error': None
}

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """获取监测状态"""
    return jsonify(monitoring_status)

@app.route('/api/404links')
def get_404_links():
    """获取404链接列表"""
    try:
        # 查找最新的404链接JSON文件
        json_files = [f for f in os.listdir('.') if f.startswith('404_links_') and f.endswith('.json')]
        if json_files:
            latest_file = sorted(json_files, reverse=True)[0]
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify({
                'success': True,
                'data': data,
                'file': latest_file,
                'count': len(data)
            })
        else:
            return jsonify({
                'success': False,
                'message': '暂无404链接数据',
                'data': [],
                'count': 0
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'读取数据失败: {str(e)}',
            'data': [],
            'count': 0
        })

@app.route('/api/start', methods=['POST'])
def start_monitoring():
    """启动监测"""
    if monitoring_status['is_running']:
        return jsonify({'success': False, 'message': '监测正在进行中，请稍候...'})
    
    def run_monitoring():
        global monitoring_status
        try:
            monitoring_status['is_running'] = True
            monitoring_status['completed'] = False
            monitoring_status['progress'] = 0
            monitoring_status['error'] = None
            monitoring_status['current_website'] = '准备中...'
            
            # 运行监测脚本（在后台线程中运行，避免阻塞）
            parse_all_websites()
            
            monitoring_status['completed'] = True
            monitoring_status['progress'] = monitoring_status['total']
            monitoring_status['current_website'] = '完成'
        except Exception as e:
            monitoring_status['error'] = str(e)
            import traceback
            print(f"监测错误: {traceback.format_exc()}")
        finally:
            monitoring_status['is_running'] = False
    
    thread = threading.Thread(target=run_monitoring)
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': '监测已启动'})

def run_app():
    """运行Flask应用"""
    print("="*60)
    print("中国海油企业安全浏览器网站监测工具")
    print("="*60)
    print("\n正在启动Web服务器...")
    
    # 延迟1.5秒后自动打开浏览器
    def open_browser():
        time.sleep(1.5)
        try:
            webbrowser.open('http://127.0.0.1:5000')
        except:
            pass
    
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    print("\nWeb界面已启动！")
    print("浏览器将自动打开，如果没有自动打开，请手动访问: http://127.0.0.1:5000")
    print("\n按 Ctrl+C 停止服务\n")
    
    app.run(host='127.0.0.1', port=5000, debug=False)

if __name__ == '__main__':
    run_app()

