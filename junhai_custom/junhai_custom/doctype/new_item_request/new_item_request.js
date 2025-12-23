// Copyright (c) 2025, BIoT and contributors
// For license information, please see license.txt

// 全局查重函数
function run_duplicate_check(frm, callback) {
    const unique_code = frm.doc.unique_code;

    if (!unique_code) {
        frappe.msgprint(__('单据未保存，无法生成指纹进行查重。请先保存或提交！'), __('操作受限'));
        return;
    }

    frappe.call({
        method: 'junhai_custom.api.new_item_request.check_duplicate_request',
        args: {
            unique_code: unique_code,
            current_docname: frm.doc.name
        },
        callback(r) {
            if (r.message && r.message.duplicate) {
                frappe.throw({
                    title: __('发现重复'),
                    message: r.message.message,
                    indicator: 'red'
                });
            } else {
                frappe.show_alert({
                    message: r.message.message,
                    indicator: 'green'
                });
                if (callback) {
                    callback();
                }
            }
        }
    });
}

frappe.ui.form.on('New Item Request', {
    refresh(frm) {
        const is_submitted = frm.doc.docstatus === 1;

        // 1. 添加 "检查重复" 按钮 (只要不是新建单据即可)
        if (!frm.is_new()) {
            frm.add_custom_button(__('检查参数重复'), function () {
                run_duplicate_check(frm);
            }, __('操作'));
        }

        // 2. 处理 "创建物料" 或 "查看已建物料" 按钮
        // 只有在已提交的状态下才需要判断
        if (is_submitted) {
            // 🌟 核心修改：通过反向字段查询 Item 表，检查是否已存在关联物料
            frappe.db.get_value('Item', { 'custom_new_item_request': frm.doc.name }, 'name', (r) => {
                if (r && r.name) {
                    // A. 如果查到了物料 -> 显示 "查看已建物料"
                    frm.add_custom_button(__('查看已建物料'), function () {
                        frappe.set_route('Form', 'Item', r.name);
                    }, __('查看'));
                } else {
                    // B. 如果没查到物料 -> 显示 "创建物料 (复核)"
                    frm.add_custom_button(__('创建物料 (复核)'), function () {
                        // B1. 先查重
                        run_duplicate_check(frm, function () {
                            // B2. 查重通过，调用API生成数据
                            frappe.call({
                                method: 'junhai_custom.api.new_item_request.generate_item_data_dict',
                                args: {
                                    doc: frm.doc
                                },
                                callback(res) {
                                    if (res.message) {
                                        const item_data = res.message;
                                        frappe.model.with_doctype('Item', function () {
                                            var new_item_doc = frappe.model.get_new_doc('Item');
                                            $.extend(new_item_doc, item_data);

                                            // 务必赋值反向链接字段，确保下次刷新能识别
                                            new_item_doc.custom_new_item_request = frm.doc.name;

                                            frappe.set_route('Form', 'Item', new_item_doc.name);
                                        });
                                    } else if (res.exc) {
                                        frm.reload_doc();
                                    }
                                },
                                error(res) {
                                    frm.reload_doc();
                                }
                            });
                        });
                    }, __('操作'));
                }
            });
        }
    },

    // 监听主表单中 'template' 字段的变动
    template(frm) {
        if (!frm.doc.template) {
            frm.clear_table('parameters');
            frm.clear_table('uoms');
            frm.refresh_field('parameters');
            frm.refresh_field('uoms');
            return;
        }

        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Item Parameter Template',
                name: frm.doc.template
            },
            callback(r) {
                if (r.message) {
                    var template = r.message;

                    // 1. 填充 Parameters
                    frm.clear_table('parameters');
                    if (template.parameters && template.parameters.length) {
                        $.each(template.parameters, function (i, row) {
                            var new_row = frm.add_child('parameters');
                            new_row.from_template = true;
                            new_row.parameter_name = row.parameter_name;
                            new_row.description = row.description;
                            new_row.constraint_type = row.constraint_type || '';
                            new_row.readonly_value = row.readonly_value || 0;
                            new_row.join_to_hash = row.join_to_hash || 0;
                            new_row.binding_field = row.binding_field || 0;
                            new_row.target_field = row.target_field || '';

                            if (row.value_float !== undefined) new_row.value_float = row.value_float;
                            if (row.value_integer !== undefined) new_row.value_integer = row.value_integer;
                            if (row.value_format !== undefined) new_row.value_format = row.value_format;
                            if (row.doctype_selector !== undefined) {
                                new_row.doctype_selector = row.doctype_selector;
                                if (row.value_doctype !== undefined) new_row.value_doctype = row.value_doctype;
                            }

                            var defaultVal = null;
                            if (row.parameter_default_value !== undefined) defaultVal = row.parameter_default_value;
                            else if (row.parameter_value !== undefined) defaultVal = row.parameter_value;
                            else if (row.default !== undefined) defaultVal = row.default;

                            if (defaultVal !== null) {
                                switch ((row.constraint_type || '').trim()) {
                                    case 'Float': new_row.value_float = defaultVal; break;
                                    case 'Integer': new_row.value_integer = defaultVal; break;
                                    case 'Doctype': new_row.value_doctype = defaultVal; break;
                                    case 'Format': new_row.value_format = defaultVal; break;
                                    default: new_row.parameter_value = defaultVal;
                                }
                                new_row.parameter_value = defaultVal;
                            }
                        });
                        frm.refresh_field('parameters');
                    }

                    // 2. 填充 UOMs
                    frm.clear_table('uoms');
                    if (template.uoms && template.uoms.length) {
                        $.each(template.uoms, function (i, row) {
                            var new_row = frm.add_child('uoms');
                            new_row.uom = row.uom;
                            new_row.conversion_factor = row.conversion_factor;
                        });
                    }
                    frm.refresh_field('uoms');

                    // 3. 填充主表字段
                    if (template.item_group) {
                        frm.set_value('item_group', template.item_group);
                    }
                } else {
                    frappe.show_alert({
                        message: __('获取物料模板数据失败。请联系管理员。'),
                        indicator: 'red'
                    });
                }
            },
            error() {
                frappe.msgprint(__('获取物料模板数据失败。请联系管理员。'));
            }
        });
    },
});

// 子表逻辑保持不变
frappe.ui.form.on('Item Parameter Definition', {
    value_float(frm, cdt, cdn) { sync_value(frm, cdt, cdn, 'value_float'); },
    value_integer(frm, cdt, cdn) { sync_value(frm, cdt, cdn, 'value_integer'); },
    value_doctype(frm, cdt, cdn) { sync_value(frm, cdt, cdn, 'value_doctype'); },
    value_format(frm, cdt, cdn) { sync_value(frm, cdt, cdn, 'value_format'); },

    constraint_type(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        var fields_to_clear = ['value_float', 'value_integer', 'value_doctype', 'value_format'];

        fields_to_clear.forEach(function (fieldname) {
            const constraint_type = row.constraint_type ? row.constraint_type.toLowerCase().trim() : '';
            const field_is_relevant = fieldname.includes(constraint_type);

            if (row[fieldname] !== null && row[fieldname] !== undefined && !field_is_relevant) {
                frappe.model.set_value(cdt, cdn, fieldname, null);
            }
        });

        frappe.model.set_value(cdt, cdn, 'parameter_value', null);
    }
});

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

    frappe.model.set_value(cdt, cdn, 'parameter_value', val);
    frm.refresh_field('parameters');
}