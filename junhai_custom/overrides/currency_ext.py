import frappe
from frappe.utils import flt

# 假设你的转换工具函数在此路径，请根据实际情况调整
from junhai_custom.utils.currency import get_rmb_upper


class RMBMixin(object):
    """
    针对 BuyingController 相关单据的人民币大写逻辑扩展
    适用范围：Purchase Order, Purchase Invoice, Material Request
    """

    def set_total_in_words(self):
        # 1. 运行链条中的上一个逻辑（原厂逻辑或其他 App 的扩展）
        try:
            super().set_total_in_words()
        except Exception:
            # 捕获原厂逻辑在 Material Request 等缺少 currency 字段单据上的报错
            pass

        # 2. 获取当前上下文币种
        # 优先级：单据自带币种 -> 价格表币种 -> 公司默认币种
        currency = (
            getattr(self, "currency", None)
            or getattr(self, "price_list_currency", None)
            or frappe.get_cached_value("Company", self.company, "default_currency")
        )

        # 3. 仅当币种为人民币 (CNY) 时执行强制覆盖
        if currency == "CNY":
            self._apply_rmb_upper_custom_logic()

    def _apply_rmb_upper_custom_logic(self):
        """执行具体的字段赋值逻辑"""
        try:
            # A. 处理 base_in_words (本位币大写)
            if self.meta.get_field("base_in_words"):
                base_amount = self._get_appropriate_amount(is_base=True)
                self.base_in_words = get_rmb_upper(base_amount)

            # B. 处理 in_words (交易币大写)
            if self.meta.get_field("in_words"):
                amount = self._get_appropriate_amount(is_base=False)
                self.in_words = get_rmb_upper(amount)

        except Exception as e:
            # 记录错误但不阻断单据保存
            frappe.log_error(
                title="RMB Upper Conversion Error",
                message=f"Doc: {self.doctype} {self.name}\nError: {str(e)}",
            )

    def _get_appropriate_amount(self, is_base=False):
        """
        复刻源码取值算法：
        如果有圆整金额（Rounded Total）且系统未禁用圆整，则取圆整值，否则取总额。
        """
        prefix = "base_" if is_base else ""
        rounded_field = f"{prefix}rounded_total"
        grand_field = f"{prefix}grand_total"

        # 检查字段是否存在且逻辑上是否启用了圆整
        if self.meta.get_field(rounded_field) and not self.is_rounded_total_disabled():
            val = getattr(self, rounded_field, 0)
        else:
            val = getattr(self, grand_field, 0)

        return abs(flt(val))
