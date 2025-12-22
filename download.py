#!/usr/bin/env python3
"""
下载脚本：从 GitHub releases 下载文件
支持从 download.toml 配置文件读取下载任务
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# 配置
DIST_DIR = "dist"
DOWNLOAD_CONFIG = "config/download.toml"


def load_download_config():
    """加载 download.toml 配置文件"""
    try:
        # 尝试使用 Python 3.11+ 的 tomllib
        import tomllib
        with open(DOWNLOAD_CONFIG, 'rb') as f:
            return tomllib.load(f)
    except ImportError:
        try:
            # 尝试使用 toml 包
            import toml
            with open(DOWNLOAD_CONFIG, 'r', encoding='utf-8') as f:
                return toml.load(f)
        except ImportError:
            print("错误: 需要 tomllib (Python 3.11+) 或 toml 包")
            print("安装 toml 包: pip install toml")
            sys.exit(1)
    except FileNotFoundError:
        print(f"错误: 找不到配置文件 {DOWNLOAD_CONFIG}")
        sys.exit(1)


def fetch_json(url):
    """获取 JSON 数据"""
    try:
        req = Request(url)
        req.add_header('Accept', 'application/vnd.github.v3+json')
        req.add_header('User-Agent', 'Python-download-script')
        
        with urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except HTTPError as e:
        print(f"HTTP 错误: {e.code} - {e.reason}")
        return None
    except URLError as e:
        print(f"URL 错误: {e.reason}")
        return None
    except Exception as e:
        print(f"错误: {e}")
        return None


def get_release_by_date(repo, date_str):
    """根据日期获取 release"""
    api_url = f"https://api.github.com/repos/{repo}/releases"
    
    releases = fetch_json(api_url)
    if not releases:
        return None
    
    try:
        # 解析日期
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # 查找匹配日期的 release
        for release in releases:
            published_at = datetime.strptime(
                release['published_at'], 
                "%Y-%m-%dT%H:%M:%SZ"
            ).date()
            
            if published_at == target_date:
                return release
        
        print(f"警告: 未找到 {date_str} 日期的 release")
        print("可用的 releases:")
        for release in releases[:10]:  # 显示前10个
            published_at = datetime.strptime(
                release['published_at'], 
                "%Y-%m-%dT%H:%M:%SZ"
            ).date()
            print(f"  - {release['tag_name']}: {published_at}")
        
        return None
        
    except Exception as e:
        print(f"错误: {e}")
        return None


def get_release_by_tag(repo, tag):
    """根据标签获取 release"""
    api_url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
    return fetch_json(api_url)


def get_latest_release(repo):
    """获取最新 release"""
    api_url = f"https://api.github.com/repos/{repo}/releases/latest"
    return fetch_json(api_url)


def find_asset_url(release, filename):
    """在 release 中查找指定的 asset URL"""
    if not release or 'assets' not in release:
        return None
    
    for asset in release['assets']:
        if asset['name'] == filename:
            return asset['browser_download_url']
    
    print(f"错误: 在 release {release.get('tag_name', 'unknown')} 中未找到 {filename}")
    print("可用的 assets:")
    for asset in release['assets']:
        print(f"  - {asset['name']}")
    
    return None


def download_file(url, output_path):
    """下载文件"""
    try:
        print(f"正在下载: {url}")
        
        req = Request(url)
        req.add_header('User-Agent', 'Python-download-script')
        
        # 创建输出目录
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with urlopen(req) as response:
            # 获取文件大小
            total_size = int(response.headers.get('Content-Length', 0))
            
            # 下载文件
            downloaded = 0
            chunk_size = 8192
            
            with open(output_path, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r  进度: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='', flush=True)
        
        print(f"\n  ✓ 下载完成: {output_path}")
        return True
        
    except HTTPError as e:
        print(f"\n错误: HTTP 错误 {e.code} - {e.reason}")
        return False
    except URLError as e:
        print(f"\n错误: URL 错误 - {e.reason}")
        return False
    except Exception as e:
        print(f"\n错误: {e}")
        return False


def download_item(item_name, item_config):
    """下载单个配置项"""
    print(f"\n处理下载项: {item_name}")
    print(f"  Repository: {item_config.get('repo', 'unknown')}")
    print(f"  文件: {item_config.get('file', 'unknown')}")
    
    repo = item_config.get('repo')
    filename = item_config.get('file')
    output_dir = item_config.get('output_dir', item_name)
    method = item_config.get('method', 'latest')
    
    if not repo or not filename:
        print(f"  错误: 配置项 {item_name} 缺少 repo 或 file 字段")
        return False
    
    # 获取 release
    release = None
    if method == 'latest':
        release = get_latest_release(repo)
        if release:
            print(f"  找到最新 release: {release['tag_name']}")
        else:
            print(f"  错误: 无法获取最新 release")
            return False
    elif method == 'date':
        date_str = item_config.get('date')
        if not date_str:
            print(f"  错误: method 为 date 但未提供 date 字段")
            return False
        release = get_release_by_date(repo, date_str)
        if release:
            print(f"  找到 release: {release['tag_name']} (发布于 {date_str})")
    elif method == 'tag':
        tag = item_config.get('tag')
        if not tag:
            print(f"  错误: method 为 tag 但未提供 tag 字段")
            return False
        release = get_release_by_tag(repo, tag)
        if release:
            print(f"  找到 release: {release['tag_name']}")
    else:
        print(f"  错误: 未知的 method: {method}")
        return False
    
    if not release:
        print(f"  错误: 未找到指定的 release")
        return False
    
    # 查找下载 URL
    download_url = find_asset_url(release, filename)
    if not download_url:
        return False
    
    # 下载文件
    output_path = Path(DIST_DIR) / output_dir / filename
    print(f"  目标文件: {output_path}")
    
    if download_file(download_url, output_path):
        print(f"  ✓ 成功下载到: {output_path}")
        return True
    else:
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='从 GitHub releases 下载文件（支持配置文件）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python download.py                    # 下载所有配置项
  python download.py rust-analyzer      # 下载指定项
  python download.py --list              # 列出所有配置项
        """
    )
    
    parser.add_argument('item', nargs='?', help='要下载的配置项名称（不指定则下载所有）')
    parser.add_argument('--list', action='store_true', help='列出所有配置项')
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_download_config()
    downloads = config.get('downloads', {})
    
    if args.list:
        print("可用的下载项:")
        for item_name, item_config in downloads.items():
            repo = item_config.get('repo', 'unknown')
            file = item_config.get('file', 'unknown')
            method = item_config.get('method', 'latest')
            print(f"  - {item_name}: {repo} / {file} (method: {method})")
        return
    
    if args.item:
        # 下载指定项
        if args.item not in downloads:
            print(f"错误: 未找到配置项 '{args.item}'")
            print("使用 --list 查看所有可用项")
            sys.exit(1)
        
        success = download_item(args.item, downloads[args.item])
        sys.exit(0 if success else 1)
    else:
        # 下载所有项
        print(f"开始下载所有配置项...")
        print("=" * 60)
        
        success_count = 0
        fail_count = 0
        
        for item_name, item_config in downloads.items():
            if download_item(item_name, item_config):
                success_count += 1
            else:
                fail_count += 1
        
        print("=" * 60)
        print(f"下载完成！成功: {success_count}, 失败: {fail_count}")


if __name__ == '__main__':
    main()
