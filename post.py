#!/usr/bin/env python3
"""
后处理脚本：为 dist 目录下的编译产物创建 zip 文件
对于 flamegraph 和 cargo-audit，将相关文件打包成 zip 文件
"""

import os
import json
import zipfile
from pathlib import Path
from datetime import datetime

# 目录配置
DIST_DIR = "dist"
TOOLS_CONFIG = "config/tools.toml"
MANIFEST_FILE = "manifest.json"

# 目标平台列表
TARGETS = [
    "x86_64-pc-windows-gnu",
    "x86_64-pc-windows-msvc",
    "aarch64-unknown-linux-gnu",
    "x86_64-unknown-linux-gnu",
]

# 需要打包的工具
PACKAGE_TOOLS = ["flamegraph", "cargo-audit"]


def load_tools_config():
    """加载 tools.toml 配置文件"""
    try:
        # 尝试使用 Python 3.11+ 的 tomllib
        import tomllib
        with open(TOOLS_CONFIG, 'rb') as f:
            return tomllib.load(f)
    except ImportError:
        try:
            # 尝试使用 toml 包
            import toml
            with open(TOOLS_CONFIG, 'r', encoding='utf-8') as f:
                return toml.load(f)
        except ImportError:
            print("警告: 无法加载 tools.toml，将使用默认配置")
            return {'tools': {}}


def get_tool_version(tool_name):
    """获取工具版本"""
    config = load_tools_config()
    return config.get('tools', {}).get(tool_name, {}).get('version', 'unknown')


def create_zip_for_tool(tool_dir, target_dir, target_name):
    """为指定工具创建 zip 文件"""
    tool_name = tool_dir.name
    zip_path = target_dir / f"{tool_name}.zip"
    
    # 查找需要打包的文件
    files_to_zip = []
    for file in target_dir.iterdir():
        if file.is_file() and not file.name.endswith('.zip'):
            # 对于 flamegraph，打包 flamegraph 和 cargo-flamegraph
            # 对于 cargo-audit，打包所有文件
            if tool_name == "flamegraph":
                file_name = file.name
                if file_name.startswith("flamegraph") or file_name.startswith("cargo-flamegraph"):
                    files_to_zip.append(file)
            else:
                # 其他工具打包所有文件
                files_to_zip.append(file)
    
    if not files_to_zip:
        print(f"  ⚠ 警告: {target_dir} 中没有找到需要打包的文件")
        return
    
    # 创建 zip 文件
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files_to_zip:
            zipf.write(file, file.name)
            print(f"  ✓ 添加到 zip: {file.name}")
    
    print(f"  ✓ 创建 zip: {zip_path}")
    return zip_path


def get_files_in_directory(directory):
    """获取目录中的所有文件列表"""
    files = []
    if directory.exists():
        for file in directory.iterdir():
            if file.is_file():
                files.append({
                    'name': file.name,
                    'size': file.stat().st_size,
                })
    return files


def process_tool(tool_dir, manifest_data):
    """处理单个工具目录"""
    tool_name = tool_dir.name
    print(f"\n处理工具: {tool_name}")
    
    # 获取工具版本
    version = get_tool_version(tool_name)
    
    # 检查是否是需要打包的工具
    should_package = tool_name in PACKAGE_TOOLS
    
    # 获取现有的目标平台目录
    existing_targets = set()
    for item in tool_dir.iterdir():
        if item.is_dir() and item.name in TARGETS:
            existing_targets.add(item.name)
    
    # 创建缺失的目标平台目录
    missing_targets = set(TARGETS) - existing_targets
    for target_name in missing_targets:
        target_dir = tool_dir / target_name
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ 创建缺失目录: {target_name}")
    
    # 收集工具信息
    tool_info = {
        'crate_name': tool_name,
        'version': version,
        'source': 'crates.io',
        'targets': {}
    }
    
    # 遍历所有目标平台目录
    for target_name in TARGETS:
        target_dir = tool_dir / target_name
        if not target_dir.exists():
            continue
        
        print(f"  目标平台: {target_name}")
        
        # 如果是需要打包的工具，先创建 zip 文件
        if should_package:
            create_zip_for_tool(tool_dir, target_dir, target_name)
        
        # 收集该目标平台的文件列表（包括可能刚创建的 zip 文件）
        files = get_files_in_directory(target_dir)
        tool_info['targets'][target_name] = {
            'files': files
        }
    
    manifest_data['tools'].append(tool_info)


def generate_manifest(manifest_data, dist_path):
    """生成清单文件"""
    manifest_path = dist_path / MANIFEST_FILE
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)
    print(f"\n✓ 生成清单文件: {manifest_path}")


def main():
    """主函数"""
    dist_path = Path(DIST_DIR)
    
    # 检查 dist 目录是否存在
    if not dist_path.exists():
        print(f"错误: {DIST_DIR} 目录不存在")
        return
    
    print(f"开始处理 {DIST_DIR} 目录下的编译产物...")
    print(f"需要打包的工具: {', '.join(PACKAGE_TOOLS)}")
    print("=" * 60)
    
    # 初始化清单数据
    manifest_data = {
        'generated_at': datetime.now().isoformat(),
        'source': 'crates.io',
        'tools': []
    }
    
    # 遍历 dist 目录下的所有工具
    tools_processed = 0
    for tool_dir in dist_path.iterdir():
        if tool_dir.is_dir() and tool_dir.name != MANIFEST_FILE.replace('.json', ''):
            process_tool(tool_dir, manifest_data)
            tools_processed += 1
    
    # 生成清单文件
    generate_manifest(manifest_data, dist_path)
    
    print("=" * 60)
    print(f"处理完成！共处理 {tools_processed} 个工具")


if __name__ == '__main__':
    main()

