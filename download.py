#!/usr/bin/env python3
"""
下载脚本：从 GitHub releases 下载 rust-analyzer
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
GITHUB_REPO = "rust-lang/rust-analyzer"
ARTIFACTS_DIR = "artifacts"
TARGET_FILE = "rust-analyzer-win32-x64.vsix"
OUTPUT_DIR = Path(ARTIFACTS_DIR) / "rust-analyzer"


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


def get_release_by_date(date_str):
    """根据日期获取 release"""
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
    
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


def get_release_by_tag(tag):
    """根据标签获取 release"""
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/{tag}"
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


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='从 GitHub releases 下载 rust-analyzer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python download.py --date 2025-12-15
  python download.py --tag 2024-12-15
  python download.py --latest
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--date', help='按发布日期下载 (格式: YYYY-MM-DD)')
    group.add_argument('--tag', help='按标签下载 (例如: 2024-12-15)')
    group.add_argument('--latest', action='store_true', help='下载最新版本')
    
    args = parser.parse_args()
    
    # 获取 release
    release = None
    if args.latest:
        api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        release = fetch_json(api_url)
        if release:
            print(f"找到最新 release: {release['tag_name']}")
        else:
            print("错误: 无法获取最新 release")
            sys.exit(1)
    elif args.date:
        release = get_release_by_date(args.date)
        if release:
            print(f"找到 release: {release['tag_name']} (发布于 {args.date})")
    elif args.tag:
        release = get_release_by_tag(args.tag)
        if release:
            print(f"找到 release: {release['tag_name']}")
    
    if not release:
        print("错误: 未找到指定的 release")
        sys.exit(1)
    
    # 查找下载 URL
    download_url = find_asset_url(release, TARGET_FILE)
    if not download_url:
        sys.exit(1)
    
    # 下载文件
    output_path = OUTPUT_DIR / TARGET_FILE
    print(f"\n目标文件: {output_path}")
    
    if download_file(download_url, output_path):
        print(f"\n✓ 成功下载到: {output_path}")
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()

