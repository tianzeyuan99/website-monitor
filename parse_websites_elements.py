#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国海油企业安全浏览器网站监测脚本
使用 Playwright 解析网站元素，提取页面标题、文本、链接、图片等信息
支持使用 Microsoft Edge 或中国海油企业安全浏览器（无头模式）

浏览器优先级：
1. Microsoft Edge（优先）
2. 中国海油企业安全浏览器（如果检测不到 Edge）
3. Chromium（如果都检测不到）

使用方法：
1. 安装依赖：pip install playwright
2. 安装浏览器：playwright install msedge（可选）
3. 运行脚本：python parse_websites_elements.py

配置浏览器路径（可选）：
- Microsoft Edge：
  Windows: set EDGE_BROWSER_PATH=C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe
  macOS/Linux: export EDGE_BROWSER_PATH='/path/to/msedge'
  
- 中国海油企业安全浏览器：
  Windows: set CNOOC_BROWSER_PATH=C:\\Program Files\\中国海油企业安全浏览器\\chrome.exe
  macOS/Linux: export CNOOC_BROWSER_PATH='/path/to/企业安全浏览器'

如果未配置，脚本将自动检测并使用系统安装的浏览器。
"""

from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
import json
import time
import os
from datetime import datetime
import asyncio
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# 网站列表
websites = [
    "cnooccapital.cnooc.com.cn",
    "www.cnooc.com.cn",
    "www.cnoocltd.com",
    "ltd.cnooc.com.cn",
    "gaspower.cnooc.com.cn",
    "www.cosl.com.cn",
    "www.chinabluechem.com.cn",
    "cenertech.cnooc.com.cn",
    "www.cenertech.com",
    "www.cnoocengineering.com",
    "cnoocsafety.cnooc.com.cn",
    "www.trici.com.cn",
    "www.trici.cn",
    "www.zhtrust.com",
    "eei.cnooc.com.cn",
    "cneei.cnooc.com.cn",
]

# 配置选项
LINK_TEST_TIMEOUT = 5000  # 链接测试超时时间（毫秒）
PAGE_LOAD_TIMEOUT = 20000  # 页面加载超时时间（毫秒）
MAX_WORKERS = 5  # 链接测试的并发线程数

def add_protocol(url):
    """为URL添加https://协议前缀"""
    if not url.startswith(('http://', 'https://')):
        return f"https://{url}"
    return url

def test_link_accessibility(context, link_url, timeout=None):
    """测试链接是否可访问（使用新页面）"""
    if timeout is None:
        timeout = LINK_TEST_TIMEOUT
    test_page = None
    try:
        # 在新页面中测试链接
        test_page = context.new_page()
        response = test_page.goto(link_url, wait_until='domcontentloaded', timeout=timeout)
        status_code = response.status if response else None
        
        # 检查状态码
        if status_code and 200 <= status_code < 400:
            return {'accessible': True, 'status_code': status_code, 'error': None, 'is_download': False}
        else:
            return {'accessible': False, 'status_code': status_code, 'error': f'HTTP {status_code}', 'is_download': False}
    except Exception as e:
        error_msg = str(e)
        
        # 检测是否是下载链接（PDF等文件下载）
        if 'Download is starting' in error_msg:
            # 这是下载链接，不是错误，返回skip标记
            return {'accessible': 'skip', 'status_code': None, 'error': None, 'is_download': True}
        
        # 尝试从错误中提取状态码
        status_code = None
        if 'net::ERR' in error_msg or 'Navigation failed' in error_msg:
            # 网络错误
            pass
        return {'accessible': False, 'status_code': status_code, 'error': error_msg[:200], 'is_download': False}
    finally:
        if test_page:
            try:
                test_page.close()
            except:
                pass

def parse_page_elements(page, url):
    """解析页面元素"""
    elements_info = {
        'url': url,
        'title': '',
        'meta_description': '',
        'headings': {},
        'links': [],
        'images': [],
        'text_content': '',
        'link_test_results': {
            'total_tested': 0,
            'accessible_count': 0,
            'inaccessible_count': 0,
            'skipped_count': 0,  # 跳过的下载链接数量
            'inaccessible_links': []
        },
        'parsed_at': datetime.now().isoformat(),
        'status': 'success',
        'error': None
    }
    
    try:
        # 等待页面加载
        page.wait_for_load_state('domcontentloaded', timeout=PAGE_LOAD_TIMEOUT)
        time.sleep(1)  # 等待动态内容加载（减少等待时间）
        
        # 提取页面标题
        try:
            elements_info['title'] = page.title()
        except:
            elements_info['title'] = ''
        
        # 提取meta描述
        try:
            meta_desc = page.locator('meta[name="description"]')
            if meta_desc.count() > 0:
                elements_info['meta_description'] = meta_desc.first.get_attribute('content') or ''
        except:
            pass
        
        # 提取标题标签 (h1-h6)
        try:
            for level in range(1, 7):
                headings = page.locator(f'h{level}').all()
                elements_info['headings'][f'h{level}'] = [
                    h.inner_text().strip() 
                    for h in headings[:10]  # 每个级别最多取10个
                    if h.inner_text().strip()
                ]
        except Exception as e:
            elements_info['error'] = f"提取标题时出错: {str(e)}"
        
        # 提取所有链接
        try:
            links = page.locator('a[href]').all()
            unique_links = set()
            extracted_links = []
            
            for link in links[:100]:  # 最多提取100个链接
                try:
                    href = link.get_attribute('href')
                    text = link.inner_text().strip()
                    if href:
                        # 跳过 javascript:, mailto:, tel: 等特殊链接
                        if href.startswith(('javascript:', 'mailto:', 'tel:', '#', 'void(0)')):
                            continue
                        
                        # 处理相对链接
                        if href.startswith('http'):
                            full_url = href
                        elif href.startswith('/'):
                            # 获取基础URL（协议+域名）
                            parsed = urlparse(url)
                            base_url = f"{parsed.scheme}://{parsed.netloc}"
                            full_url = f"{base_url}{href}"
                        else:
                            full_url = f"{url.rstrip('/')}/{href}"
                        
                        link_info = {
                            'url': full_url,
                            'text': text[:200]  # 限制文本长度
                        }
                        # 去重
                        link_key = full_url.lower()
                        if link_key not in unique_links:
                            unique_links.add(link_key)
                            extracted_links.append(link_info)
                            elements_info['links'].append(link_info)
                except:
                    continue
        except Exception as e:
            if not elements_info['error']:
                elements_info['error'] = f"提取链接时出错: {str(e)}"
        
        # 提取所有图片
        try:
            images = page.locator('img[src]').all()
            unique_images = set()
            for img in images[:50]:  # 最多提取50个图片
                try:
                    src = img.get_attribute('src')
                    alt = img.get_attribute('alt') or ''
                    if src:
                        # 处理相对路径
                        if src.startswith('http'):
                            full_src = src
                        elif src.startswith('/'):
                            full_src = f"{url.rstrip('/')}{src}"
                        else:
                            full_src = f"{url.rstrip('/')}/{src}"
                        
                        img_info = {
                            'src': full_src,
                            'alt': alt[:200]
                        }
                        # 去重
                        if full_src not in unique_images:
                            unique_images.add(full_src)
                            elements_info['images'].append(img_info)
                except:
                    continue
        except Exception as e:
            if not elements_info['error']:
                elements_info['error'] = f"提取图片时出错: {str(e)}"
        
        # 提取主要文本内容（body文本，去除script和style）
        try:
            body_text = page.locator('body').inner_text()
            # 清理文本，去除多余空白
            cleaned_text = ' '.join(body_text.split())[:5000]  # 限制长度
            elements_info['text_content'] = cleaned_text
        except Exception as e:
            if not elements_info['error']:
                elements_info['error'] = f"提取文本内容时出错: {str(e)}"
        
    except Exception as e:
        elements_info['status'] = 'error'
        elements_info['error'] = str(e)
    
    return elements_info

def test_single_link_requests(link_info, timeout):
    """使用 requests 库测试单个链接的可访问性（线程安全）"""
    link_url = link_info['url']
    result = {
        'link_info': link_info,
        'test_result': None,
        'error': None
    }
    
    # 跳过文件下载链接（pdf, jpg, png, jpeg, gif, zip, doc, docx, xls, xlsx 等）
    file_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.zip', '.rar', 
                       '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
                       '.mp4', '.mp3', '.avi', '.mov', '.exe', '.dmg']
    
    # 检查链接是否以文件扩展名结尾（不区分大小写）
    link_lower = link_url.lower()
    if any(link_lower.endswith(ext) for ext in file_extensions):
        result['test_result'] = {
            'accessible': 'skip',
            'status_code': None,
            'error': None,
            'is_download': True
        }
        return result
    
    try:
        # 使用 requests 测试链接（先尝试 HEAD，失败则用 GET）
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # 先尝试 HEAD 请求（更快）
        try:
            response = requests.head(link_url, headers=headers, timeout=timeout/1000, allow_redirects=True, stream=True)
            status_code = response.status_code
        except (requests.exceptions.RequestException, AttributeError):
            # HEAD 失败，改用 GET 请求（更准确，但稍慢）
            response = requests.get(link_url, headers=headers, timeout=timeout/1000, allow_redirects=True, stream=True)
            status_code = response.status_code
        
        # 检查状态码
        if 200 <= status_code < 400:
            result['test_result'] = {
                'accessible': True,
                'status_code': status_code,
                'error': None,
                'is_download': False
            }
        else:
            result['test_result'] = {
                'accessible': False,
                'status_code': status_code,
                'error': f'HTTP {status_code}',
                'is_download': False
            }
    except requests.exceptions.Timeout:
        result['test_result'] = {
            'accessible': False,
            'status_code': None,
            'error': '请求超时',
            'is_download': False
        }
    except requests.exceptions.ConnectionError as e:
        result['test_result'] = {
            'accessible': False,
            'status_code': None,
            'error': f'连接错误: {str(e)[:100]}',
            'is_download': False
        }
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        # 检测是否是下载链接（通过 Content-Type）
        if 'application/pdf' in error_msg.lower() or 'download' in error_msg.lower():
            result['test_result'] = {
                'accessible': 'skip',
                'status_code': None,
                'error': None,
                'is_download': True
            }
        else:
            result['test_result'] = {
                'accessible': False,
                'status_code': None,
                'error': f'请求异常: {error_msg[:100]}',
                'is_download': False
            }
    except Exception as e:
        result['error'] = str(e)
        result['test_result'] = {
            'accessible': False,
            'status_code': None,
            'error': f'测试异常: {str(e)[:100]}',
            'is_download': False
        }
    
    return result

def test_all_links(browser, elements_info):
    """使用多线程测试所有链接的可访问性（链接池模式，使用 requests 库）"""
    links_to_test = elements_info['links']
    total_links = len(links_to_test)
    
    if total_links == 0:
        print("  没有链接需要测试")
        return
    
    print(f"  正在使用 {MAX_WORKERS} 个线程并发测试 {total_links} 个链接（链接池模式，使用 requests 库）...")
    
    elements_info['link_test_results']['total_tested'] = total_links
    
    # 使用线程池并发测试链接
    completed = 0
    lock = threading.Lock()  # 用于线程安全的计数和结果更新
    
    def update_progress():
        nonlocal completed
        with lock:
            completed += 1
            if completed % 10 == 0 or completed == total_links:
                print(f"    测试进度: {completed}/{total_links}")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 将所有链接提交到线程池（链接池）
        future_to_link = {
            executor.submit(test_single_link_requests, link_info, LINK_TEST_TIMEOUT): link_info
            for link_info in links_to_test
        }
        
        # 收集结果
        for future in as_completed(future_to_link):
            link_info = future_to_link[future]
            try:
                result = future.result()
                test_result = result['test_result']
                
                if test_result:
                    # 如果是下载链接，跳过，不记录
                    if test_result.get('is_download') or test_result.get('accessible') == 'skip':
                        with lock:
                            elements_info['link_test_results']['skipped_count'] += 1
                    elif test_result.get('accessible'):
                        with lock:
                            elements_info['link_test_results']['accessible_count'] += 1
                    else:
                        with lock:
                            elements_info['link_test_results']['inaccessible_count'] += 1
                            # 记录无法访问的链接
                            inaccessible_info = {
                                'url': link_info['url'],
                                'text': link_info['text'],
                                'status_code': test_result.get('status_code'),
                                'error': test_result.get('error')
                            }
                            elements_info['link_test_results']['inaccessible_links'].append(inaccessible_info)
                
                update_progress()
                
            except Exception as e:
                # 处理异常
                with lock:
                    elements_info['link_test_results']['inaccessible_count'] += 1
                    elements_info['link_test_results']['inaccessible_links'].append({
                        'url': link_info['url'],
                        'text': link_info['text'],
                        'status_code': None,
                        'error': f'测试异常: {str(e)[:100]}'
                    })
                update_progress()
    
    print(f"    测试完成: 可访问 {elements_info['link_test_results']['accessible_count']} 个, "
          f"不可访问 {elements_info['link_test_results']['inaccessible_count']} 个, "
          f"跳过下载链接 {elements_info['link_test_results']['skipped_count']} 个")

def get_edge_path():
    """获取 Microsoft Edge 浏览器路径"""
    # 首先检查环境变量
    env_path = os.getenv('EDGE_BROWSER_PATH')
    if env_path and os.path.exists(env_path):
        return env_path
    
    # 常见的 Microsoft Edge 安装路径
    possible_paths = []
    
    # Windows 常见路径
    if os.name == 'nt':  # Windows
        possible_paths.extend([
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\Application\msedge.exe"),
        ])
    else:  # macOS/Linux
        possible_paths.extend([
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/usr/bin/microsoft-edge",
            "/usr/bin/msedge",
            "/usr/local/bin/microsoft-edge",
        ])
    
    # 检查常见路径
    for path in possible_paths:
        if path and os.path.exists(path):
            return path
    
    return None

def get_cnooc_browser_path():
    """获取中国海油企业安全浏览器路径"""
    # 首先检查环境变量
    env_path = os.getenv('CNOOC_BROWSER_PATH')
    if env_path and os.path.exists(env_path):
        return env_path
    
    # 常见的中国海油企业安全浏览器安装路径
    possible_paths = []
    
    # Windows 常见路径
    if os.name == 'nt':  # Windows
        username = os.getenv('USERNAME', '')
        possible_paths.extend([
            r"C:\Program Files\中国海油企业安全浏览器\chrome.exe",
            r"C:\Program Files (x86)\中国海油企业安全浏览器\chrome.exe",
            r"C:\Program Files\中国海油企业安全浏览器\中国海油企业安全浏览器.exe",
            r"C:\Program Files (x86)\中国海油企业安全浏览器\中国海油企业安全浏览器.exe",
        ])
        if username:
            possible_paths.extend([
                rf"C:\Users\{username}\AppData\Local\中国海油企业安全浏览器\Application\chrome.exe",
                rf"C:\Users\{username}\AppData\Local\中国海油企业安全浏览器\Application\中国海油企业安全浏览器.exe",
            ])
    else:  # macOS/Linux
        possible_paths.extend([
            "/Applications/中国海油企业安全浏览器.app/Contents/MacOS/中国海油企业安全浏览器",
            "/Applications/中国海油企业安全浏览器.app/Contents/MacOS/Chrome",
            "/usr/bin/中国海油企业安全浏览器",
            "/usr/local/bin/中国海油企业安全浏览器",
        ])
    
    # 检查常见路径
    for path in possible_paths:
        if path and os.path.exists(path):
            return path
    
    return None

# 全局变量，用于存储监测结果
all_results = []

def parse_all_websites():
    """解析所有网站的元素"""
    global all_results
    all_results = []  # 重置结果
    
    print("="*60)
    print("中国海油企业安全浏览器网站监测脚本")
    print("="*60)
    print("正在启动浏览器...")
    
    browser = None
    playwright = None
    browser_name = None
    
    try:
        playwright = sync_playwright().start()
        
        # 第一步：尝试使用 Microsoft Edge 浏览器
        edge_path = get_edge_path()
        
        if edge_path:
            print(f"检测到 Microsoft Edge: {edge_path}")
            print("正在启动 Microsoft Edge（无头模式）...")
            browser = playwright.chromium.launch(
                headless=True,
                executable_path=edge_path
            )
            browser_name = "Microsoft Edge"
            print("✓ 成功启动 Microsoft Edge")
        else:
            # 尝试使用 Playwright 的 msedge channel（如果已安装）
            try:
                print("尝试使用 Playwright 的 Microsoft Edge...")
                browser = playwright.chromium.launch(
                    headless=True,
                    channel='msedge'
                )
                browser_name = "Microsoft Edge"
                print("✓ 成功启动 Microsoft Edge（通过 Playwright channel）")
            except Exception as e:
                print(f"未检测到 Microsoft Edge，尝试使用中国海油企业安全浏览器...")
                
                # 第二步：如果检测不到 Edge，尝试使用中国海油企业安全浏览器
                cnooc_path = get_cnooc_browser_path()
                
                if cnooc_path:
                    print(f"检测到中国海油企业安全浏览器: {cnooc_path}")
                    print("正在启动中国海油企业安全浏览器（无头模式）...")
                    browser = playwright.chromium.launch(
                        headless=True,
                        executable_path=cnooc_path
                    )
                    browser_name = "中国海油企业安全浏览器"
                    print("✓ 成功启动中国海油企业安全浏览器")
                else:
                    # 第三步：如果都检测不到，使用 Chromium
                    print("未检测到中国海油企业安全浏览器，使用 Chromium 浏览器...")
                    print("提示：如需使用指定浏览器，请设置环境变量：")
                    print("  Microsoft Edge: set EDGE_BROWSER_PATH='C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'")
                    print("  企业安全浏览器: set CNOOC_BROWSER_PATH='C:\\Program Files\\中国海油企业安全浏览器\\chrome.exe'")
                    print("正在启动 Chromium 浏览器（无头模式）...")
                    browser = playwright.chromium.launch(headless=True)
                    browser_name = "Chromium"
                    print("✓ 成功启动 Chromium 浏览器")
        
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        
        print(f"\n开始解析 {len(websites)} 个网站...")
        print("="*60)
        
        for i, website in enumerate(websites, 1):
            url = add_protocol(website)
            print(f"\n[{i}/{len(websites)}] 正在解析: {url}")
            
            page = context.new_page()
            try:
                page.goto(url, wait_until='domcontentloaded', timeout=PAGE_LOAD_TIMEOUT)
                elements_info = parse_page_elements(page, url)
                
                # 测试所有链接的可访问性
                if elements_info['links']:
                    test_all_links(None, elements_info)  # browser 参数已不再使用，保留以兼容
                
                all_results.append(elements_info)
                
                # 显示简要信息
                print(f"  ✓ 标题: {elements_info['title'][:60]}")
                print(f"  ✓ 链接数: {len(elements_info['links'])}")
                print(f"  ✓ 图片数: {len(elements_info['images'])}")
                if elements_info['link_test_results']['total_tested'] > 0:
                    print(f"  ✓ 链接测试: 可访问 {elements_info['link_test_results']['accessible_count']} 个, "
                          f"不可访问 {elements_info['link_test_results']['inaccessible_count']} 个, "
                          f"跳过下载 {elements_info['link_test_results']['skipped_count']} 个")
                if elements_info['error']:
                    print(f"  ⚠ 警告: {elements_info['error'][:80]}")
                    
            except Exception as e:
                print(f"  ❌ 错误: {str(e)[:80]}...")
                all_results.append({
                    'url': url,
                    'status': 'error',
                    'error': str(e),
                    'parsed_at': datetime.now().isoformat()
                })
            finally:
                page.close()
                time.sleep(0.5)  # 短暂延迟（减少等待时间）
        
        print("\n" + "="*60)
        print("✓ 所有网站解析完成！")
        print("="*60)
        
        # 汇总并输出所有404链接
        print("\n" + "="*60)
        print("404链接汇总")
        print("="*60)
        
        all_404_links = []
        for result in all_results:
            if result.get('link_test_results', {}).get('inaccessible_links'):
                for link in result['link_test_results']['inaccessible_links']:
                    # 只收集404状态的链接
                    if link.get('status_code') == 404:
                        link['source_url'] = result.get('url', 'N/A')
                        all_404_links.append(link)
        
        if all_404_links:
            print(f"\n共发现 {len(all_404_links)} 个404链接：\n")
            for idx, link in enumerate(all_404_links, 1):
                print(f"{idx}. {link.get('url', 'N/A')}")
                print(f"   来源: {link.get('source_url', 'N/A')}")
                if link.get('text'):
                    print(f"   链接文本: {link.get('text', '')[:80]}")
                print()
        else:
            print("\n✓ 未发现404链接！")
        
        print("="*60)
        
        # 保存404链接到JSON文件（只保存404链接及其来源）
        output_file = f"404_links_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # 构建只包含404链接的JSON结构
        json_data = []
        for link in all_404_links:
            json_data.append({
                'url': link.get('url', 'N/A'),
                'source': link.get('source_url', 'N/A'),
                'text': link.get('text', '')
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        print(f"\n404链接结果已保存到: {output_file}")
        
        # 生成简要报告
        generate_summary_report(all_results)
        
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        print("\n提示：")
        print("  1. 如果提示未安装浏览器，请运行：")
        print("     playwright install msedge")
        print("  2. 如需使用 Microsoft Edge，请设置环境变量：")
        print("     Windows: set EDGE_BROWSER_PATH=C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe")
        print("     macOS/Linux: export EDGE_BROWSER_PATH='/path/to/msedge'")
        print("  3. 如需使用中国海油企业安全浏览器，请设置环境变量：")
        print("     Windows: set CNOOC_BROWSER_PATH=C:\\Program Files\\中国海油企业安全浏览器\\chrome.exe")
        print("     macOS/Linux: export CNOOC_BROWSER_PATH='/path/to/企业安全浏览器'")
        print("  4. 或修改脚本中的 get_edge_path() 或 get_cnooc_browser_path() 函数，添加浏览器路径")
        
    finally:
        if browser:
            try:
                browser.close()
            except:
                pass
        if playwright:
            try:
                playwright.stop()
            except:
                pass

def generate_summary_report(results):
    """生成简要报告"""
    report_file = f"websites_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("网站元素解析摘要报告\n")
        f.write("="*60 + "\n\n")
        
        success_count = sum(1 for r in results if r.get('status') != 'error')
        error_count = len(results) - success_count
        total_links_tested = sum(r.get('link_test_results', {}).get('total_tested', 0) for r in results)
        total_inaccessible = sum(r.get('link_test_results', {}).get('inaccessible_count', 0) for r in results)
        total_skipped = sum(r.get('link_test_results', {}).get('skipped_count', 0) for r in results)
        
        f.write(f"总计网站数: {len(results)}\n")
        f.write(f"成功解析: {success_count}\n")
        f.write(f"解析失败: {error_count}\n")
        f.write(f"总计测试链接数: {total_links_tested}\n")
        f.write(f"不可访问链接数: {total_inaccessible}\n")
        f.write(f"跳过下载链接数: {total_skipped}\n\n")
        
        for i, result in enumerate(results, 1):
            f.write("-"*60 + "\n")
            f.write(f"{i}. {result['url']}\n")
            f.write(f"   状态: {result.get('status', 'unknown')}\n")
            
            if result.get('title'):
                f.write(f"   标题: {result['title'][:100]}\n")
            if result.get('meta_description'):
                f.write(f"   描述: {result['meta_description'][:100]}\n")
            if 'links' in result:
                f.write(f"   链接数: {len(result['links'])}\n")
            if 'images' in result:
                f.write(f"   图片数: {len(result['images'])}\n")
            if result.get('headings'):
                total_headings = sum(len(v) for v in result['headings'].values())
                f.write(f"   标题标签数: {total_headings}\n")
            
            # 链接测试结果
            if result.get('link_test_results', {}).get('total_tested', 0) > 0:
                test_results = result['link_test_results']
                f.write(f"   链接测试结果:\n")
                f.write(f"     总测试数: {test_results['total_tested']}\n")
                f.write(f"     可访问: {test_results['accessible_count']}\n")
                f.write(f"     不可访问: {test_results['inaccessible_count']}\n")
                f.write(f"     跳过下载: {test_results.get('skipped_count', 0)}\n")
                
                # 列出不可访问的链接
                if test_results['inaccessible_links']:
                    f.write(f"   不可访问的链接列表:\n")
                    for inaccessible in test_results['inaccessible_links']:
                        f.write(f"     - {inaccessible['url']}\n")
                        if inaccessible.get('text'):
                            f.write(f"       文本: {inaccessible['text'][:80]}\n")
                        if inaccessible.get('status_code'):
                            f.write(f"       状态码: {inaccessible['status_code']}\n")
                        if inaccessible.get('error'):
                            f.write(f"       错误: {inaccessible['error'][:100]}\n")
            
            if result.get('error'):
                f.write(f"   错误: {result['error'][:100]}\n")
            f.write("\n")
    
    print(f"摘要报告已保存到: {report_file}")

if __name__ == "__main__":
    parse_all_websites()

