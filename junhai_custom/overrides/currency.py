import frappe
from frappe.utils import flt
from erpnext.controllers.buying_controller import BuyingController
from junhai_custom.utils.currency import get_rmb_upper

# 1. 保存系统原有的方法引用
_original_set_total_in_words = BuyingController.set_total_in_words


# 2. 定义我们自己的逻辑
def set_total_in_words_patched(self):
    """
    针对 BuyingController 的补丁方法
    兼容 Material Request (无 currency 字段) 和 Purchase Order (有 currency 字段)
    """

    # --- 第一步：安全运行系统原逻辑 ---
    try:
        # 尝试运行原方法。如果是 Purchase Order，这通常能正常运行。
        # 如果是 Material Request，原方法可能会因为找不 currency 而报错，我们捕获它而不中断。
        _original_set_total_in_words(self)
    except AttributeError:
        # 吞掉“没有属性”的错误，继续执行我们的自定义逻辑
        pass
    except Exception as e:
        # 记录其他意料之外的错误，方便调试，但尽量不阻断保存
        frappe.log_error(f"Error in original set_total_in_words: {str(e)}")

    # --- 第二步：智能获取上下文币种 ---
    # 优先级：单据自带币种 -> 价格表币种 -> 公司默认币种
    currency = (
        getattr(self, "currency", None)
        or getattr(self, "price_list_currency", None)
        or frappe.get_cached_value("Company", self.company, "default_currency")
    )

    # --- 第三步：针对 CNY 的强制覆盖逻辑 ---
    if currency == "CNY":
        try:
            # A. 处理 base_in_words (公司本位币大写)
            # 只有当单据里确实有这个字段时才处理，避免报错
            if self.meta.get_field("base_in_words"):
                # 逻辑复刻源码：优先取圆整后的金额，没有则取总金额
                if (
                    self.meta.get_field("base_rounded_total")
                    and not self.is_rounded_total_disabled()
                ):
                    base_amount = abs(flt(self.base_rounded_total))
                else:
                    base_amount = abs(flt(self.base_grand_total))

                # 调用您的中文转换函数
                self.base_in_words = get_rmb_upper(base_amount)

            # B. 处理 in_words (交易币种大写)
            if self.meta.get_field("in_words"):
                # 逻辑复刻源码：优先取圆整后的金额
                if (
                    self.meta.get_field("rounded_total")
                    and not self.is_rounded_total_disabled()
                ):
                    amount = abs(flt(self.rounded_total))
                else:
                    amount = abs(flt(self.grand_total))

                # 调用您的中文转换函数
                self.in_words = get_rmb_upper(amount)

        except Exception as e:
            # 捕获转换过程中的任何错误，防止卡住单据保存
            frappe.log_error(f"Error in RMB conversion patch: {str(e)}")
            pass


# 3. 执行替换 (Monkey Patch)
BuyingController.set_total_in_words = set_total_in_words_patched
