import frappe
import hashlib


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


def calculate_parameters_hash(doc, method=None):
    """
    计算 New Item Request 单据中，标记为 join_to_hash 的参数的标准化MD5指纹。
    """

    standardized_params = {}

    for row in doc.parameters:

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
