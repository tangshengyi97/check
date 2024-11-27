from flask import Flask, render_template, request, jsonify
import json
import os
from check_update import check_for_update, add_monitored_url, get_monitored_urls

app = Flask(__name__)

# 修改文件路径到 /tmp 目录，这是 Vercel 环境中可写的目录
HISTORY_FILE = '/tmp/update_history.json'
URLS_FILE = '/tmp/monitored_urls.json'

def ensure_file_exists(file_path, default_content=None):
    """确保文件存在，如果不存在则创建"""
    try:
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_content if default_content is not None else [], f)
    except Exception as e:
        print(f"Error ensuring file exists: {e}")

def load_history():
    try:
        ensure_file_exists(HISTORY_FILE, [])
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)
            return sorted(history, key=lambda x: x['timestamp'], reverse=True)
    except Exception as e:
        print(f"Error loading history: {e}")
        return []

def save_history(history):
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving history: {e}")
        raise

@app.route('/')
def index():
    try:
        history = load_history()
        urls = get_monitored_urls()
        return render_template('index.html', history=history, monitored_urls=urls)
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/add_url', methods=['POST'])
def add_url():
    try:
        url = request.form.get('url')
        description = request.form.get('description', '')
        
        if not url:
            return jsonify({'status': 'error', 'message': '请输入URL'}), 400
            
        if add_monitored_url(url, description):
            return jsonify({'status': 'success', 'message': '添加成功'})
        else:
            return jsonify({'status': 'error', 'message': 'URL已存在'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/check', methods=['POST'])
def check():
    try:
        results = check_for_update()
        return jsonify({'status': 'success', 'message': '检查完成', 'results': results})
    except Exception as e:
        print(f"Check error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/delete_url', methods=['POST'])
def delete_url():
    try:
        url = request.json.get('url')
        if not url:
            return jsonify({'status': 'error', 'message': 'URL不能为空'}), 400
            
        urls = get_monitored_urls()
        urls = [u for u in urls if u['url'] != url]
        
        with open(URLS_FILE, 'w', encoding='utf-8') as f:
            json.dump(urls, f, ensure_ascii=False, indent=2)
            
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
else:
    # 确保文件在应用启动时存在
    ensure_file_exists(HISTORY_FILE, [])
    ensure_file_exists(URLS_FILE, [])
