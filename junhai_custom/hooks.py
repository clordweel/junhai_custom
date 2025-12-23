app_name = "junhai_custom"
app_title = "Junhai Custom"
app_publisher = "BIoT"
app_description = "Custom Features For Junhai Componany."
app_email = "dev@bit.js.cn"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
    {
        "name": "junhai_custom",
        "logo": "/assets/junhai_custom/images/jh-app-logo.svg",
        "title": "Junhai Custom",
        "route": "/app/overview",
        "has_permission": "junhai_custom.check_app_permission",
    }
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = [
    "/assets/junhai_custom/css/junhai_standard.css",
    "/assets/junhai_custom/css/v16_patching_styles.css",
]
app_include_js = [
    "/assets/junhai_custom/js/v16_link_hotfix.js",
    "/assets/junhai_custom/js/code_field_custom.js",
]

# include js, css files in header of web template
# web_include_css = "/assets/junhai_custom/css/junhai_custom.css"
# web_include_js = "/assets/junhai_custom/js/junhai_custom.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "junhai_custom/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views

doctype_js = {
    # "New Item Request": "public/js/doctype/new_item_request.js",
    # "Item Parameter Template": "public/js/doctype/item_parameter_template.js",
    "Item Group": "public/js/doctype/item_group.js",
}

# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "junhai_custom/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "junhai_custom.utils.jinja_methods",
# 	"filters": "junhai_custom.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "junhai_custom.install.before_install"

after_install = "junhai_custom.utils.setup.setup_uom_data"

# Uninstallation
# ------------

# before_uninstall = "junhai_custom.uninstall.before_uninstall"
# after_uninstall = "junhai_custom.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "junhai_custom.utils.before_app_install"
# after_app_install = "junhai_custom.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "junhai_custom.utils.before_app_uninstall"
# after_app_uninstall = "junhai_custom.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "junhai_custom.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "New Item Request": {
        "before_save": "junhai_custom.utils.new_item_request.calculate_parameters_hash",
    },
    "Item": {
        # "on_update": "junhai_custom.utils.new_item_request.update_request_on_item_save",
        "before_insert": "junhai_custom.utils.item.auto_set_item_code",
        "validate": "junhai_custom.utils.tax_logic.update_item_tax_data",
    },
}

# Scheduled Tasks
# ---------------

scheduler_events = {
    # 	"all": [
    # 		"junhai_custom.tasks.all"
    # 	],
    "daily": ["junhai_custom.utils.tax_logic.daily_tax_audit"],
    # 	"hourly": [
    # 		"junhai_custom.tasks.hourly"
    # 	],
    # 	"weekly": [
    # 		"junhai_custom.tasks.weekly"
    # 	],
    # 	"monthly": [
    # 		"junhai_custom.tasks.monthly"
    # 	],
}

# Testing
# -------

# before_tests = "junhai_custom.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "junhai_custom.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "junhai_custom.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "junhai_custom.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["junhai_custom.utils.before_request"]
# after_request = ["junhai_custom.utils.after_request"]

# Job Events
# ----------
# before_job = ["junhai_custom.utils.before_job"]
# after_job = ["junhai_custom.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"junhai_custom.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

fixtures = [
    {"dt": "Print Format", "filters": [["module", "=", app_title]]},
    {"dt": "Print Style", "filters": [["name", "=", "Standard"]]},
    {"dt": "Report", "filters": [["module", "=", app_title]]},
    {"dt": "Client Script", "filters": [["module", "=", app_title]]},
    {"dt": "Server Script", "filters": [["module", "=", app_title]]},
    {"dt": "Translation", "filters": []},
    {"dt": "Executive Standard", "filters": []},
    {"dt": "Item Group", "filters": []},
    {"dt": "Item Surface", "filters": []},
    {"dt": "Item Material", "filters": []},
    {"dt": "Item Color", "filters": []},
    {"dt": "Item Base Name", "filters": []},
    {"dt": "Item Parameter Template", "filters": [["module", "=", app_title]]},
    # {"dt": "New Item Request", "filters": []},
    # 导出时，因为加密了 secret，再导入会填充错误密钥，所以不导出
    # {"dt": "Social Login Key", "filters": [["name", "=", "logto"]]},
    {"dt": "External Link", "filters": [["module", "=", app_title]]},
    {"dt": "Custom Field", "filters": [["module", "=", app_title]]},
    {"dt": "UOM", "filters": [["name", "in", ["件", "张", "台"]]]},
    {"dt": "Currency", "filters": [["name", "in", ["CNY"]]]},
    {
        "dt": "Property Setter",
        "filters": [
            [
                "doc_type",
                "in",
                [
                    "New Item Request",
                    "Item Parameter Template",
                    "Item Group",
                    "Item",
                    "UOM",
                    "Material Request Item",
                    "Purchase Order Item",
                    "Purchase Receipt Item",
                    "Purchase Invoice Item",
                    "Supplier Quotation Item",
                    "Quotation Item",
                    "Sales Order Item",
                    "Delivery Note Item",
                    "Sales Invoice Item",
                    "Stock Entry Detail",
                    "BOM Item",
                    "BOM Explosion Item",
                ],
            ],
        ],
    },
]
