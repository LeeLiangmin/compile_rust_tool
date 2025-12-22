
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
    # download rust-analyzer
    python download.py --date 2025-12-15

