import frappe


def patch_login_context(context):
    """
    在登录页面渲染前，强行改写发往前端的 LDAP 配置。
    这个 context 会覆盖原生 LDAP Settings 产生的所有数据。
    """
    # 检查当前页面是否是登录页
    if frappe.local.request.path.strip("/") == "login":
        # 获取你的新设置
        new_ldap = frappe.get_cached_doc("New LDAP Settings")

        if new_ldap.enabled:
            # 强行注入前端需要的配置
            context["ldap_settings"] = {
                "enabled": 1,
                "method": "junhai_custom.api.new_ldap_settings.custom_ldap_login",
            }
            # 这一步能确保即使原生 LDAP Settings 是空的，前端也会显示 LDAP 按钮
