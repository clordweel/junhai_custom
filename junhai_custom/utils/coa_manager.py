import os
import shutil
import frappe

# 定义路径常量
APP_NAME = "junhai_custom"
JSON_FILENAME = "cn_junhai_chart.json"

# 目标路径：ERPNext 存放标准科目表的目录 (V16 路径)
# 注意：如果 V16 以后改了路径，改这里即可
TARGET_DIR = frappe.get_app_path(
    "erpnext", "accounts", "doctype", "account", "chart_of_accounts", "verified"
)

# 源路径：你自定义 App 里的文件
SOURCE_FILE = frappe.get_app_path(APP_NAME, "data", JSON_FILENAME)


@frappe.whitelist()
def install_coa_template():
    """将自定义科目表复制到 ERPNext 系统目录"""

    # 1. 检查源文件是否存在
    if not os.path.exists(SOURCE_FILE):
        return {"status": "error", "message": f"源文件丢失：{SOURCE_FILE}"}

    # 2. 检查目标目录是否存在
    if not os.path.exists(TARGET_DIR):
        return {"status": "error", "message": f"目标目录不存在：{TARGET_DIR}"}

    try:
        # 3. 执行复制
        shutil.copy(SOURCE_FILE, TARGET_DIR)

        # 4. 清理缓存 (重要：让 ERPNext 重新扫描目录)
        frappe.cache().delete_value("get_charts_for_country")

        return {
            "status": "success",
            "message": f"成功！已将 {JSON_FILENAME} 部署到系统目录。<br>请刷新页面并在新建公司时选择中国。",
        }
    except Exception as e:
        return {"status": "error", "message": f"复制失败：{str(e)}"}


@frappe.whitelist()
def remove_coa_template():
    """从 ERPNext 系统目录删除自定义科目表（重置）"""
    target_file = os.path.join(TARGET_DIR, JSON_FILENAME)

    if os.path.exists(target_file):
        try:
            os.remove(target_file)
            frappe.cache().delete_value("get_charts_for_country")
            return {
                "status": "success",
                "message": "重置成功！已从系统目录删除自定义模板。",
            }
        except Exception as e:
            return {"status": "error", "message": f"删除失败：{str(e)}"}
    else:
        return {"status": "skipped", "message": "目标文件本来就不存在，无需删除。"}
