// 文件名/脚本名: Item Parameter Template - Default Value Sync

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
