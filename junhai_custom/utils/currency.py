import frappe
import cn2an


# 核心转换逻辑 (保持不变)
def get_rmb_upper(amount):
    if not amount or float(amount) == 0:
        return "人民币零元整"
    try:
        amount_str = "{:.2f}".format(float(amount))
        upper = cn2an.an2cn(amount_str, "rmb")
        return "人民币" + upper
    except Exception as e:
        frappe.log_error(
            title="RMB Conversion Error", message=f"Input: {amount}, Error: {str(e)}"
        )
        return f"人民币{str(amount)}"
