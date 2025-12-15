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

frappe.ui.form.on('Item Parameter Template Definition', { // 监听子表事件
    // // 监听所有动态输入字段的变动
    // value_material: function (frm, cdt, cdn) { sync_default_value(frm, cdt, cdn, 'value_material'); },
    // value_surface: function (frm, cdt, cdn) { sync_default_value(frm, cdt, cdn, 'value_surface'); },
    // value_float: function (frm, cdt, cdn) { sync_default_value(frm, cdt, cdn, 'value_float'); },
    // value_integer: function (frm, cdt, cdn) { sync_default_value(frm, cdt, cdn, 'value_integer'); },
    // value_base_name: function (frm, cdt, cdn) { sync_default_value(frm, cdt, cdn, 'value_base_name'); },
    // value_unit: function (frm, cdt, cdn) { sync_default_value(frm, cdt, cdn, 'value_unit'); },

    // // 监听约束类型变化，用于清空不相关的字段 (防脏数据)
    // constraint_type: function (frm, cdt, cdn) {
    //     var row = locals[cdt][cdn];
    //     var fields_to_clear = ['value_material', 'value_surface', 'value_float', 'value_integer', 'value_base_name', 'value_unit'];

    //     fields_to_clear.forEach(function (fieldname) {
    //         if (row[fieldname] !== null && row[fieldname] !== undefined) {
    //             if (!fieldname.includes(row.constraint_type.toLowerCase())) {
    //                 frappe.model.set_value(cdt, cdn, fieldname, null);
    //             }
    //         }
    //     });

    //     frappe.model.set_value(cdt, cdn, 'parameter_default_value', null);
    // }
});

// 通用同步函数 (必须放在全局，或者在frappe.ui.form.on之外)
function sync_default_value(frm, cdt, cdn, source_field) {
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
    frm.refresh_field('parameters'); // 刷新子表显示
}
