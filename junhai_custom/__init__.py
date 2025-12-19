import frappe
from frappe.utils.user import is_website_user
import junhai_custom.overrides.account_tax as account_tax

__version__ = "0.0.1"


def check_app_permission():
    if frappe.session.user == "Administrator":
        return True

    if is_website_user():
        return False

    return True


account_tax.apply_patch()
