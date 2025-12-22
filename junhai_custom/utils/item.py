import frappe


def auto_set_item_code(doc, method=None):
    """
    Hooks: Item > before_validate 或 before_insert
    功能：根据物料组的 custom_code 自动设置 naming_series
    """

    # 1. 检查是否选择了物料组
    if not doc.item_group:
        return

    # 2. 获取物料组的 custom_code (直接取值，无需加载整个 Item Group 对象，效率更高)
    group_code = frappe.db.get_value("Item Group", doc.item_group, "custom_code")


    # 3. 核心逻辑
    if group_code:
        # 直接构造目标格式：代码 + .####
        # 结果示例：1010.####
        target_series = f"{group_code}.####"

        # 赋值给单据
        doc.naming_series = target_series

    else:
        # 4. 防呆机制：如果物料组没有配置代码，抛出错误阻止保存
        # 这样可以防止生成错误的编号，强制要求维护好基础数据
        frappe.throw(
            title="编号生成失败",
            msg=f"物料组 <b>{doc.item_group}</b> 未配置编码前缀 (Custom Code)。<br>请先在物料组中设置代码（如 1010），或选择正确的末级分组。",
        )
