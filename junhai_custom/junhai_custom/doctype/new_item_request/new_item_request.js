// Copyright (c) 2025, BIoT and contributors

const trigger_preview_calculation = frappe.utils.debounce((frm) => {
    let context_data = {};
    let has_format = false;

    // 收集所有当前值作为 Jinja 渲染的初始变量
    (frm.doc.parameters || []).forEach(row => {
        let val = row.parameter_value;
        if (row.constraint_type === 'Integer' || row.constraint_type === 'Float') {
            val = flt(val);
        }
        if (row.parameter_name) {
            context_data[row.parameter_name] = val;
        }
        if (row.constraint_type === 'Format') {
            has_format = true;
        }
    });

    if (!has_format) return;

    frappe.call({
        method: 'junhai_custom.api.new_item_request.preview_parameters',
        args: {
            parameters: frm.doc.parameters,
            context: context_data
        },
        callback: (r) => {
            if (r.message) {
                frm._is_system_updating = true;
                let has_changes = false;

                $.each(frm.doc.parameters, function (i, row) {
                    if (r.message[row.name] !== undefined && row.parameter_value !== r.message[row.name]) {
                        frappe.model.set_value(row.doctype, row.name, 'parameter_value', r.message[row.name]);
                        has_changes = true;
                    }
                });

                frm._is_system_updating = false;
                if (has_changes) {
                    frm.refresh_field('parameters');
                }
            }
        }
    });
}, 500);

frappe.ui.form.on('New Item Request', {
    refresh(frm) {
        frm._is_system_updating = false;
        if (!frm.is_new()) {
            frm.add_custom_button(__('检查参数重复'), () => run_duplicate_check(frm));
        }

        if (frm.doc.docstatus === 1) {
            frappe.db.get_value('Item', { 'custom_new_item_request': frm.doc.name }, 'name', (r) => {
                if (r && r.name) {
                    frm.add_custom_button(__('查看已建物料'), () => frappe.set_route('Form', 'Item', r.name));
                } else {
                    frm.add_custom_button(__('创建物料 (复核)'), function () {
                        run_duplicate_check(frm, function () {
                            frappe.call({
                                method: 'junhai_custom.api.new_item_request.generate_item_data_dict',
                                args: { doc: frm.doc },
                                freeze: true,
                                callback(res) {
                                    if (res.message) {
                                        let new_item = frappe.model.get_new_doc('Item');
                                        $.extend(new_item, res.message);
                                        new_item.custom_new_item_request = frm.doc.name;
                                        frappe.set_route('Form', 'Item', new_item.name);
                                    }
                                }
                            });
                        });
                    });
                }
            });
        }
    },

    template(frm) {
        if (!frm.doc.template) {
            frm.clear_table('parameters');
            frm.clear_table('uoms');
            frm.refresh_field('parameters');
            return;
        }
        frappe.call({
            method: 'frappe.client.get',
            args: { doctype: 'Item Parameter Template', name: frm.doc.template },
            freeze: true,
            callback(r) {
                if (!r.message) return;
                frm._is_system_updating = true;
                frm.clear_table('parameters');
                (r.message.parameters || []).forEach(row => {
                    let new_row = frm.add_child('parameters');
                    Object.assign(new_row, {
                        from_template: 1,
                        parameter_name: row.parameter_name,
                        description: row.description,
                        constraint_type: row.constraint_type,
                        readonly_value: row.readonly_value,
                        join_to_hash: row.join_to_hash,
                        binding_field: row.binding_field,
                        target_field: row.target_field,
                        doctype_selector: row.doctype_selector,
                        value_format: row.value_format,
                        value_float: row.value_float,
                        value_integer: row.value_integer,
                        value_doctype: row.value_doctype,
                        parameter_value: row.parameter_default_value
                    });
                });
                frm.clear_table('uoms');
                (r.message.uoms || []).forEach(row => {
                    let u = frm.add_child('uoms');
                    u.uom = row.uom;
                    u.conversion_factor = row.conversion_factor;
                });
                if (r.message.item_group) frm.set_value('item_group', r.message.item_group);
                frm.refresh_field('parameters');
                frm.refresh_field('uoms');
                frm._is_system_updating = false;
                trigger_preview_calculation(frm);
            }
        });
    }
});

frappe.ui.form.on('Item Parameter Definition', {
    value_float: (frm, cdt, cdn) => sync_value(frm, cdt, cdn, 'value_float'),
    value_integer: (frm, cdt, cdn) => sync_value(frm, cdt, cdn, 'value_integer'),
    value_doctype: (frm, cdt, cdn) => sync_value(frm, cdt, cdn, 'value_doctype'),
    value_format: (frm, cdt, cdn) => sync_value(frm, cdt, cdn, 'value_format'),
    parameter_value: (frm) => {
        if (frm._is_system_updating) return;
        trigger_preview_calculation(frm);
    }
});

function sync_value(frm, cdt, cdn, field) {
    if (frm._is_system_updating) return;
    let row = locals[cdt][cdn];
    frm._is_system_updating = true;
    frappe.model.set_value(cdt, cdn, 'parameter_value', row[field]);
    frm._is_system_updating = false;
    trigger_preview_calculation(frm);
}

function run_duplicate_check(frm, callback) {
    frappe.call({
        method: 'junhai_custom.api.new_item_request.check_duplicate_request',
        args: { unique_code: frm.doc.unique_code, current_docname: frm.doc.name },
        callback(r) {
            if (r.message && r.message.duplicate) {
                frappe.throw({ title: __('发现重复'), message: r.message.message, indicator: 'red' });
            } else {
                frappe.show_alert({ message: r.message.message, indicator: 'green' });
                if (callback) callback();
            }
        }
    });
}