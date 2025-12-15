import frappe


def setup_uom_data():
    """
    1. 执行重命名 (汉化)
    2. 设置打印符号 (symbol)
    """
    print(">>> [Setup] 开始配置 UOM 数据 (汉化 + 符号)...")

    # 格式： "旧英文名": ("新中文名", "符号")
    # 如果已经是中文环境，旧名写成中文即可，脚本会处理
    uom_data = {
        # === 基础 ===
        "Meter": ("米", "m"),
        "Kg": ("千克", "kg"),
        "Nos": ("个", "pcs"),
        "Box": ("箱", "box"),
        "Set": ("套", "set"),
        "Pair": ("双", "pair"),
        # === 补充清单 ===
        "Tonne": ("吨", "t"),
        "Metric Ton": ("吨", "t"),  # 覆盖
        "Gram": ("克", "g"),
        "Milligram": ("毫克", "mg"),
        "Millimeter": ("毫米", "mm"),
        "Centimeter": ("厘米", "cm"),
        "Kilometer": ("公里", "km"),
        # === 包装与形态 ===
        "Drum": ("桶", "drum"),
        "Bag": ("袋", "bag"),
        "Roll": ("卷", "roll"),
        # === 时间与物理 ===
        "Hour": ("小时", "hr"),
        "Minute": ("分钟", "min"),
        "Second": ("秒", "s"),
        "Kilowatt Hour": ("度", "kWh"),
        "Watt": ("瓦", "W"),
        "Volt": ("伏", "V"),
        "Ampere": ("安", "A"),
        # === 面积体积 ===
        "Square Meter": ("平方米", "m²"),
        "Cubic Meter": ("立方米", "m³"),
    }

    for src_name, (target_name, symbol) in uom_data.items():
        # --- 1. 处理重命名 ---
        final_uom_name = src_name  # 默认为原名

        # 如果旧名字存在（比如 Meter），且还没改名
        if frappe.db.exists("UOM", src_name):
            # 检查目标名字是否存在（比如 米）
            is_merge = frappe.db.exists("UOM", target_name)

            # 如果源名字和目标名字不一样（防止重复改名 Meter -> Meter）
            if src_name != target_name:
                try:
                    frappe.rename_doc("UOM", src_name, target_name, merge=is_merge)
                    print(f"✅ 重命名: {src_name} -> {target_name}")
                    final_uom_name = target_name
                except Exception as e:
                    print(f"⚠️ 重命名跳过: {e}")

        # 也有可能系统里已经是“米”了，或者原名就是“米”
        elif frappe.db.exists("UOM", target_name):
            final_uom_name = target_name

        # --- 2. 更新符号字段 ---
        if frappe.db.exists("UOM", final_uom_name):
            # 只有当符号还没设置，或者想强制更新时执行
            current_symbol = frappe.db.get_value("UOM", final_uom_name, "symbol")

            if current_symbol != symbol:
                frappe.db.set_value("UOM", final_uom_name, "symbol", symbol)
                print(f"   ⚙️ 设置符号: {final_uom_name} = {symbol}")

    frappe.db.commit()
    print(">>> UOM 重命名补丁执行完毕。")
