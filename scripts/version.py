#!/usr/bin/env python3
"""
版本管理脚本 - 用于管理项目版本号和变更日志
"""
import os
import re
import sys
import argparse
from datetime import datetime
from typing import List, Tuple

VERSION_FILE = '../VERSION'
CHANGELOG_FILE = '../CHANGELOG.md'

def read_version() -> str:
    """读取当前版本号"""
    if not os.path.exists(VERSION_FILE):
        return '0.1.0'
        
    with open(VERSION_FILE, 'r', encoding='utf-8') as f:
        return f.read().strip()

def write_version(version: str):
    """写入新版本号
    
    Args:
        version (str): 新版本号
    """
    with open(VERSION_FILE, 'w', encoding='utf-8') as f:
        f.write(version)

def parse_version(version: str) -> Tuple[int, int, int]:
    """解析版本号
    
    Args:
        version (str): 版本号字符串
        
    Returns:
        Tuple[int, int, int]: 主版本号、次版本号、修订号
    """
    match = re.match(r'(\d+)\.(\d+)\.(\d+)', version)
    if not match:
        raise ValueError(f'Invalid version format: {version}')
        
    return tuple(map(int, match.groups()))

def increment_version(current: str, increment: str) -> str:
    """增加版本号
    
    Args:
        current (str): 当前版本号
        increment (str): 增加类型 ('major', 'minor', 或 'patch')
        
    Returns:
        str: 新版本号
    """
    major, minor, patch = parse_version(current)
    
    if increment == 'major':
        return f'{major + 1}.0.0'
    elif increment == 'minor':
        return f'{major}.{minor + 1}.0'
    elif increment == 'patch':
        return f'{major}.{minor}.{patch + 1}'
    else:
        raise ValueError(f'Invalid increment type: {increment}')

def update_changelog(version: str, changes: List[str]):
    """更新变更日志
    
    Args:
        version (str): 新版本号
        changes (List[str]): 变更列表
    """
    if not os.path.exists(CHANGELOG_FILE):
        with open(CHANGELOG_FILE, 'w', encoding='utf-8') as f:
            f.write('# Changelog\n\n')
            
    with open(CHANGELOG_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
        
    date = datetime.now().strftime('%Y-%m-%d')
    new_entry = f'\n## [{version}] - {date}\n\n'
    
    for change in changes:
        new_entry += f'- {change}\n'
        
    insert_pos = content.find('\n## [') if '\n## [' in content else len(content)
    new_content = content[:insert_pos] + new_entry + content[insert_pos:]
    
    with open(CHANGELOG_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Version Management Tool')
    parser.add_argument(
        'increment',
        choices=['major', 'minor', 'patch'],
        help='Version increment type'
    )
    parser.add_argument(
        '-m', '--message',
        action='append',
        help='Change message (can be specified multiple times)'
    )
    
    args = parser.parse_args()
    
    try:
        current_version = read_version()
        new_version = increment_version(current_version, args.increment)
        
        # 更新版本文件
        write_version(new_version)
        
        # 更新变更日志
        if args.message:
            update_changelog(new_version, args.message)
            
        print(f'Successfully updated version from {current_version} to {new_version}')
        return 0
        
    except Exception as e:
        print(f'Error: {str(e)}', file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
