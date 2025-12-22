#!/usr/bin/env python3
"""
后处理脚本：将 dist 目录下的编译产物复制到 artifacts 目录
对于 flamegraph 和 cargo-audit，将相关文件打包成 zip 文件
"""

import os
import shutil
import zipfile
from pathlib import Path

# 目录配置
DIST_DIR = "dist"
ARTIFACTS_DIR = "artifacts"

# 需要打包的工具
PACKAGE_TOOLS = ["flamegraph", "cargo-audit"]


def copy_file(src, dst):
    """复制文件，如果目标目录不存在则创建"""
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  ✓ 复制: {src.name} -> {dst}")


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


def process_tool(tool_dir):
    """处理单个工具目录"""
    tool_name = tool_dir.name
    print(f"\n处理工具: {tool_name}")
    
    # 检查是否是需要打包的工具
    should_package = tool_name in PACKAGE_TOOLS
    
    # 遍历所有目标平台目录
    for target_dir in tool_dir.iterdir():
        if not target_dir.is_dir():
            continue
        
        target_name = target_dir.name
        artifacts_target_dir = Path(ARTIFACTS_DIR) / tool_name / target_name
        
        print(f"  目标平台: {target_name}")
        
        # 复制所有文件到 artifacts 目录
        files_copied = []
        for file in target_dir.iterdir():
            if file.is_file():
                dst_file = artifacts_target_dir / file.name
                copy_file(file, dst_file)
                files_copied.append(file)
        
        # 如果是需要打包的工具，创建 zip 文件
        if should_package and files_copied:
            create_zip_for_tool(tool_dir, artifacts_target_dir, target_name)


def main():
    """主函数"""
    dist_path = Path(DIST_DIR)
    artifacts_path = Path(ARTIFACTS_DIR)
    
    # 检查 dist 目录是否存在
    if not dist_path.exists():
        print(f"错误: {DIST_DIR} 目录不存在")
        return
    
    # 确保 artifacts 目录存在
    artifacts_path.mkdir(parents=True, exist_ok=True)
    
    print(f"开始处理 {DIST_DIR} 目录下的编译产物...")
    print(f"目标目录: {ARTIFACTS_DIR}")
    print(f"需要打包的工具: {', '.join(PACKAGE_TOOLS)}")
    print("=" * 60)
    
    # 遍历 dist 目录下的所有工具
    tools_processed = 0
    for tool_dir in dist_path.iterdir():
        if tool_dir.is_dir():
            process_tool(tool_dir)
            tools_processed += 1
    
    print("=" * 60)
    print(f"处理完成！共处理 {tools_processed} 个工具")


if __name__ == '__main__':
    main()

