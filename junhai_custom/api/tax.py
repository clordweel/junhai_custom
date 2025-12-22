import frappe
from utils.tax_logic import update_item_tax_data


# --- 供按钮调用的函数保持不变，但内部逻辑已更新 ---
@frappe.whitelist()
def sync_group_taxes_to_items(item_group):
    group_info = frappe.db.get_value(
        "Item Group", item_group, ["lft", "rgt"], as_dict=True
    )
    if not group_info:
        return

    descendants = frappe.get_all(
        "Item Group",
        filters={"lft": (">=", group_info.lft), "rgt": ("<=", group_info.rgt)},
    )
    items = frappe.get_all(
        "Item", filters={"item_group": ("in", [d.name for d in descendants])}
    )

    count = 0
    for i in items:
        doc = frappe.get_doc("Item", i.name)
        update_item_tax_data(doc)
        doc.save(ignore_permissions=True)
        count += 1
        if count % 100 == 0:
            frappe.db.commit()

    frappe.db.commit()
    return {"message": f"成功更新了 {count} 个物料的进/销项税率数据"}


@frappe.whitelist()
def bulk_cleanup_tax_templates(keyword="(销项)"):
    """
    修正版：一键清理所有标题包含特定关键字的旧版模板。
    Item Tax 表在数据库中同时服务于 Item 和 Item Group 的税率关联。
    """
    # 查找匹配的模板
    templates = frappe.get_all(
        "Item Tax Template", filters=[["title", "like", f"%{keyword}%"]]
    )

    count = 0
    for t in templates:
        t_name = t.name

        # 1. 核心修复：清理所有引用该模板的子表行
        # 在 ERPNext 中，Item 和 Item Group 的税率子表都存储在 tabItem Tax 表中
        # parenttype 字段会区分它是属于 Item 还是 Item Group
        frappe.db.delete("Item Tax", {"item_tax_template": t_name})

        # 2. 删除模板文档本身
        # 使用 ignore_missing 以防万一某些文档已被手动删除
        frappe.delete_doc("Item Tax Template", t_name, ignore_missing=True)
        count += 1

    frappe.db.commit()
    return {"message": f"成功清理了 {count} 个旧版模板及所有（物料/物料组）关联引用。"}
