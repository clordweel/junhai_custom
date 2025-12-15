import frappe


def rename_uoms():
    """
    批量将英文UOM重命名为中文。
    使用 frappe.rename_doc 可以自动更新所有关联文档。
    """

    # 定义映射关系：{ "旧名称": "新名称" }
    # 注意：确保旧名称是系统里实际存在的ID（大小写敏感）
    uom_mapping = {
        # === 原有列表 ===
        "Meter": "米",
        "Kilogram": "公斤",
        "Nos": "个",
        "Box": "箱",
        "Set": "套",
        "Pair": "双",
        "Litre": "升",
        "Hour": "小时",
        "Minute": "分钟",
        "Square Meter": "平方米",
        "Cubic Meter": "立方米",
        # === 核心补充 (重工制造) ===
        "Tonne": "吨",  # 钢材、原材料核心单位
        "Metric Ton": "吨",  # 某些系统预设叫 Metric Ton
        "Gram": "克",  # 化学品
        "Millimeter": "毫米",  # 核心尺寸单位
        "Centimeter": "厘米",
        # === 包装形态 ===
        "Roll": "卷",  # 电缆、带钢
        "Drum": "桶",  # 油漆、大桶油
        "Bag": "袋",  # 耐火材料
        "Pack": "包",  # 标准件包
        "Packet": "包",
        "Sheet": "张",  # 板材、砂纸
        "Piece": "件",  # 通用计件
        # === 时间周期 (项目/财务) ===
        "Second": "秒",
        "Day": "天",
        "Week": "周",
        "Month": "月",
        "Year": "年",
        # === 能源 ===
        "Kilowatt Hour": "度",  # 或 千瓦时
    }

    for old_uom, new_uom in uom_mapping.items():
        if frappe.db.exists("UOM", old_uom):
            try:
                if frappe.db.exists("UOM", new_uom):
                    frappe.rename_doc("UOM", old_uom, new_uom, merge=True)
                else:
                    frappe.rename_doc("UOM", old_uom, new_uom)
            except Exception as e:
                print(f"❌ 错误: {str(e)}")

    print(">>> UOM 重命名补丁执行完毕。")
