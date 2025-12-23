// Copyright (c) 2025, BIoT and contributors
// For license information, please see license.txt

frappe.ui.form.on('Item Parameter Template', {
    refresh: function (frm) {
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

frappe.ui.form.on('Item Parameter Template Definition', { // 监听子表事件 (保持不变)
    // 监听所有动态输入字段的变动
    value_float(frm, cdt, cdn) { sync_value(frm, cdt, cdn, 'value_float'); },
    value_integer(frm, cdt, cdn) { sync_value(frm, cdt, cdn, 'value_integer'); },
    value_doctype(frm, cdt, cdn) { sync_value(frm, cdt, cdn, 'value_doctype'); },
    value_format(frm, cdt, cdn) { sync_value(frm, cdt, cdn, 'value_format'); },

    // 监听约束类型变化，用于清空不相关的字段 (防脏数据)
    constraint_type(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        var fields_to_clear = ['value_float', 'value_integer', 'value_format', 'value_doctype'];

        fields_to_clear.forEach(function (fieldname) {
            // 修正清除逻辑，避免清除当前类型对应的值
            const constraint_type = row.constraint_type ? row.constraint_type.toLowerCase().trim() : '';
            const field_is_relevant = fieldname.includes(constraint_type);

            if (row[fieldname] !== null && row[fieldname] !== undefined && !field_is_relevant) {
                frappe.model.set_value(cdt, cdn, fieldname, null);
            }
        });

        frappe.model.set_value(cdt, cdn, 'parameter_default_value', null);
    }
});

// 通用同步函数 (必须放在全局，或者在frappe.ui.form.on之外) (保持不变)
function sync_value(frm, cdt, cdn, source_field) {
    var row = locals[cdt][cdn];
    var val = row[source_field];

    if (frappe.get_meta(cdt).fields.find(f => f.fieldname == source_field && f.fieldtype == 'Link')) {
        val = String(val || "");
    } else if (val === null || val === undefined) {
        val = null;
    } else {
        val = String(val);
    }

    frappe.model.set_value(cdt, cdn, 'parameter_default_value', val);

    frm.refresh_field('parameters');
}