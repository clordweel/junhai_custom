// Copyright (c) 2025, BIoT and contributors
// For license information, please see license.txt

// 全局查重函数，可被多个按钮调用
function run_duplicate_check(frm, callback) {
    // 假设 unique_code 字段在 New Item Request 主表中
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
                // 发现重复，给出警告
                frappe.throw({
                    title: __('发现重复'),
                    message: r.message.message,
                    indicator: 'red'
                });
            } else {
                // 没有重复，执行回调 (如果是 '创建物料' 按钮)
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
        const item_not_generated = !frm.doc.generated_item;

        // 1. 添加 "检查重复" 按钮
        if (frm.doc.docstatus === 0 || is_submitted) {
            frm.add_custom_button(__('检查参数重复'), function () {
                run_duplicate_check(frm);
            }, __('操作'));
        }

        if (is_submitted && item_not_generated) {

            frm.add_custom_button(__('创建物料 (复核)'), function () {

                // A. 首先执行重复检查
                run_duplicate_check(frm, function () {
                    // B. 如果查重通过，继续执行数据生成和跳转

                    frm.clear_custom_buttons();

                    frappe.call({
                        method: 'junhai_custom.api.new_item_request.generate_item_data_dict',
                        args: {
                            doc: frm.doc
                        },
                        callback(r) {
                            if (r.message) {
                                const item_data = r.message;

                                frappe.model.with_doctype('Item', function () {
                                    var new_item_doc = frappe.model.get_new_doc('Item');
                                    $.extend(new_item_doc, item_data);
                                    new_item_doc.custom_new_item_request = frm.doc.name;

                                    frappe.set_route('Form', 'Item', new_item_doc.name);
                                });
                            } else if (r.exc) {
                                frm.reload_doc();
                            }
                        },
                        error(r) {
                            frm.reload_doc();
                        }
                    });
                });
            }, __('操作'));
        }

        // 3. 如果已生成物料，则显示链接而不是按钮
        else if (frm.doc.generated_item) {
            frm.add_custom_button(__('查看已建物料'), function () {
                frappe.set_route('Form', 'Item', frm.doc.generated_item);
            }, __('查看'));
        }
    },

    // 监听主表单中 'template' 字段的变动
    template(frm) {

        // 如果模板字段被清空，则清除子表数据
        if (!frm.doc.template) {
            frm.clear_table('parameters');
            frm.clear_table('uoms');
            frm.refresh_field('parameters');
            frm.refresh_field('uoms');
            return;
        }

        // 🌟 关键修正：清空操作移入 callback 中，确保在数据返回后立即执行。
        // 这里先不清空，在 callback 中清空。

        // 调用后端API，获取所选模板的全部数据
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Item Parameter Template',
                name: frm.doc.template
            },
            callback(r) {
                if (r.message) {
                    var template = r.message;

                    // 🌟 修正区域 1：在添加数据前，清除现有的 parameters
                    frm.clear_table('parameters');

                    // --- 1. 预填充 Item Parameters 子表 ---
                    if (template.parameters && template.parameters.length) {
                        $.each(template.parameters, function (i, row) {
                            var new_row = frm.add_child('parameters');

                            //  添加 from_template 字段，用于标识是否来自模板
                            new_row.from_template = true;

                            //  拷贝模板中的参数数据到子表
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
                                    // 'Data' 类型不需要特别处理
                                    default: new_row.parameter_value = defaultVal;
                                }
                                new_row.parameter_value = defaultVal;
                            }
                        });
                        frm.refresh_field('parameters');
                    }

                    // 🌟 修正区域 2：在添加 UOMs 数据前，清除现有的 uoms
                    frm.clear_table('uoms');

                    // --- 2. 预填充 UOMs 子表 (UOMs 子表逻辑) ---
                    if (template.uoms && template.uoms.length) {
                        $.each(template.uoms, function (i, row) {
                            var new_row = frm.add_child('uoms');
                            new_row.uom = row.uom;
                            new_row.conversion_factor = row.conversion_factor;
                        });
                    }

                    // 统一刷新 UOMs 字段
                    frm.refresh_field('uoms');

                    // --- 3. 预填充主表字段 (Item Group) ---
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

frappe.ui.form.on('Item Parameter Definition', { // 监听子表事件 (保持不变)
    // 监听所有动态输入字段的变动
    value_float(frm, cdt, cdn) { sync_value(frm, cdt, cdn, 'value_float'); },
    value_integer(frm, cdt, cdn) { sync_value(frm, cdt, cdn, 'value_integer'); },
    value_doctype(frm, cdt, cdn) { sync_value(frm, cdt, cdn, 'value_doctype'); },
    value_format(frm, cdt, cdn) { sync_value(frm, cdt, cdn, 'value_format'); },

    // 监听约束类型变化，用于清空不相关的字段 (防脏数据)
    constraint_type(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        var fields_to_clear = ['value_float', 'value_integer', 'value_doctype', 'value_format'];

        fields_to_clear.forEach(function (fieldname) {
            // 修正清除逻辑，避免清除当前类型对应的值
            const constraint_type = row.constraint_type ? row.constraint_type.toLowerCase().trim() : '';
            const field_is_relevant = fieldname.includes(constraint_type);

            if (row[fieldname] !== null && row[fieldname] !== undefined && !field_is_relevant) {
                frappe.model.set_value(cdt, cdn, fieldname, null);
            }
        });

        frappe.model.set_value(cdt, cdn, 'parameter_value', null);
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

    frappe.model.set_value(cdt, cdn, 'parameter_value', val);

    frm.refresh_field('parameters');
}