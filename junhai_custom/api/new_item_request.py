import frappe
import json
from frappe.utils import flt


@frappe.whitelist()
def check_duplicate_request(unique_code, current_docname):
    """
    检查系统中是否存在具有相同参数指纹且已提交的 New Item Request。
    """
    if not unique_code:
        return {"duplicate": False, "message": "指纹为空，无法查重。"}

    # 查找所有已提交（docstatus=1）且指纹相同的单据，排除当前单据
    duplicate_name = frappe.db.get_value(
        "New Item Request",
        filters={
            "docstatus": 1,
            "unique_code": unique_code,
            "name": ["!=", current_docname],
        },
        fieldname="name",
        order_by="modified DESC",
    )

    if duplicate_name:
        return {
            "duplicate": True,
            "name": duplicate_name,
            "message": f"发现重复的物料参数组合！重复单据：{duplicate_name}。请核实！",
        }
    else:
        return {"duplicate": False, "message": "当前参数组合未发现重复申请单。"}


@frappe.whitelist()
def generate_item_data_dict(doc):
    """
    接收 New Item Request 数据，解析参数、格式化规则、UOM 子表，生成 Item DocType 的数据字典。
    """

    # --- 核心修正：处理 Frappe.call 传入的 JSON 字符串参数 ---
    if isinstance(doc, str):
        try:
            doc_data = json.loads(doc)
            doc = frappe.get_doc(doc_data)
        except Exception as e:
            frappe.throw(f"无法解析传入的单据数据：{e}", title="数据解析错误")
    elif isinstance(doc, dict):
        doc = frappe.get_doc(doc)

    if doc.docstatus != 1:
        frappe.throw("只能对已提交的物料申请单执行操作。", title="操作限制")

    params = {}  # 用于 str.format() 拼接的参数字典
    assignment_rules = []  # 用于直接或格式化赋值的规则列表
    unit_conversions = []  # 用于单位转换子表的列表

    # --- 阶段一：收集参数值和所有赋值规则 ---
    for row in doc.parameters:

        # 1. 收集到 params 字典中 (所有非 Format 的行)
        if row.constraint_type != "Format":
            value = row.parameter_value
            params[row.parameter_name] = str(value) if value is not None else ""

        # 2. 收集赋值规则 (Binding Rule)
        if row.binding_field == 1 and row.target_field:
            rule = {
                "target_field": row.target_field,
                "constraint_type": row.constraint_type,
                "source_value": row.parameter_value,
                "parameter_name": row.parameter_name,
            }
            assignment_rules.append(rule)

    # --- 阶段二：处理单位转换子表 (UOMs) ---

    # 🌟 关键：遍历 New Item Request.uoms 子表
    if hasattr(doc, "uoms") and doc.uoms:
        for row in doc.uoms:
            factor = flt(row.conversion_factor)

            # 排除转换系数为 1 的行，防止重复创建基准单位
            # if factor != 1:
            unit_conversions.append(
                {
                    "doctype": "Item Unit Conversion",  # 目标 DocType
                    "uom": row.uom,
                    "conversion_factor": factor,
                }
            )

    # --- 阶段三：应用赋值规则，构建 Item 字典 ---

    item_fields = {
        "doctype": "Item",
        "is_stock_item": 1,
        # 继承主字段
        "custom_new_item_request": doc.name,
        "item_group": doc.item_group,
        "custom_unique_code": doc.unique_code,
        # 🌟 附加单位转换子表数据
        "uoms": unit_conversions,
    }

    final_item_name = None

    for rule in assignment_rules:
        target_field = rule["target_field"]
        final_value = None

        if rule["constraint_type"] == "Format":
            format_string = rule["source_value"]
            try:
                final_value = format_string.format(**params)
            except KeyError as e:
                missing_param = str(e).strip("'")
                frappe.throw(
                    f"字段【{target_field}】的格式化模板中引用的参数【{missing_param}】在申请单中未提供值或名称不匹配。",
                    title="格式化错误",
                )
        else:
            final_value = rule["source_value"]

        if final_value is not None:
            item_fields[target_field] = final_value

            if target_field == "item_name":
                final_item_name = final_value

    # --- 阶段四：最终校验和返回 ---

    if not final_item_name:
        frappe.toast(
            f"申请单 {doc.name}: 模板中未指定物料名称 (item_name) 的格式化规则。将依赖 Item DocType 的命名规则。",
            "orange",
        )

    if final_item_name and frappe.db.exists("Item", {"item_name": final_item_name}):
        frappe.msgprint(
            f"注意：系统中已存在名为【{final_item_name}】的物料！请在新建页面核实。",
            title="查重提醒",
            indicator="orange",
        )

    return item_fields
