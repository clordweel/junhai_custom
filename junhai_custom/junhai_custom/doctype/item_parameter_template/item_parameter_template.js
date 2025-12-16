// Copyright (c) 2025, BIoT and contributors
// For license information, please see license.txt

frappe.ui.form.on('Item Parameter Template', {
    refresh: function (frm) {
        console.log("Item Parameter Template 刷新事件触发");
        if (!frm.doc.__islocal) {

            frm.add_custom_button(__('创建物料申请单'), function () {

                const template_name = frm.doc.name;

                // 🌟 关键修正：使用 frappe.model.with_doctype 和 frappe.model.get_new_doc
                frappe.model.with_doctype('New Item Request', function () {

                    // 1. 在内存中创建一个新的 Doc 对象
                    var new_request_doc = frappe.model.get_new_doc('New Item Request');

                    // 2. 预设字段值
                    // 预设字段名必须与 New Item Request DocType 上的字段名一致
                    new_request_doc.template = template_name;
                    // 命名系列字段会在这里被初始化 (即使 DocName 仍是 'New Item Request-00001')

                    // 3. 导航到新的 Doc 对象
                    // 我们使用 new_request_doc.name，它此时是一个临时客户端名称
                    frappe.set_route('Form', 'New Item Request', new_request_doc.name);
                });

            }, __('操作'));
        }
    }
});
