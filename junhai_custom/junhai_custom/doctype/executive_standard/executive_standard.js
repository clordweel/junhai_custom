// Copyright (c) 2025, BIoT and contributors
// For license information, please see license.txt

frappe.ui.form.on("Executive Standard", {
    refresh(frm) {

    },
    validate(frm) {
        // 获取年份字段的值 (假设字段名为 revision_year)
        let year = frm.doc.revision_year;

        // 如果有值，且不符合4位数字的规则
        if (year && !/^\d{4}$/.test(year)) {
            frappe.msgprint('年份格式错误，请输入 4 位数字，例如：2024');
            frappe.validated = false; // 阻止保存
        }
    }
});
