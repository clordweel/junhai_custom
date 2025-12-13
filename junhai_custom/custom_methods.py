import frappe
import json
from frappe.utils import now_datetime


@frappe.whitelist()
def generate_item_data_dict(doc):
    """
    接收 New Item Request 数据，解析参数和格式化规则，生成 Item DocType 的数据字典。
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

    # --- 阶段零：前置校验和初始化 ---
    if doc.docstatus != 1:
        frappe.throw("只能对已提交的物料申请单执行操作。", title="操作限制")

    params = {}
    format_rules = []

    # --- 阶段一：收集用户填写的参数值和格式化规则 ---

    for row in doc.item_parameters:

        # 1. 判断是否为格式化行 (constraint_type == 'Format')
        if row.constraint_type == "Format":
            if row.binding_field == 1 and row.target_field:
                # 格式模板存储在 parameter_value 字段
                format_rules.append(
                    {
                        "target_field": row.target_field,
                        "format_string": row.parameter_value,
                    }
                )
            continue

        # 2. 处理普通参数行 (constraint_type != 'Format')
        value = row.parameter_value

        # 存储参数到字典，确保值为字符串以便于 str.format() 拼接
        params[row.parameter_name] = str(value) if value is not None else ""

    # --- 阶段二：应用模板规则，构建 Item 字典 ---

    item_fields = {
        "doctype": "Item",
        "is_stock_item": 1,
        # 🌟 修正：使用 custom_new_item_request 字段存储来源申请单名称
        "custom_new_item_request": doc.name,
        # 🌟 修正：从申请单继承 item_group
        "item_group": doc.item_group,
        # description 字段不再有默认值，将完全由 format_rules 覆盖
    }

    final_item_name = None

    for rule in format_rules:
        target_field = rule["target_field"]
        format_string = rule["format_string"]
        final_value = None

        try:
            # 核心：使用参数字典 params 格式化字符串
            final_value = format_string.format(**params)
        except KeyError as e:
            missing_param = str(e).strip("'")
            frappe.throw(
                f"字段【{target_field}】的格式化模板中引用的参数【{missing_param}】在申请单中未提供值或名称不匹配。",
                title="格式化错误",
            )

        if final_value is not None:
            item_fields[target_field] = final_value

            if target_field == "item_name":
                final_item_name = final_value
            # 🌟 修正：物料描述 (description) 现在也是一个普通的格式化字段，直接赋值。

    # --- 阶段三：最终校验和返回 ---

    if not final_item_name:
        frappe.throw(
            "模板配置错误：物料名称 (item_name) 字段未通过模板赋值，无法创建。",
            title="配置错误",
        )

    # 查重提醒
    if frappe.db.exists("Item", {"item_name": final_item_name}):
        frappe.msgprint(
            f"注意：系统中已存在名为【{final_item_name}】的物料！请在新建页面核实。",
            title="查重提醒",
            indicator="orange",
        )

    return item_fields


# --- 可选：回填申请单的钩子函数 ---
def update_request_on_item_save(doc, method):
    """
    在 Item 保存时，回填 New Item Request 的 generated_item 字段。
    此函数使用 Item DocType 上的 custom_new_item_request 字段作为回填依据。
    """
    # 🌟 修正：使用新的字段名
    request_name = doc.custom_new_item_request

    if request_name and not frappe.db.get_value(
        "New Item Request", request_name, "generated_item"
    ):
        try:
            request_doc = frappe.get_doc("New Item Request", request_name)
            request_doc.generated_item = doc.name
            request_doc.status = "Completed"
            request_doc.save(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(
                f"无法回填物料申请单 {request_name}，错误: {e}",
                "ITEM_REQUEST_BACKFILL_ERROR",
            )
