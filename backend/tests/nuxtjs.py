# fetch_nuxt_modules.py
import requests
import json
from datetime import datetime
from collections import defaultdict

# Nuxt 官方模块数据源
MODULES_URL = 'https://api.nuxt.com/modules'


def fetch_modules():
    """获取模块数据"""
    print('🔍 正在获取 Nuxt.js 模块数据...')
    try:
        response = requests.get(MODULES_URL, timeout=30)
        response.raise_for_status()
        data = response.json()

        # 检查数据格式
        if isinstance(data, dict):
            # 如果返回的是字典，可能模块数据在某个key下
            if 'modules' in data:
                modules = data['modules']
            elif 'data' in data:
                modules = data['data']
            else:
                # 打印可用的keys
                print(f'⚠️  返回的是字典，可用的keys: {list(data.keys())}')
                modules = data
        elif isinstance(data, list):
            modules = data
        else:
            print(f'⚠️  未知的数据格式: {type(data)}')
            modules = data

        print(f'✅ 成功获取 {len(modules) if isinstance(modules, list) else "未知数量"} 个模块')
        print(f'📝 数据类型: {type(modules)}')

        # 打印第一个元素的结构以便调试
        if isinstance(modules, list) and len(modules) > 0:
            print(f'📝 第一个元素类型: {type(modules[0])}')
            if isinstance(modules[0], dict):
                print(f'📝 第一个元素的keys: {list(modules[0].keys())[:10]}')
            else:
                print(f'📝 第一个元素内容: {modules[0][:100] if isinstance(modules[0], str) else modules[0]}')

        print()
        return modules
    except Exception as e:
        print(f'❌ 获取失败: {e}')
        import traceback
        traceback.print_exc()
        return None


def organize_modules(modules):
    """整理模块数据"""
    print('📋 正在整理数据...')

    # 验证数据格式
    if not isinstance(modules, list):
        print(f'❌ 错误: modules 不是列表类型，而是 {type(modules)}')
        return None

    if len(modules) == 0:
        print('❌ 错误: modules 列表为空')
        return None

    organized = {
        'by_category': defaultdict(list),
        'statistics': {
            'total': len(modules),
            'categories': {},
            'types': {}
        }
    }

    for idx, module in enumerate(modules):
        # 检查每个module是否是字典
        if not isinstance(module, dict):
            print(f'⚠️  跳过第 {idx} 个元素，类型为 {type(module)}: {module}')
            continue

        # 提取关键信息，使用更安全的方式
        module_info = {
            'name': module.get('name', module.get('title', f'未命名-{idx}')),
            'npm': module.get('npm', module.get('package', '')),
            'description': module.get('description', module.get('desc', '')),
            'category': module.get('category', module.get('type', 'Uncategorized')),
            'type': module.get('type', 'community'),
            'repo': module.get('repo', module.get('repository', '')),
            'website': module.get('website', module.get('url', '')),
            'stars': module.get('stars', module.get('github_stars', 0)),
            'downloads': module.get('downloads', module.get('npm_downloads', 0)),
            'tags': module.get('tags', module.get('keywords', []))
        }

        # 确保 tags 是列表
        if not isinstance(module_info['tags'], list):
            module_info['tags'] = []

        # 确保数字类型
        try:
            module_info['stars'] = int(module_info['stars']) if module_info['stars'] else 0
            module_info['downloads'] = int(module_info['downloads']) if module_info['downloads'] else 0
        except (ValueError, TypeError):
            module_info['stars'] = 0
            module_info['downloads'] = 0

        # 按分类整理
        category = module_info['category']
        organized['by_category'][category].append(module_info)

        # 统计
        organized['statistics']['categories'][category] = \
            organized['statistics']['categories'].get(category, 0) + 1

        module_type = module_info['type']
        organized['statistics']['types'][module_type] = \
            organized['statistics']['types'].get(module_type, 0) + 1

    # 转换 defaultdict 为 dict 并排序
    organized['by_category'] = dict(organized['by_category'])

    # 对每个分类按 stars 排序
    for category in organized['by_category']:
        organized['by_category'][category].sort(
            key=lambda x: x['stars'],
            reverse=True
        )

    print('✅ 数据整理完成\n')
    return organized


def save_raw_json(modules):
    """保存原始 JSON 数据"""
    with open('nuxt-modules-raw.json', 'w', encoding='utf-8') as f:
        json.dump(modules, f, ensure_ascii=False, indent=2)
    print('✅ 原始数据已保存到: nuxt-modules-raw.json')


def save_organized_json(organized):
    """保存整理后的 JSON 数据"""
    with open('nuxt-modules-organized.json', 'w', encoding='utf-8') as f:
        json.dump(organized, f, ensure_ascii=False, indent=2)
    print('✅ 整理数据已保存到: nuxt-modules-organized.json')


def generate_markdown_report(organized):
    """生成 Markdown 报告"""
    lines = []

    # 标题和时间
    lines.append('# Nuxt.js Modules 整理报告\n')
    lines.append(f'> 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
    lines.append('---\n')

    # 统计信息
    lines.append('## 📊 统计信息\n')
    lines.append(f'- **总模块数**: {organized["statistics"]["total"]}')
    lines.append(f'- **分类数量**: {len(organized["by_category"])}\n')

    # 按类型统计
    if organized['statistics']['types']:
        lines.append('### 📌 按类型统计\n')
        for type_name, count in sorted(organized['statistics']['types'].items(),
                                       key=lambda x: x[1], reverse=True):
            lines.append(f'- **{type_name}**: {count} 个模块')
        lines.append('')

    # 按分类统计
    lines.append('### 📌 按分类统计\n')
    sorted_categories = sorted(
        organized['statistics']['categories'].items(),
        key=lambda x: x[1],
        reverse=True
    )
    for category, count in sorted_categories:
        lines.append(f'- **{category}**: {count} 个模块')

    lines.append('\n---\n')

    # 详细分类列表
    lines.append('## 📦 分类详细列表\n')

    for category, modules in sorted(organized['by_category'].items(),
                                    key=lambda x: len(x[1]),
                                    reverse=True):
        lines.append(f'### {category} ({len(modules)} 个模块)\n')

        for idx, module in enumerate(modules, 1):
            lines.append(f'#### {idx}. {module["name"]}\n')

            if module['npm']:
                lines.append(f'- **NPM**: `{module["npm"]}`')

            if module['description']:
                lines.append(f'- **描述**: {module["description"]}')

            if module['stars'] > 0:
                lines.append(f'- **⭐ Stars**: {module["stars"]:,}')

            if module['downloads'] > 0:
                lines.append(f'- **📥 下载量**: {module["downloads"]:,}')

            if module['repo']:
                lines.append(f'- **仓库**: {module["repo"]}')

            if module['website']:
                lines.append(f'- **官网**: {module["website"]}')

            if module['tags']:
                lines.append(f'- **标签**: `{", ".join(module["tags"])}`')

            lines.append('')

        lines.append('')

    # Top 模块
    lines.append('---\n')
    lines.append('## ⭐ 热门模块 Top 20\n')

    all_modules = []
    for modules in organized['by_category'].values():
        all_modules.extend(modules)

    top_modules = sorted(all_modules, key=lambda x: x['stars'], reverse=True)[:20]

    if top_modules:
        lines.append('| 排名 | 模块名 | 分类 | Stars | 下载量 |')
        lines.append('|------|--------|------|-------|--------|')

        for idx, module in enumerate(top_modules, 1):
            lines.append(f'| {idx} | {module["name"]} | {module["category"]} | '
                         f'{module["stars"]:,} | {module["downloads"]:,} |')
    else:
        lines.append('暂无数据')

    # 保存文件
    with open('nuxt-modules-report.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print('✅ Markdown报告已保存到: nuxt-modules-report.md')


def print_summary(organized):
    """打印摘要信息"""
    print('\n' + '=' * 60)
    print('📊 数据摘要')
    print('=' * 60)
    print(f'总模块数: {organized["statistics"]["total"]}\n')

    print('分类分布:')
    sorted_categories = sorted(
        organized['statistics']['categories'].items(),
        key=lambda x: x[1],
        reverse=True
    )
    for category, count in sorted_categories:
        print(f'  • {category}: {count} 个')

    # 热门模块
    all_modules = []
    for modules in organized['by_category'].values():
        all_modules.extend(modules)

    if all_modules:
        print('\n⭐ 热门模块 Top 5:')
        top_5 = sorted(all_modules, key=lambda x: x['stars'], reverse=True)[:5]
        for idx, module in enumerate(top_5, 1):
            if module['stars'] > 0:
                print(f'  {idx}. {module["name"]} - ⭐ {module["stars"]:,} stars')
            else:
                print(f'  {idx}. {module["name"]}')

    print('\n' + '=' * 60)


def main():
    """主函数"""
    print('\n' + '=' * 60)
    print('Nuxt.js Modules 数据获取工具')
    print('=' * 60 + '\n')

    # 1. 获取数据
    modules = fetch_modules()
    if not modules:
        print('❌ 无法获取数据，程序退出')
        return

    # 2. 整理数据
    organized = organize_modules(modules)
    if not organized:
        print('❌ 数据整理失败，程序退出')
        return

    # 3. 保存文件
    save_raw_json(modules)
    save_organized_json(organized)
    generate_markdown_report(organized)

    # 4. 打印摘要
    print_summary(organized)

    print('\n✨ 所有任务完成！\n')


if __name__ == '__main__':
    main()