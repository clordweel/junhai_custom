import frappe


def rename_uoms():
    """
    批量将英文UOM重命名为中文。
    使用 frappe.rename_doc 可以自动更新所有关联文档。
    """

    # 定义映射关系：{ "旧名称": "新名称" }
    # 注意：确保旧名称是系统里实际存在的ID（大小写敏感）
    uom_mapping = {
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
        "Week": "周",
        "Second": "秒",
    }

    for old_uom, new_uom in uom_mapping.items():
        # 调试：打印当前正在检查什么

        if frappe.db.exists("UOM", old_uom):
            try:
                if frappe.db.exists("UOM", new_uom):
                    frappe.rename_doc("UOM", old_uom, new_uom, merge=True)
                else:
                    frappe.rename_doc("UOM", old_uom, new_uom)
            except Exception as e:
                print(f"❌ 错误: {str(e)}")

    print(">>> UOM 重命名补丁执行完毕。")
