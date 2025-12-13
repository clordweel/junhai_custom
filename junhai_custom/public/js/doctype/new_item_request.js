// New Item Request - Auto Load Parameters

frappe.ui.form.on('New Item Request', {
    // 监听主表单中 'template' 字段的变动 (您的实际字段名)
    template: function (frm) {

        // 如果模板字段被清空，则清除子表数据
        if (!frm.doc.template) {
            frm.clear_table('item_parameters');
            frm.refresh_field('item_parameters');
            return;
        }

        // 清空子表，准备加载新数据
        frm.clear_table('item_parameters');

        // 调用后端API，获取所选模板的全部数据
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Item Parameter Template',
                name: frm.doc.template // 使用实际字段名 template
            },
            callback: function (r) {
                // 检查返回的数据和模板子表 'parameters'
                if (r.message && r.message.parameters) {
                    var template = r.message;

                    // 遍历模板中的参数定义 (子表名: parameters)
                    $.each(template.parameters, function (i, row) {
                        // 在申请单的子表 (子表名: item_parameters) 中添加新行
                        var new_row = frm.add_child('item_parameters');

                        // 映射常用字段
                        new_row.parameter_name = row.parameter_name || row.name || '';
                        new_row.constraint_type = row.constraint_type || '';

                        // 拷贝模板中已有的具体约束字段（如果存在）
                        if (row.value_material) new_row.value_material = row.value_material;
                        if (row.value_surface) new_row.value_surface = row.value_surface;
                        if (row.value_float !== undefined) new_row.value_float = row.value_float;
                        if (row.value_integer !== undefined) new_row.value_integer = row.value_integer;
                        if (row.value_base_name) new_row.value_base_name = row.value_base_name;
                        if (row.value_unit) new_row.value_unit = row.value_unit;

                        // 兼容模板中可能的默认值字段名（parameter_default_value / parameter_value / default）
                        var defaultVal = null;
                        if (row.parameter_default_value !== undefined) defaultVal = row.parameter_default_value;
                        else if (row.parameter_value !== undefined) defaultVal = row.parameter_value;
                        else if (row.default !== undefined) defaultVal = row.default;

                        // 根据约束类型将默认值填入相应字段，同时也保留通用的 parameter_value 字段
                        if (defaultVal !== null) {
                            switch ((row.constraint_type || '').trim()) {
                                case 'Material':
                                    new_row.value_material = defaultVal; break;
                                case 'Surface':
                                    new_row.value_surface = defaultVal; break;
                                case 'Float':
                                    new_row.value_float = defaultVal; break;
                                case 'Integer':
                                    new_row.value_integer = defaultVal; break;
                                case 'Base Name':
                                    new_row.value_base_name = defaultVal; break;
                                case 'Unit':
                                    new_row.value_unit = defaultVal; break;
                                default:
                                    new_row.parameter_value = defaultVal;
                            }
                            // 通用展示/搜索字段
                            new_row.parameter_value = defaultVal;

                            // 标记该行数据来源于模板
                            new_row.from_template = true;
                        }
                    });

                    // 刷新子表显示
                    frm.refresh_field('item_parameters');
                } else {
                    frappe.show_alert({
                        message: __('所选物料模板中没有定义任何参数。'),
                        indicator: 'orange'
                    }, 3);
                }

                if (r.message && r.message.item_group) {
                    frm.set_value('item_group', r.message.item_group);
                }
            },
            error: function () {
                frappe.msgprint(__('获取物料模板数据失败。请联系管理员。'));
            }
        });
    }
});

frappe.ui.form.on('Item Parameter Definition', { // 监听子表事件
    // 监听所有动态输入字段的变动
    value_material: function (frm, cdt, cdn) { sync_default_value(frm, cdt, cdn, 'value_material'); },
    value_surface: function (frm, cdt, cdn) { sync_default_value(frm, cdt, cdn, 'value_surface'); },
    value_float: function (frm, cdt, cdn) { sync_default_value(frm, cdt, cdn, 'value_float'); },
    value_integer: function (frm, cdt, cdn) { sync_default_value(frm, cdt, cdn, 'value_integer'); },
    value_base_name: function (frm, cdt, cdn) { sync_default_value(frm, cdt, cdn, 'value_base_name'); },
    value_unit: function (frm, cdt, cdn) { sync_default_value(frm, cdt, cdn, 'value_unit'); },

    // 监听约束类型变化，用于清空不相关的字段 (防脏数据)
    constraint_type: function (frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        var fields_to_clear = ['value_material', 'value_surface', 'value_float', 'value_integer', 'value_base_name', 'value_unit'];

        fields_to_clear.forEach(function (fieldname) {
            if (row[fieldname] !== null && row[fieldname] !== undefined) {
                if (!fieldname.includes(row.constraint_type.toLowerCase())) {
                    frappe.model.set_value(cdt, cdn, fieldname, null);
                }
            }
        });

        frappe.model.set_value(cdt, cdn, 'parameter_value', null);
    }
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

    frappe.model.set_value(cdt, cdn, 'parameter_value', val);
    frm.refresh_field('parameters'); // 刷新子表显示
}
