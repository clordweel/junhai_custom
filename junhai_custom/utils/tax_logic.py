import frappe
from frappe import _
from frappe.utils import flt


def update_item_tax_data(doc, method=None):
    """
    更新物料税率：每个公司仅创建一个综合模板，包含进/销项两个科目
    """
    if not doc.item_group:
        return

    tax_rate = get_tax_rate_hierarchy(doc.item_group)
    if tax_rate is None:
        return

    companies = frappe.get_all("Company", filters={"is_group": 0})
    doc.set("taxes", [])

    for c in companies:
        # 创建或获取该公司的“综合税率模板”
        template_name = ensure_combined_tax_template(c.name, tax_rate)
        if template_name:
            doc.append(
                "taxes",
                {
                    "item_tax_template": template_name,
                    "tax_category": "",  # 保持留空，确保普适性
                },
            )

    return True


def ensure_combined_tax_template(company, rate):
    """
    核心优化：创建一个同时包含进项和销项科目的单一模板
    """
    # 标题不再区分进销项，例如：中国增值税 13% (测试公司)
    title = f"中国增值税 {rate}% ({company})"

    # 1. 检查是否存在
    existing_name = frappe.db.get_value(
        "Item Tax Template", {"title": title, "company": company}, "name"
    )

    if existing_name:
        # 如果已存在，我们需要确保它内部包含了两个科目（防止之前只有销项）
        update_existing_template(existing_name, company, rate)
        return existing_name

    # 2. 获取科目
    sales_account = frappe.db.get_value(
        "Account", {"account_name": "销项税额", "company": company}
    )
    purchase_account = frappe.db.get_value(
        "Account", {"account_name": "进项税额", "company": company}
    )

    if not sales_account or not purchase_account:
        frappe.log_error(f"公司 {company} 缺少销项或进项税科目，无法创建综合模板。")
        return None

    try:
        new_template = frappe.get_doc(
            {
                "doctype": "Item Tax Template",
                "title": title,
                "company": company,
                "taxes": [
                    {"tax_type": sales_account, "tax_rate": rate},
                    {"tax_type": purchase_account, "tax_rate": rate},
                ],
            }
        )
        new_template.insert(ignore_permissions=True, ignore_if_duplicate=True)
        return new_template.name
    except Exception:
        return None


def update_existing_template(template_name, company, rate):
    """辅助函数：确保现有模板同时拥有进/销项行"""
    t_doc = frappe.get_doc("Item Tax Template", template_name)
    accounts_in_tpl = [d.tax_type for d in t_doc.taxes]

    updated = False
    for acc_name in ["销项税额", "进项税额"]:
        acc = frappe.db.get_value(
            "Account", {"account_name": acc_name, "company": company}
        )
        if acc and acc not in accounts_in_tpl:
            t_doc.append("taxes", {"tax_type": acc, "tax_rate": rate})
            updated = True

    if updated:
        t_doc.save(ignore_permissions=True)


def get_tax_rate_hierarchy(group_name):
    rate = frappe.db.get_value("Item Group", group_name, "custom_standard_tax_rate")
    if rate is not None:
        return flt(rate)
    parent = frappe.db.get_value("Item Group", group_name, "parent_item_group")
    if parent and parent != "All Item Groups":
        return get_tax_rate_hierarchy(parent)
    return None


# --- 定期巡查：计划任务函数 ---
def daily_tax_audit():
    """
    每天凌晨巡查：发现税率不一致的物料并自动修正
    """
    items = frappe.get_all("Item", fields=["name", "item_group"])
    for i in items:
        # 这里可以加一个逻辑，判断当前税率是否与物料组一致，不一致才 save
        # 为保证脚本简洁，此处直接调用更新逻辑
        doc = frappe.get_doc("Item", i.name)
        update_item_tax_data(doc)
        doc.save(ignore_permissions=True)
