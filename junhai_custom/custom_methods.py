import frappe
import hashlib
import json
from frappe.utils import now_datetime


@frappe.whitelist()
def calculate_parameters_hash(doc, method=None):
    """
    计算 New Item Request 单据中，标记为 join_to_hash 的参数的标准化MD5指纹。
    """

    standardized_params = {}

    for row in doc.item_parameters:

        # 🌟 核心修正：双重检查
        # 1. 必须标记为 join_to_hash (1/True)
        # 2. 必须不是 Format 类型 (Format 行不提供参数值)
        if row.join_to_hash and row.constraint_type != "Format":
            param_name = row.parameter_name
            param_value = row.parameter_value

            # 标准化：去除 None，转换为字符串
            # 注意：Link/Unit 等字段的值在 parameter_value 中可能是 Link Name
            value = str(param_value).strip() if param_value is not None else ""

            # 排除空的参数值，只保留有意义的组合
            if value:
                standardized_params[param_name] = value

    # 2. 排序参数并拼接成字符串

    sorted_keys = sorted(standardized_params.keys())

    # 拼接最终的指纹源字符串 (格式: key1=value1|key2=value2)
    fingerprint_source = "|".join(
        [f"{key}={standardized_params[key]}" for key in sorted_keys]
    )

    # 3. 计算 MD5 指纹
    md5_hash = hashlib.md5(fingerprint_source.encode("utf-8")).hexdigest()

    # 4. 存储指纹源和指纹到 DocType 字段
    # 假设 New Item Request 上有 fields: unique_code (Data)
    doc.unique_code = md5_hash

    return md5_hash


# -----------------------------------------------------
# 2. 查重操作函数 (用于前端按钮调用)
# -----------------------------------------------------


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
