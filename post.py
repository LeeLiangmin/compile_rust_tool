#!/usr/bin/env python3
"""
后处理脚本：为 dist 目录下的编译产物创建压缩文件
根据 tools.toml 配置决定是否压缩以及压缩格式
"""

import os
import json
import zipfile
import tarfile
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

# Windows 目标平台列表
WINDOWS_TARGETS = [
    "x86_64-pc-windows-gnu",
    "x86_64-pc-windows-msvc",
]

# 非 Windows 目标平台列表（Linux）
NON_WINDOWS_TARGETS = [
    "aarch64-unknown-linux-gnu",
    "x86_64-unknown-linux-gnu",
]


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


def get_tool_compress_config(tool_name):
    """获取工具的压缩配置"""
    config = load_tools_config()
    tool_config = config.get('tools', {}).get(tool_name, {})
    return {
        'compress': tool_config.get('compress', False),  # 默认不压缩
        'windows_format': tool_config.get('windows_format', 'zip'),  # 默认 zip
        'non_windows_format': tool_config.get('non_windows_format', 'tar.gz'),  # 默认 tar.gz
    }


def is_windows_target(target_name):
    """判断目标平台是否为 Windows"""
    return target_name in WINDOWS_TARGETS


def get_files_to_compress(tool_dir, target_dir, tool_name):
    """获取需要压缩的文件列表"""
    files_to_compress = []
    # 排除已有的压缩文件
    compressed_extensions = ['.zip', '.7z', '.tar.gz', '.tar.xz', '.tar.bz2', '.tgz', '.txz', '.tbz2']
    
    for file in target_dir.iterdir():
        if file.is_file():
            # 检查是否是压缩文件
            is_compressed = any(file.name.endswith(ext) for ext in compressed_extensions)
            if not is_compressed:
                # 对于 flamegraph，打包 flamegraph 和 cargo-flamegraph
                # 对于其他工具，打包所有文件
                if tool_name == "flamegraph":
                    file_name = file.name
                    if file_name.startswith("flamegraph") or file_name.startswith("cargo-flamegraph"):
                        files_to_compress.append(file)
                else:
                    # 其他工具打包所有文件
                    files_to_compress.append(file)
    
    return files_to_compress


def create_zip_archive(tool_name, target_dir, files_to_compress):
    """创建 ZIP 压缩文件"""
    zip_path = target_dir / f"{tool_name}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files_to_compress:
            zipf.write(file, file.name)
            print(f"  ✓ 添加到 zip: {file.name}")
    print(f"  ✓ 创建 zip: {zip_path}")
    return zip_path


def create_7z_archive(tool_name, target_dir, files_to_compress):
    """创建 7Z 压缩文件（需要 py7zr 库）"""
    try:
        import py7zr
    except ImportError:
        print(f"  ⚠ 警告: 需要 py7zr 库来创建 7z 文件，回退到 zip 格式")
        return create_zip_archive(tool_name, target_dir, files_to_compress)
    
    zip_path = target_dir / f"{tool_name}.7z"
    with py7zr.SevenZipFile(zip_path, 'w') as archive:
        for file in files_to_compress:
            archive.write(file, file.name)
            print(f"  ✓ 添加到 7z: {file.name}")
    print(f"  ✓ 创建 7z: {zip_path}")
    return zip_path


def create_tar_gz_archive(tool_name, target_dir, files_to_compress):
    """创建 tar.gz 压缩文件"""
    tar_path = target_dir / f"{tool_name}.tar.gz"
    with tarfile.open(tar_path, 'w:gz') as tar:
        for file in files_to_compress:
            tar.add(file, arcname=file.name)
            print(f"  ✓ 添加到 tar.gz: {file.name}")
    print(f"  ✓ 创建 tar.gz: {tar_path}")
    return tar_path


def create_tar_xz_archive(tool_name, target_dir, files_to_compress):
    """创建 tar.xz 压缩文件"""
    tar_path = target_dir / f"{tool_name}.tar.xz"
    with tarfile.open(tar_path, 'w:xz') as tar:
        for file in files_to_compress:
            tar.add(file, arcname=file.name)
            print(f"  ✓ 添加到 tar.xz: {file.name}")
    print(f"  ✓ 创建 tar.xz: {tar_path}")
    return tar_path


def create_tar_bz2_archive(tool_name, target_dir, files_to_compress):
    """创建 tar.bz2 压缩文件"""
    tar_path = target_dir / f"{tool_name}.tar.bz2"
    with tarfile.open(tar_path, 'w:bz2') as tar:
        for file in files_to_compress:
            tar.add(file, arcname=file.name)
            print(f"  ✓ 添加到 tar.bz2: {file.name}")
    print(f"  ✓ 创建 tar.bz2: {tar_path}")
    return tar_path


def create_compressed_archive(tool_dir, target_dir, target_name, compress_format):
    """根据指定格式创建压缩文件"""
    tool_name = tool_dir.name
    
    # 获取需要压缩的文件
    files_to_compress = get_files_to_compress(tool_dir, target_dir, tool_name)
    
    if not files_to_compress:
        print(f"  ⚠ 警告: {target_dir} 中没有找到需要打包的文件")
        return None
    
    # 根据格式创建压缩文件
    if compress_format == 'zip':
        return create_zip_archive(tool_name, target_dir, files_to_compress)
    elif compress_format == '7z':
        return create_7z_archive(tool_name, target_dir, files_to_compress)
    elif compress_format == 'tar.gz':
        return create_tar_gz_archive(tool_name, target_dir, files_to_compress)
    elif compress_format == 'tar.xz':
        return create_tar_xz_archive(tool_name, target_dir, files_to_compress)
    elif compress_format == 'tar.bz2':
        return create_tar_bz2_archive(tool_name, target_dir, files_to_compress)
    else:
        print(f"  ⚠ 警告: 不支持的压缩格式: {compress_format}，跳过压缩")
        return None


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
    
    # 获取压缩配置
    compress_config = get_tool_compress_config(tool_name)
    should_compress = compress_config['compress']
    
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
        
        # 如果需要压缩，根据目标平台类型选择压缩格式
        if should_compress:
            if is_windows_target(target_name):
                compress_format = compress_config['windows_format']
            else:
                compress_format = compress_config['non_windows_format']
            
            print(f"  压缩格式: {compress_format}")
            create_compressed_archive(tool_dir, target_dir, target_name, compress_format)
        
        # 收集该目标平台的文件列表（包括可能刚创建的压缩文件）
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

