#!/usr/bin/env python3
"""
批量为使用 @audit_log 装饰器的路由添加 BackgroundTasks 参数

使用方法:
    python scripts/add_background_tasks.py
"""
import re
import os
from pathlib import Path


def add_background_tasks_import(content: str) -> str:
    """添加 BackgroundTasks 导入"""
    # 检查是否已经导入
    if "BackgroundTasks" in content:
        return content
    
    # 查找 fastapi 导入行
    pattern = r'from fastapi import ([^)]+)'
    match = re.search(pattern, content)
    
    if match:
        imports = match.group(1)
        if "BackgroundTasks" not in imports:
            # 添加 BackgroundTasks 到导入列表
            new_imports = imports.rstrip() + ", BackgroundTasks"
            content = content.replace(
                f"from fastapi import {imports}",
                f"from fastapi import {new_imports}"
            )
    
    return content


def add_background_tasks_parameter(content: str) -> str:
    """为使用 @audit_log 的异步函数添加 background_tasks 参数"""
    
    # 查找所有使用 @audit_log 装饰器的函数
    pattern = r'(@audit_log\([^)]+\)\s+async def \w+\([^)]+\):)'
    
    def replace_func(match):
        func_def = match.group(1)
        
        # 检查是否已经有 background_tasks 参数
        if "background_tasks" in func_def.lower():
            return func_def
        
        # 在 db: Session = Depends(get_db) 之前添加 background_tasks 参数
        # 或者在最后一个参数后添加
        if "db: Session = Depends(get_db)" in func_def:
            func_def = func_def.replace(
                "db: Session = Depends(get_db)",
                "background_tasks: BackgroundTasks = BackgroundTasks(),\n    db: Session = Depends(get_db)"
            )
        elif "db = Depends(get_db)" in func_def:
            func_def = func_def.replace(
                "db = Depends(get_db)",
                "background_tasks: BackgroundTasks = BackgroundTasks(),\n    db = Depends(get_db)"
            )
        
        return func_def
    
    content = re.sub(pattern, replace_func, content, flags=re.DOTALL)
    
    return content


def process_file(file_path: Path) -> bool:
    """处理单个文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否使用了 @audit_log
        if "@audit_log" not in content:
            return False
        
        original_content = content
        
        # 添加导入
        content = add_background_tasks_import(content)
        
        # 添加参数
        content = add_background_tasks_parameter(content)
        
        # 如果内容有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 已更新: {file_path}")
            return True
        else:
            print(f"⏭️  跳过（已更新或无需更新）: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ 处理失败 {file_path}: {e}")
        return False


def main():
    """主函数"""
    # 获取 backend/app/api/v1 目录
    api_dir = Path(__file__).parent.parent / "app" / "api" / "v1"
    
    if not api_dir.exists():
        print(f"❌ 目录不存在: {api_dir}")
        return
    
    print(f"📁 扫描目录: {api_dir}\n")
    
    # 需要处理的文件列表
    files_to_process = [
        "forms.py",
        "submissions.py",
        "users.py",
        "upload.py",
        "form_permissions.py",
        "attachments.py",
    ]
    
    updated_count = 0
    
    for filename in files_to_process:
        file_path = api_dir / filename
        if file_path.exists():
            if process_file(file_path):
                updated_count += 1
        else:
            print(f"⚠️  文件不存在: {file_path}")
    
    print(f"\n✨ 完成！共更新 {updated_count} 个文件")


if __name__ == "__main__":
    main()
