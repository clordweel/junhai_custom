import json
import re
import html
import frappe
from frappe.utils import flt


@frappe.whitelist()
def check_duplicate_request(unique_code, current_docname):
    """检查是否存在相同参数指纹的已提交申请"""
    if not unique_code:
        return {"duplicate": False, "message": "指纹为空，无法查重。"}

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
            "message": f"发现重复的物料参数组合！重复单据：{duplicate_name}。",
        }
    return {"duplicate": False, "message": "当前参数组合未发现重复。"}


@frappe.whitelist()
def preview_parameters(parameters, context=None):
    """前端预览计算逻辑：支持级联引用"""
    if isinstance(parameters, str):
        parameters = json.loads(parameters)
    if isinstance(context, str):
        context = json.loads(context)

    # 1. 整理初始上下文，处理数值类型
    safe_context = {}
    if context:
        for k, v in context.items():
            if v is None or v == "":
                safe_context[k] = ""
                continue
            try:
                f_val = float(v)
                safe_context[k] = int(f_val) if f_val.is_integer() else f_val
            except ValueError:
                safe_context[k] = v

    # 2. 核心：按 idx 排序，确保级联计算顺序
    sorted_params = sorted(parameters, key=lambda x: x.get("idx", 0))
    result = {}

    for row in sorted_params:
        p_name = row.get("parameter_name")
        if row.get("constraint_type") == "Format":
            raw_template = row.get("value_format") or row.get("parameter_default_value")
            if not raw_template:
                continue

            try:
                # 反转义 HTML (处理 > < 等符号) 并渲染
                template = html.unescape(raw_template)
                rendered_value = frappe.render_template(template, safe_context)

                # 清理多余空格和换行
                rendered_value = re.sub(r"\n\s*\n", "\n", rendered_value).strip()
                rendered_value = re.sub(r" +", " ", rendered_value)

                result[row.get("name")] = rendered_value

                # 🌟 关键：将当前渲染结果存入上下文，供后续 Format 行引用
                if p_name:
                    safe_context[p_name] = rendered_value
            except Exception as e:
                result[row.get("name")] = f"渲染错误: {str(e)}"
        else:
            # 非 Format 类型，确保上下文中的值是最新的
            if p_name:
                val = row.get("parameter_value")
                try:
                    if val and str(val).replace(".", "", 1).isdigit():
                        f_val = float(val)
                        safe_context[p_name] = (
                            int(f_val) if f_val.is_integer() else f_val
                        )
                    else:
                        safe_context[p_name] = val
                except:
                    safe_context[p_name] = val

    return result


@frappe.whitelist()
def generate_item_data_dict(doc):
    """正式生成 Item 数据字典：支持级联引用"""
    if isinstance(doc, str):
        doc = frappe.get_doc(json.loads(doc))
    elif isinstance(doc, dict):
        doc = frappe.get_doc(doc)

    if doc.docstatus != 1:
        frappe.throw("只能对已提交的单据执行操作。")

    # 1. 收集 UOM
    unit_conversions = []
    for row in doc.uoms or []:
        unit_conversions.append(
            {
                "doctype": "Item Unit Conversion",
                "uom": row.uom,
                "conversion_factor": flt(row.conversion_factor),
            }
        )

    # 2. 顺序处理参数，构建最终 Context
    final_context = {}
    assignment_rules = []
    sorted_parameters = sorted(doc.parameters, key=lambda x: x.idx)

    for row in sorted_parameters:
        p_name = row.parameter_name
        if row.constraint_type != "Format":
            final_context[p_name] = row.parameter_value
        else:
            template_str = (
                row.parameter_value or row.value_format or row.parameter_default_value
            )
            if template_str:
                try:
                    rendered = frappe.render_template(
                        html.unescape(template_str), final_context
                    )
                    rendered = re.sub(r"\s+", " ", rendered).strip()
                    final_context[p_name] = rendered
                except:
                    final_context[p_name] = ""

        # 收集需要绑定到 Item 字段的规则
        if row.binding_field == 1 and row.target_field:
            assignment_rules.append(
                {"target_field": row.target_field, "parameter_name": p_name}
            )

    # 3. 映射到 Item 字段
    item_fields = {
        "doctype": "Item",
        "is_stock_item": 1,
        "item_group": doc.item_group,
        "image": doc.image,
        "custom_new_item_request": doc.name,
        "custom_unique_code": doc.unique_code,
        "uoms": unit_conversions,
    }

    for rule in assignment_rules:
        val = final_context.get(rule["parameter_name"])
        if val is not None:
            item_fields[rule["target_field"]] = val

    return item_fields
