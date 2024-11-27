import requests
from bs4 import BeautifulSoup
import hashlib
import json
from datetime import datetime
import os

def get_monitored_urls():
    try:
        urls_file = os.path.join(os.path.dirname(__file__), 'monitored_urls.json')
        with open(urls_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_monitored_urls(urls):
    urls_file = os.path.join(os.path.dirname(__file__), 'monitored_urls.json')
    with open(urls_file, 'w', encoding='utf-8') as f:
        json.dump(urls, f, ensure_ascii=False, indent=2)

def add_monitored_url(url, description=""):
    urls = get_monitored_urls()
    # 检查URL是否已存在
    if not any(u['url'] == url for u in urls):
        urls.append({
            'url': url,
            'description': description,
            'added_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_monitored_urls(urls)
        return True
    return False

def get_page_content(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.encoding = 'utf-8'
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"获取页面失败: {e}")
        return None

def get_content_hash(content):
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def load_history():
    try:
        history_file = os.path.join(os.path.dirname(__file__), 'update_history.json')
        with open(history_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_history(history):
    history_file = os.path.join(os.path.dirname(__file__), 'update_history.json')
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def summarize_changes(added_content, removed_content):
    summary = []
    if added_content:
        summary.append(f"新增内容: {added_content[0][:100]}...")
    if removed_content:
        summary.append(f"删除内容: {removed_content[0][:100]}...")
    return ' | '.join(summary) if summary else "内容已更新"

def check_single_url(url):
    # 获取当前页面内容
    current_content = get_page_content(url)
    if current_content is None:
        return {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'url': url,
            'has_update': False,
            'error': True,
            'summary': "获取页面失败",
            'added_content': [],
            'removed_content': []
        }
    
    # 使用BeautifulSoup提取主要内容
    soup = BeautifulSoup(current_content, 'html.parser', from_encoding='utf-8')
    main_content = soup.find('main') or soup.find('article') or soup.body
    
    if main_content:
        current_text = ''
        for element in main_content.descendants:
            if isinstance(element, str) and element.strip():
                current_text += element.strip() + '\n'
    else:
        current_text = ''

    current_hash = get_content_hash(current_text)

    # 读取历史记录
    history = load_history()
    
    # 获取该URL最后一次更新的记录
    last_record = None
    for record in reversed(history):
        if record.get('url') == url:
            last_record = record
            break

    last_hash = last_record.get('hash', '') if last_record else ''
    last_text = last_record.get('content', '') if last_record else ''

    # 比较哈希值
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    has_update = current_hash != last_hash
    
    if has_update:
        # 将文本分割成段落进行比较
        last_paragraphs = [p.strip() for p in last_text.split('\n') if p.strip()]
        current_paragraphs = [p.strip() for p in current_text.split('\n') if p.strip()]
        
        # 使用difflib比较文本差异
        import difflib
        matcher = difflib.SequenceMatcher(None, last_paragraphs, current_paragraphs)
        
        added_content = []
        removed_content = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'insert':
                added_content.extend(current_paragraphs[j1:j2])
            elif tag == 'delete':
                removed_content.extend(last_paragraphs[i1:i2])

    else:
        added_content = []
        removed_content = []

    update_record = {
        'timestamp': current_time,
        'hash': current_hash,
        'content': current_text,
        'has_update': has_update,
        'added_content': added_content,
        'removed_content': removed_content,
        'summary': summarize_changes(added_content, removed_content) if has_update else "无更新",
        'url': url,
        'error': False
    }
    
    history.append(update_record)
    save_history(history)
    return update_record

def check_for_update():
    urls = get_monitored_urls()
    results = []
    
    for url_info in urls:
        url = url_info['url']
        print(f"\n检查网址: {url}")
        result = check_single_url(url)
        results.append(result)
        
        if result['error']:
            print(f"错误: {result['summary']}")
        elif result['has_update']:
            print(f"[{result['timestamp']}] 页面有更新！")
            print(f"更新摘要: {result['summary']}")
        else:
            print("页面没有更新。")
    
    return results

if __name__ == "__main__":
    check_for_update()