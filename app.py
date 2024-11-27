from flask import Flask, render_template, request, jsonify
import json
import os
from check_update import check_for_update, add_monitored_url, get_monitored_urls

app = Flask(__name__)

def load_history():
    try:
        history_file = os.path.join(os.path.dirname(__file__), 'update_history.json')
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
            # 按时间戳倒序排序
            return sorted(history, key=lambda x: x['timestamp'], reverse=True)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

@app.route('/')
def index():
    history = load_history()
    urls = get_monitored_urls()
    return render_template('index.html', history=history, monitored_urls=urls)

@app.route('/add_url', methods=['POST'])
def add_url():
    url = request.form.get('url')
    description = request.form.get('description', '')
    
    if not url:
        return jsonify({'status': 'error', 'message': '请输入URL'}), 400
        
    if add_monitored_url(url, description):
        return jsonify({'status': 'success', 'message': '添加成功'})
    else:
        return jsonify({'status': 'error', 'message': 'URL已存在'}), 400

@app.route('/check', methods=['POST'])
def check():
    results = check_for_update()
    return jsonify({'status': 'success', 'message': '检查完成', 'results': results})

@app.route('/delete_url', methods=['POST'])
def delete_url():
    try:
        url = request.json.get('url')
        urls_file = os.path.join(os.path.dirname(__file__), 'monitored_urls.json')
        with open(urls_file, 'r') as f:
            urls = json.load(f)
        
        # Remove the URL from the list
        urls = [u for u in urls if u['url'] != url]
        
        with open(urls_file, 'w') as f:
            json.dump(urls, f, indent=4)
            
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

if __name__ == '__main__':
    app.run()
else:
    # For Vercel deployment
    app = app
