import frappe
from frappe.desk.search import search_link as original_search_link
import re


@frappe.whitelist()
def custom_search_link(doctype, txt, **kwargs):
    # 1. 核心修复：剔除会导致 Crash 的参数
    # 根据你的报错，必须移除 'issingle' 和 'istable'
    # 这些是前端视图（特别是 Workflow Builder）传来的，但 search_link 不接受
    kwargs.pop("issingle", None)
    kwargs.pop("istable", None)

    # 移除系统自动附加的 API 参数
    kwargs.pop("cmd", None)
    kwargs.pop("data", None)
    kwargs.pop("request_id", None)  # 建议加上这个，这也是常见的系统参数

    # 注意：ignore_user_permissions 在新版 Frappe 的 search_link 中通常是支持的参数。
    # 如果你确定它不报错，建议保留它，以便管理员权限能生效。
    # 如果之前报过它的错，则取消下面这行的注释：
    # kwargs.pop("ignore_user_permissions", None)

    # 2. 你的业务逻辑：处理规格中的 * 号
    if txt:
        # 兼容 5*100, 5 * 100, 5x100, 5X100 -> 5%100
        # 这种模糊匹配非常适合找规格
        txt = re.sub(r"\s*[\*xX]\s*", "%", txt)

    # 3. 调用原始方法
    return original_search_link(doctype, txt, **kwargs)
