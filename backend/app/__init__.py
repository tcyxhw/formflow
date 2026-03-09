import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
import pandas as pd
import re
import os
from dataclasses import dataclass, asdict, field
from typing import List, Optional
from datetime import datetime

OUTPUT_DIR = "yunwu_data"


def setup_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    print("📁 输出目录: " + os.path.abspath(OUTPUT_DIR))


def get_output_path(filename):
    return os.path.join(OUTPUT_DIR, filename)


@dataclass
class ModelInfo:
    model_name: str
    provider: str
    input_price: Optional[float]
    output_price: Optional[float]
    model_price: Optional[float]
    price_unit: str
    currency: str
    description: str
    tags: List[str]
    billing_type: str
    model_multiplier: Optional[float]
    completion_multiplier: Optional[float]
    group_multiplier: Optional[float]


@dataclass
class FilterOption:
    category: str
    name: str
    count: Optional[int]
    multiplier: Optional[str]


async def get_total_model_count(page):
    try:
        js_code = "(() => { const buttons = document.querySelectorAll('button'); for (const btn of buttons) { const text = btn.innerText; if (text.includes('全部') && (text.includes('供应商') || text.includes('标签'))) { const match = text.match(/(\\d+)/); if (match) return parseInt(match[1]); } } return 0; })()"
        count = await page.evaluate(js_code)
        return count if count > 0 else 543
    except:
        return 543


async def expand_all_filters(page):
    print("  🔽 展开所有筛选条件...")
    expanded_count = 0
    max_attempts = 20

    for attempt in range(max_attempts):
        try:
            expand_elements = await page.locator("span:has-text('展开更多')").all()

            if len(expand_elements) == 0:
                break

            for elem in expand_elements:
                try:
                    parent = await elem.locator("..").first
                    await parent.click()
                    expanded_count += 1
                    await page.wait_for_timeout(300)
                except:
                    try:
                        await elem.click()
                        expanded_count += 1
                        await page.wait_for_timeout(300)
                    except:
                        pass

            await page.wait_for_timeout(500)
        except:
            break

    print("  ✅ 已展开筛选条件 (点击了 " + str(expanded_count) + " 次)")


async def set_page_size_to_max(page):
    print("  📐 设置每页显示100条...")
    try:
        await page.locator(".semi-page-switch .semi-select").click()
        await page.wait_for_timeout(800)

        await page.locator(".semi-select-option-list .semi-select-option").last.click()
        await page.wait_for_timeout(2000)

        print("  ✅ 已设置为每页100条")
        return True
    except Exception as e:
        print("  ⚠️ 设置每页条数失败: " + str(e))
        return False


async def count_model_cards(page):
    count = await page.evaluate("""
        (() => {
            let count = 0;
            const cards = document.querySelectorAll('.semi-card');
            cards.forEach(card => {
                const h3 = card.querySelector('h3');
                if (h3 && h3.textContent.trim().length > 0) {
                    const text = card.innerText;
                    if (text.includes('¥') || text.includes('$')) {
                        count++;
                    }
                }
            });
            return count;
        })()
    """)
    return count


async def load_all_pages(page, expected_count):
    all_html_content = []
    total_loaded = 0
    page_num = 1

    await set_page_size_to_max(page)
    await page.wait_for_timeout(2000)

    while True:
        await page.wait_for_timeout(1500)

        current_count = await count_model_cards(page)
        total_loaded += current_count

        print(
            "  📄 第 " + str(page_num) + " 页: " + str(current_count) + " 个模型, 累计 " + str(total_loaded) + "/" + str(
                expected_count))

        content = await page.content()
        all_html_content.append(content)

        next_btn = await page.query_selector("li.semi-page-next:not([aria-disabled='true'])")
        if not next_btn:
            print("  ✅ 已到达最后一页")
            break

        is_disabled = await next_btn.get_attribute("aria-disabled")
        if is_disabled == "true":
            print("  ✅ 已到达最后一页")
            break

        try:
            await next_btn.click()
            await page.wait_for_timeout(2000)
            page_num += 1
        except:
            print("  ⚠️ 翻页失败")
            break

        if page_num > 30:
            print("  ⚠️ 超过30页，停止")
            break

    print("  📊 共 " + str(page_num) + " 页, 累计 " + str(total_loaded) + " 个模型")
    return all_html_content


def parse_model_card(card):
    h3 = card.find("h3")
    if not h3:
        return None

    model_name = h3.get_text(strip=True)
    if not model_name or len(model_name) < 2:
        return None

    card_text = card.get_text()
    if "¥" not in card_text and "$" not in card_text:
        return None

    provider = "Unknown"
    svg = card.find("svg")
    if svg:
        title = svg.find("title")
        if title:
            provider = title.get_text(strip=True)

    input_price = None
    output_price = None
    model_price = None
    price_unit = ""
    currency = "¥"

    input_match = re.search(r"输入[^¥$]*([¥$])([\d.]+)\s*(/\w+)?", card_text)
    if input_match:
        currency = input_match.group(1)
        input_price = float(input_match.group(2))
        if input_match.group(3):
            price_unit = input_match.group(3)

    output_match = re.search(r"输出[^¥$]*([¥$])([\d.]+)\s*(/\w+)?", card_text)
    if output_match:
        output_price = float(output_match.group(2))
        if not price_unit and output_match.group(3):
            price_unit = output_match.group(3)

    model_price_match = re.search(r"模型价格[^¥$]*([¥$])([\d.]+)", card_text)
    if model_price_match:
        currency = model_price_match.group(1)
        model_price = float(model_price_match.group(2))

    description = ""
    desc_row = card.find("div", class_="pricing-desc-row")
    if desc_row:
        p = desc_row.find("p")
        if p:
            description = p.get_text(strip=True)

    tags = []
    tag_elements = card.find_all("div", attrs={"aria-label": True})
    for tag_elem in tag_elements:
        aria = tag_elem.get("aria-label", "")
        if aria.startswith("Tag:"):
            tag_name = aria.replace("Tag:", "").strip()
            if tag_name and "计费" not in tag_name and not tag_name.startswith("x"):
                tags.append(tag_name)

    billing_type = ""
    billing_keywords = ["按量计费", "按次计费", "按张计费", "按像素计费", "分段计费"]
    for kw in billing_keywords:
        if kw in card_text:
            billing_type = kw
            break

    model_multiplier = None
    completion_multiplier = None
    group_multiplier = None

    model_mult_match = re.search(r"模型[：:]\s*([\d.]+)", card_text)
    if model_mult_match:
        model_multiplier = float(model_mult_match.group(1))

    completion_mult_match = re.search(r"补全[：:]\s*([\d.]+)", card_text)
    if completion_mult_match:
        completion_multiplier = float(completion_mult_match.group(1))

    group_mult_match = re.search(r"分组[：:]\s*([\d.]+)", card_text)
    if group_mult_match:
        group_multiplier = float(group_mult_match.group(1))

    return ModelInfo(
        model_name=model_name,
        provider=provider,
        input_price=input_price,
        output_price=output_price,
        model_price=model_price,
        price_unit=price_unit,
        currency=currency,
        description=description,
        tags=tags,
        billing_type=billing_type,
        model_multiplier=model_multiplier,
        completion_multiplier=completion_multiplier,
        group_multiplier=group_multiplier
    )


def extract_models_from_html_list(html_list):
    models = []
    seen = set()

    for idx, html in enumerate(html_list):
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.find_all("div", class_=re.compile(r"semi-card"))

        page_count = 0
        for card in cards:
            model = parse_model_card(card)
            if model and model.model_name not in seen:
                seen.add(model.model_name)
                models.append(model)
                page_count += 1

        print("  🔍 第 " + str(idx + 1) + " 页解析: " + str(page_count) + " 个新模型")

    return models


def extract_filters(soup):
    filters = []

    buttons = soup.find_all("button", class_=re.compile(r"sbg-button"))

    for btn in buttons:
        content = btn.find("div", class_="sbg-content")
        if not content:
            continue

        name_span = content.find("span", class_="sbg-ellipsis")
        if not name_span:
            continue

        name = name_span.get_text(strip=True)
        if not name:
            continue

        category = determine_category(name, btn)

        count = None
        multiplier = None

        tag_div = content.find("div", class_="sbg-tag")
        if tag_div:
            tag_text = tag_div.get_text(strip=True)
            if tag_text.startswith("x"):
                multiplier = tag_text
            else:
                try:
                    count = int(tag_text)
                except:
                    pass

        filters.append(FilterOption(
            category=category,
            name=name,
            count=count,
            multiplier=multiplier
        ))

    return filters


def determine_category(name, button_element):
    parent_text = ""
    try:
        parent = button_element.find_parent("div", class_=re.compile(r"semi-row|filter|section"))
        if parent:
            parent_text = parent.get_text()[:100]
    except:
        pass

    if "供应商" in name or "供应商" in parent_text:
        return "供应商"
    if "标签" in name or "全部标签" in parent_text:
        return "标签"
    if "令牌" in name or "分组" in name or "专属" in name or "Code" in name or "x1." in str(
            button_element) or "x2." in str(button_element):
        return "令牌分组"
    if "计费" in name:
        return "计费类型"

    providers = ["OpenAI", "Claude", "Google", "Anthropic", "Meta", "智谱", "百度", "阿里", "Gemini", "DeepSeek",
                 "Doubao", "Qwen", "Mistral", "Grok", "Replicate", "Ollama", "Spark", "Flux", "Fal", "Jimeng"]
    if name in providers:
        return "供应商"

    tags = ["对话", "识图", "思考", "绘图", "嵌入", "音频", "TTS", "STT", "视频", "向量", "多模态", "工具", "联网",
            "绘画", "文本", "语音", "重排序", "异步", "实时", "弃用", "GPTS"]
    for t in tags:
        if t in name:
            return "标签"

    return "其他"


def save_data(models, filters):
    models_data = [asdict(m) for m in models]
    filters_data = [asdict(f) for f in filters]

    providers_list = sorted(list(set(m.provider for m in models)))
    tags_list = sorted(list(set(tag for m in models for tag in m.tags)))
    billing_list = sorted(list(set(m.billing_type for m in models if m.billing_type)))

    result = {
        "scrape_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "total_models": len(models),
            "total_filters": len(filters),
            "providers": providers_list,
            "all_tags": tags_list,
            "billing_types": billing_list
        },
        "models": models_data,
        "filters": filters_data
    }

    json_path = get_output_path("pricing_data.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("💾 已保存: " + json_path)

    if models:
        try:
            df = pd.DataFrame(models_data)
            df["tags"] = df["tags"].apply(lambda x: ", ".join(x) if x else "")
            csv_path = get_output_path("models.csv")
            df.to_csv(csv_path, index=False, encoding="utf-8-sig")
            print("💾 已保存: " + csv_path)
        except PermissionError:
            backup_path = get_output_path("models_" + datetime.now().strftime("%H%M%S") + ".csv")
            df.to_csv(backup_path, index=False, encoding="utf-8-sig")
            print("💾 已保存备份: " + backup_path)

    if filters:
        try:
            df = pd.DataFrame(filters_data)
            csv_path = get_output_path("filters.csv")
            df.to_csv(csv_path, index=False, encoding="utf-8-sig")
            print("💾 已保存: " + csv_path)
        except PermissionError:
            backup_path = get_output_path("filters_" + datetime.now().strftime("%H%M%S") + ".csv")
            df.to_csv(backup_path, index=False, encoding="utf-8-sig")
            print("💾 已保存备份: " + backup_path)

    save_readme()
    print_analysis(models, filters)


def save_readme():
    lines = [
        "# 云雾AI定价数据字段说明",
        "",
        "## 模型信息字段",
        "",
        "| 字段名 | 类型 | 说明 |",
        "|--------|------|------|",
        "| model_name | string | 模型唯一标识名称 |",
        "| provider | string | 模型供应商 |",
        "| input_price | float/null | 输入价格（按量计费） |",
        "| output_price | float/null | 输出价格（按量计费） |",
        "| model_price | float/null | 模型价格（按次/按张计费） |",
        "| price_unit | string | 价格单位 |",
        "| currency | string | 货币符号 |",
        "| description | string | 模型描述 |",
        "| tags | array | 功能标签 |",
        "| billing_type | string | 计费类型 |",
        "| model_multiplier | float/null | 模型倍率 |",
        "| completion_multiplier | float/null | 补全倍率 |",
        "| group_multiplier | float/null | 分组倍率 |",
        "",
        "## 筛选选项字段",
        "",
        "| 字段名 | 类型 | 说明 |",
        "|--------|------|------|",
        "| category | string | 筛选分类 |",
        "| name | string | 选项名称 |",
        "| count | int/null | 该选项的模型数量 |",
        "| multiplier | string/null | 倍率（如x1.6） |",
    ]

    readme_path = get_output_path("README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("📝 已保存: " + readme_path)


def print_analysis(models, filters):
    print("")
    print("=" * 70)
    print("📊 数据分析结果")
    print("=" * 70)

    print("")
    print("【模型统计】")
    print("  总数: " + str(len(models)))

    providers = sorted(set(m.provider for m in models))
    print("  供应商 (" + str(len(providers)) + "): " + str(providers))

    all_tags = sorted(set(tag for m in models for tag in m.tags))
    print("  标签 (" + str(len(all_tags)) + "): " + str(all_tags))

    billing_types = {}
    for m in models:
        bt = m.billing_type if m.billing_type else "未知"
        billing_types[bt] = billing_types.get(bt, 0) + 1
    print("  计费类型分布:")
    for bt, cnt in sorted(billing_types.items()):
        print("    " + bt + ": " + str(cnt))

    print("")
    print("【筛选选项统计】")
    categories = {}
    for f in filters:
        if f.category not in categories:
            categories[f.category] = []
        categories[f.category].append(f.name)

    for cat, names in categories.items():
        print("  " + cat + " (" + str(len(names)) + "项): " + str(names[:5]) + ("..." if len(names) > 5 else ""))

    print("")
    print("【输出文件】")
    print("  📁 " + os.path.abspath(OUTPUT_DIR))
    print("")
    print("=" * 70)


async def scrape_yunwu_pricing():
    setup_output_dir()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()

        print("🌐 访问 https://yunwu.ai/pricing ...")
        await page.goto("https://yunwu.ai/pricing", wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(3000)

        total_expected = await get_total_model_count(page)
        print("📊 页面显示共 " + str(total_expected) + " 个模型")

        await expand_all_filters(page)
        await page.wait_for_timeout(1000)

        filters_html = await page.content()
        filters_soup = BeautifulSoup(filters_html, "html.parser")
        filters = extract_filters(filters_soup)
        print("✅ 提取到 " + str(len(filters)) + " 个筛选选项")

        print("📜 分页加载模型...")
        all_html = await load_all_pages(page, total_expected)

        await page.screenshot(path=get_output_path("screenshot.png"), full_page=True)
        print("📸 已保存截图")

        await browser.close()

    print("")
    print("🔍 解析模型数据...")
    models = extract_models_from_html_list(all_html)
    print("✅ 共提取 " + str(len(models)) + " 个模型")

    if len(models) < total_expected:
        print("⚠️ 少了 " + str(total_expected - len(models)) + " 个模型")

    save_data(models, filters)

    return models, filters


if __name__ == "__main__":
    print("🚀 开始爬取云雾AI定价页面...")
    print("")
    models, filters = asyncio.run(scrape_yunwu_pricing())
    print("")
    print("✅ 完成!")