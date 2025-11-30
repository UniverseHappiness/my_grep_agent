#!/usr/bin/env python3
"""
运行脚本 - 简化启动
"""
import sys
from pathlib import Path

# 添加src目录到路径
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from grep_agent.__main__ import main

if __name__ == "__main__":
    main()
