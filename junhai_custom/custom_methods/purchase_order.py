from junhai_custom.utils.currency import get_rmb_upper


def purchase_order_validate(doc, method):
    """
    在保存和提交时强制覆盖金额大写
    """
    if doc.currency == "CNY":
        # 计算大写
        upper_text = get_rmb_upper(doc.grand_total)

        # 强制赋值
        doc.base_in_words = upper_text
        doc.in_words = upper_text
