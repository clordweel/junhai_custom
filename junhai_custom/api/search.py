import frappe
from frappe.desk.search import search_link as original_search_link
import re


@frappe.whitelist()
def custom_search_link(doctype, txt, **kwargs):
    # 1. 核心修复：剔除 Frappe 自动生成的系统级参数
    # 这些参数是 API 调用产生的，但内核 search_link 函数并不支持
    kwargs.pop("cmd", None)
    kwargs.pop("data", None)  # 某些请求可能包含 data 参数
    kwargs.pop("ignore_user_permissions", None)  # 如果 core 不支持，也需移除

    # 2. 你的业务逻辑：处理规格中的 * 号
    # if txt and '*' in txt:
    #     # 将 "5 * 100" 转换为 "5%100"
    #     txt = re.sub(r'\s*\*\s*', '%', txt)
    if txt:
        # 兼容 5*100, 5 * 100, 5x100, 5X100
        txt = re.sub(r"\s*[\*xX]\s*", "%", txt)

    # 3. 再次确保 txt 已经处理后传给原始方法
    # 这里我们只传递原始方法确实需要的核心参数
    return original_search_link(doctype, txt, **kwargs)
