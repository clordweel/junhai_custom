import frappe
from frappe.desk.search import search_link as original_search_link
import re
import inspect


@frappe.whitelist()
def custom_search_link(doctype, txt, **kwargs):
    # 1. 获取 original_search_link 函数接受的所有合法参数名
    # 这样即使 Frappe 后续升级增加了参数，代码也能自动适配
    sig = inspect.signature(original_search_link)
    allowed_keys = sig.parameters.keys()

    # 2. 构造干净的参数字典
    # 只保留 original_search_link 定义中存在的参数
    sanitized_kwargs = {k: v for k, v in kwargs.items() if k in allowed_keys}

    # 3. 业务逻辑处理：规格中的 * 或 x 转换
    if txt:
        # 兼容 5*100, 5 * 100, 5x100, 5X100 -> 5%100
        txt = re.sub(r"\s*[\*xX]\s*", "%", txt)

    # 4. 调用原始方法
    return original_search_link(doctype, txt, **sanitized_kwargs)
