import frappe
from frappe import _

# 引用 ERPNext 核心公司模块
import erpnext.setup.doctype.company.company as company_module

# 1. 备份原始函数
original_setup_taxes = company_module.setup_taxes_and_charges


def patched_setup_taxes_and_charges(company_name, country):
    """
    君海智造强化补丁：适配公司初始化时的税费模板创建
    """
    if country == "China":
        # 记录开始执行
        frappe.logger().info(
            f"--- 君海补丁：开始为 {company_name} 配置中国税率体系 ---"
        )

        # 调用创建函数
        create_junhai_standard_taxes(company_name)

        # 拦截成功
        return

    return original_setup_taxes(company_name, country)


def create_junhai_standard_taxes(company_name):
    tax_configs = [
        {"title": "13%", "rate": 13.0, "is_default": 1},
        {"title": "9%", "rate": 9.0, "is_default": 0},
        {"title": "6%", "rate": 6.0, "is_default": 0},
        {"title": "3%", "rate": 3.0, "is_default": 0},
        {"title": "1%", "rate": 1.0, "is_default": 0},
    ]

    for item in tax_configs:
        # 销项模板
        _make_idempotent_template(
            company_name,
            "Sales Taxes and Charges Template",
            f"中国增值税 - {item['title']} (销项)",
            "22210108",  # 销项编号
            "销项税额",  # 备份名称
            item["rate"],
            item["is_default"],
        )

        # 进项模板
        _make_idempotent_template(
            company_name,
            "Purchase Taxes and Charges Template",
            f"中国增值税 - {item['title']} (进项)",
            "22210101",  # 进项编号
            "进项税额",  # 备份名称
            item["rate"],
            item["is_default"],
        )


def _make_idempotent_template(
    company, doctype, title, account_number, backup_name, rate, is_default
):
    child_doctype = (
        "Sales Taxes and Charges"
        if doctype == "Sales Taxes and Charges Template"
        else "Purchase Taxes and Charges"
    )

    # 1. 多维度查找科目
    account_head = frappe.db.get_value(
        "Account", {"account_number": account_number, "company": company}
    )

    if not account_head:
        account_head = frappe.db.get_value(
            "Account",
            {
                "account_name": ["like", f"%{backup_name}%"],
                "company": company,
                "is_group": 0,
            },
        )

    if not account_head:
        frappe.logger().error(
            f"君海补丁错误：公司 {company} 找不到科目 {account_number} 或 {backup_name}"
        )
        return

    # 2. 修正科目类型
    if frappe.db.get_value("Account", account_head, "account_type") != "Tax":
        frappe.db.set_value(
            "Account", account_head, "account_type", "Tax", update_modified=False
        )

    # 3. 确定成本中心 (修复报错点)
    # ERPNext 公司文档中的默认成本中心字段是 'cost_center'
    cost_center = frappe.db.get_value("Company", company, "cost_center")

    # 如果公司还没设置默认成本中心（导入期间常见），尝试找该公司的根成本中心
    if not cost_center:
        cost_center = frappe.db.get_value(
            "Cost Center",
            {
                "company": company,
                "is_group": 1,
                "parent_cost_center": ["is", "not set"],
            },
            "name",
        )
        # 如果还是找不到，找任何属于该公司的成本中心
        if not cost_center:
            cost_center = frappe.db.get_value(
                "Cost Center", {"company": company}, "name"
            )

    # 4. 幂等处理：获取或新建
    existing_name = frappe.db.get_value(doctype, {"title": title, "company": company})

    if existing_name:
        doc = frappe.get_doc(doctype, existing_name)
        frappe.db.delete(child_doctype, {"parent": existing_name})
    else:
        doc = frappe.new_doc(doctype)
        doc.title = title
        doc.company = company

    doc.is_default = is_default
    doc.set("taxes", [])

    # 5. 插入税率行
    doc.append(
        "taxes",
        {
            "charge_type": "On Net Total",
            "account_head": account_head,
            "rate": rate,
            "description": f"增值税 {rate}%",
            "cost_center": cost_center,  # 使用找到的成本中心
        },
    )

    doc.flags.ignore_permissions = True
    doc.save(ignore_version=True)
    frappe.db.commit()


def apply_patch():
    company_module.setup_taxes_and_charges = patched_setup_taxes_and_charges
