$(document).on('app_ready', function () {
    // 重写 Code 字段的初始化逻辑
    if (frappe.ui.form.ControlCode) {
        const standard_make_ace_editor = frappe.ui.form.ControlCode.prototype.make_ace_editor;
        frappe.ui.form.ControlCode.prototype.make_ace_editor = function () {
            standard_make_ace_editor.apply(this, arguments);
            if (this.editor) {
                this.editor.setOption("wrap", true); // 开启换行
                this.editor.setOption("showPrintMargin", false); // 隐藏打印边界线
            }
        };
    }
});