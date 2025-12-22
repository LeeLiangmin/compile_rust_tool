# 处理流程
# 1. 安装 target 工具链
# 2. 下载 rust-analyzer
# 3. 编译所有工具
# 4. 后处理, 主要是打包为 zip 文件
# 5. 发布



# Python command based on OS: python3 on Linux, python on Windows
python := if os() == 'windows' { 'python' } else { 'python3' }

# install all toolchains
iat:
    {{python}} build.py install-targets

# install windows toolchains
iwt:
    {{python}} build.py install-windows-targets

# install non-windows toolchains
inwt:
    {{python}} build.py install-non-windows-targets





# build all
ba:
    {{python}} build.py build-all


# build windows
bw:
    {{python}} build.py build-windows

# build non-windows
bnw:
    {{python}} build.py build-non-windows



clean:
    rm -rf dist


post:
    {{python}} post.py


download:
    # download rust-analyzer, mingw 
    python download.py 




