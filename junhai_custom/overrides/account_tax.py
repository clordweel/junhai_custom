import frappe
from frappe import _

# 引用您确认正确的路径
import erpnext.setup.doctype.company.company as company_module

# 1. 备份原始函数
original_setup_taxes = company_module.setup_taxes_and_charges


def patched_setup_taxes_and_charges(company_name, country):
    """
    君海智造补丁：拦截过时的 17% 税率
    采用物理清理逻辑，确保删除重建公司时税费模板不重复
    """
    if country == "China":
        frappe.logger().info(
            f"君海补丁执行中：正在为公司 {company_name} 强制重置 13%/9%/6%/3%/1% 税率体系"
        )

        # 调用强化后的创建函数
        create_junhai_standard_taxes(company_name)

        # 拦截成功，不再执行 ERPNext 源码
        return

    return original_setup_taxes(company_name, country)


def create_junhai_standard_taxes(company_name):
    """
    创建标准税率模板清单
    """
    tax_configs = [
        {"title": "13%", "rate": 13.0, "is_default": 1},
        {"title": "9%", "rate": 9.0, "is_default": 0},
        {"title": "6%", "rate": 6.0, "is_default": 0},
        {"title": "3%", "rate": 3.0, "is_default": 0},
        {"title": "1%", "rate": 1.0, "is_default": 0},
    ]

    for item in tax_configs:
        # 创建销售税模板 (销项)
        _make_idempotent_template(
            company_name,
            "Sales Taxes and Charges Template",
            f"中国增值税 - {item['title']} (销项)",
            "销项税额",
            item["rate"],
            item["is_default"],
        )

        # 创建采购税模板 (进项)
        _make_idempotent_template(
            company_name,
            "Purchase Taxes and Charges Template",
            f"中国增值税 - {item['title']} (进项)",
            "进项税额",
            item["rate"],
            item["is_default"],
        )


def _make_idempotent_template(company, doctype, title, account_name, rate, is_default):
    """
    核心幂等函数：物理清理子表，确保无论重复执行多少次，结果永远只有一行
    """
    # 确定对应的子表 DocType
    child_doctype = (
        "Sales Taxes and Charges"
        if doctype == "Sales Taxes and Charges Template"
        else "Purchase Taxes and Charges"
    )

    # 获取科目 ID (适配纯净科目名)
    account_head = frappe.db.get_value(
        "Account", {"account_name": account_name, "company": company}
    )
    if not account_head:
        return

    # 1. 检查并处理父文档
    existing_name = frappe.db.get_value(doctype, {"title": title, "company": company})

    if existing_name:
        # --- 核心修复：物理删除属于该父文档的所有子表行 ---
        # 这样做可以彻底抹除“删除公司后残留”的孤儿数据
        frappe.db.delete(child_doctype, {"parent": existing_name})

        doc = frappe.get_doc(doctype, existing_name)
    else:
        doc = frappe.new_doc(doctype)
        doc.title = title
        doc.company = company

    # 2. 重置父文档属性
    doc.is_default = is_default
    doc.set("taxes", [])  # 在内存对象中也清空子表列表

    # 3. 添加唯一的税率行
    doc.append(
        "taxes",
        {
            "charge_type": "On Net Total",
            "account_head": account_head,
            "rate": rate,
            "account_name": account_name,
            "description": f"增值税 {rate}%",
            "cost_center": frappe.db.get_value("Company", company, "cost_center"),
        },
    )

    # 4. 强制保存
    doc.flags.ignore_permissions = True
    doc.flags.ignore_mandatory = True
    doc.save()

    # 显式提交数据库事务，确保删除重建时数据立即固化
    frappe.db.commit()


def apply_patch():
    # 执行替换
    company_module.setup_taxes_and_charges = patched_setup_taxes_and_charges
