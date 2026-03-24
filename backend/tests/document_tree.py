import os


def print_tree(directory, prefix=""):
    """打印目录树状结构"""
    try:
        entries = os.listdir(directory)
    except PermissionError:
        print(f"{prefix}[权限不足]")
        return

    entries.sort()

    for i, entry in enumerate(entries):
        path = os.path.join(directory, entry)
        is_last = i == len(entries) - 1

        # 打印当前项
        connector = "└── " if is_last else "├── "
        print(f"{prefix}{connector}{entry}")

        # 如果是目录，递归打印
        if os.path.isdir(path):
            extension = "    " if is_last else "│   "
            print_tree(path, prefix + extension)


# 使用示例
if __name__ == "__main__":
    folder_path = "../app"  # 当前目录，可以改为任意路径
    # C:\Users\Administrator\Desktop\非作业文件\毕设\formflow\my - app
    print(f"\n{os.path.abspath(folder_path)}")
    print_tree(folder_path)