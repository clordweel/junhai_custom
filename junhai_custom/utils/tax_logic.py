import frappe
from frappe import _
from frappe.utils import flt


def update_item_tax_data(doc, method=None):
    """
    更新物料税率逻辑：增加多公司适配和科目存在性筛选
    """
    if not doc.item_group:
        return False

    tax_rate = get_tax_rate_hierarchy(doc.item_group)
    if tax_rate is None:
        return False

    # 获取所有非集团公司
    companies = frappe.get_all("Company", filters={"is_group": 0})

    target_templates = []
    for c in companies:
        # 改进点：ensure 函数现在会返回 None 如果该公司不满足条件
        template_name = ensure_combined_tax_template(c.name, tax_rate)
        if template_name:
            target_templates.append(template_name)

    # 性能优化：检查当前物料的税率表是否已符合目标
    current_templates = [d.item_tax_template for d in doc.get("taxes")]

    if set(target_templates) == set(current_templates) and len(target_templates) == len(
        current_templates
    ):
        return False

    # 执行更新
    doc.set("taxes", [])
    for t_name in target_templates:
        doc.append(
            "taxes",
            {
                "item_tax_template": t_name,
                "tax_category": "",
            },
        )
    return True


def ensure_combined_tax_template(company, rate):
    """
    改进后的模板生成：严格筛选公司科目
    """
    title = f"中国增值税 {rate}% ({company})"

    # 1. 检查是否存在该模板
    existing_name = frappe.db.get_value(
        "Item Tax Template", {"title": title, "company": company}, "name"
    )

    # 2. 核心改进：预先校验该公司是否有对应的进销项科目
    # 使用科目编号查找（针对您的 CSV 结构）
    sales_account = frappe.db.get_value(
        "Account", {"account_number": "22210108", "company": company}
    )
    purchase_account = frappe.db.get_value(
        "Account", {"account_number": "22210101", "company": company}
    )

    # 如果该公司不具备这两个科目，直接跳过，不为此公司生成模板
    if not sales_account or not purchase_account:
        # 可选：如果是调试阶段，可以取消下面注释查看哪些公司缺科目
        # frappe.msgprint(_("公司 {0} 缺少指定的进销项税科目，跳过自动税率分配。").format(company))
        return None

    # 3. 校验科目类型（防止报错“科目类型须为税项”）
    for acc in [sales_account, purchase_account]:
        acc_type = frappe.db.get_value("Account", acc, "account_type")
        if acc_type not in ["Tax", "Income", "Expense"]:
            # 只有在确定的情况下才修正
            frappe.db.set_value("Account", acc, "account_type", "Tax")

    if existing_name:
        update_existing_template(existing_name, sales_account, purchase_account, rate)
        return existing_name

    # 4. 创建新模板
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
    except Exception as e:
        frappe.log_error(f"Company {company} template creation failed: {str(e)}")
        return None


def update_existing_template(template_name, sales_account, purchase_account, rate):
    """确保现有模板科目准确"""
    t_doc = frappe.get_doc("Item Tax Template", template_name)
    accounts_in_tpl = [d.tax_type for d in t_doc.taxes]

    updated = False
    for acc in [sales_account, purchase_account]:
        if acc and acc not in accounts_in_tpl:
            t_doc.append("taxes", {"tax_type": acc, "tax_rate": rate})
            updated = True

    if updated:
        t_doc.save(ignore_permissions=True)


def get_tax_rate_hierarchy(group_name):
    """层级获取税率"""
    rate = frappe.db.get_value("Item Group", group_name, "custom_standard_tax_rate")
    if rate is not None:
        return flt(rate)

    parent = frappe.db.get_value("Item Group", group_name, "parent_item_group")
    if parent and parent != "All Item Groups":
        return get_tax_rate_hierarchy(parent)
    return None


def daily_tax_audit():
    """计划任务：高性能巡查"""
    items = frappe.get_all("Item", fields=["name"])
    updated_count = 0

    for i in items:
        doc = frappe.get_doc("Item", i.name)
        if update_item_tax_data(doc):
            doc.save(ignore_permissions=True)
            updated_count += 1

    if updated_count > 0:
        frappe.logger().info(f"Tax Audit: Updated {updated_count} items.")
