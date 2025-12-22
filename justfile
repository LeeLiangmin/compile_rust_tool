# 处理流程
# 1. 安装 target 工具链
# 2. 下载 rust-analyzer
# 3. 编译所有工具
# 4. 后处理, 主要是打包为 zip 文件
# 5. 发布



install-toolchains:
    python build.py install-targets


build-all:
    python build.py build-all


build-windows:
    python build.py build-windows

build-non-windows:
    python build.py build-non-windows


build-grcov:
    python build.py build grcov x86_64-pc-windows-msvc
    python build.py build grcov x86_64-pc-windows-gnu


clean:
    rm -rf dist


post:
    python post.py


download:
    # download rust-analyzer, mingw 
    python download.py 




