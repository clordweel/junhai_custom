# apps/junhai_custom/junhai_custom/overrides.py
from erpnext.controllers.buying_controller import BuyingController
from junhai_custom.utils.currency import get_rmb_upper

# 1. 保存系统原有的方法引用（以防万一需要用到）
_original_set_total_in_words = BuyingController.set_total_in_words


# 2. 定义我们自己的逻辑
def set_total_in_words_patched(self):
    """
    这是替换后的新方法
    """
    # 先运行系统原逻辑（确保其他货币或字段初始化正常）
    _original_set_total_in_words(self)

    # 针对 CNY 进行强制覆盖 (这是最后一道防线)
    if self.currency == "CNY":
        try:
            # 调用你 utils.py 里的转换函数
            upper = get_rmb_upper(self.grand_total)

            # 暴力覆盖所有相关字段
            self.base_in_words = upper
            self.in_words = upper
        except Exception:
            pass


# 3. 执行替换 (Monkey Patch)
# 这行代码一运行，ERPNext 里的 BuyingController 就会变身
BuyingController.set_total_in_words = set_total_in_words_patched
