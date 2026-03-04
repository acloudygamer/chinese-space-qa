# -*- coding: utf-8 -*-
"""
编码解决方案
解决 Windows 下的 UTF-8 输出问题

使用方式:
    from src._encoding import setup_encoding
    setup_encoding()
"""

import sys
import io


def setup_encoding():
    """设置 UTF-8 编码"""
    try:
        if sys.platform == "win32":
            if hasattr(sys.stdout, "buffer") and sys.stdout.buffer:
                sys.stdout = io.TextIOWrapper(
                    sys.stdout.buffer,
                    encoding="utf-8",
                    line_buffering=True,
                    write_through=True,
                )
    except Exception:
        pass
