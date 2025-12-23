// Copyright (c) 2025, BIoT and contributors
// For license information, please see license.txt

// --- 工具函数：防抖动，避免频繁请求 ---
const trigger_preview_calculation = frappe.utils.debounce((frm) => {
    // 1. 收集当前所有非 Format 类型的参数值作为上下文
    let context_data = {};
    let format_rows = [];

    (frm.doc.parameters || []).forEach(row => {
        if (row.constraint_type !== 'Format') {
            // 确保数值类型正确转换，避免字符串拼接错误
            let val = row.parameter_value;
            if (row.constraint_type === 'Integer' || row.constraint_type === 'Float') {
                val = flt(val);
            }
            context_data[row.parameter_name] = val;
        } else {
            format_rows.push(row);
        }
    });

    // 如果没有 Format 行，直接返回
    if (format_rows.length === 0) return;

    // 2. 调用后端 API 进行 Jinja2 渲染 (确保支持 Python 的 round/float 等过滤器)
    frappe.call({
        method: 'junhai_custom.api.new_item_request.preview_parameters', // 需配套后端 Python 方法
        args: {
            parameters: frm.doc.parameters, // 将整个子表传给后端处理
            context: context_data
        },
        freeze: false, // 不冻结屏幕，实现无感刷新
        callback: (r) => {
            if (r.message) {
                // 3. 更新界面上的 Format 行
                let has_changes = false;
                $.each(frm.doc.parameters, function (i, row) {
                    if (r.message[row.name] !== undefined && row.parameter_value !== r.message[row.name]) {
                        frappe.model.set_value(row.doctype, row.name, 'parameter_value', r.message[row.name]);
                        has_changes = true;
                    }
                });

                if (has_changes) {
                    frm.refresh_field('parameters');
                }
            }
        }
    });
}, 500); // 延迟 500ms 触发


// --- 全局查重函数 ---
function run_duplicate_check(frm, callback) {
    const unique_code = frm.doc.unique_code;
    if (!unique_code) {
        frappe.msgprint(__('单据未保存或指纹未生成，请先保存！'));
        return;
    }
    frappe.call({
        method: 'junhai_custom.api.new_item_request.check_duplicate_request',
        args: { unique_code: unique_code, current_docname: frm.doc.name },
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

frappe.ui.form.on('New Item Request', {
    refresh(frm) {
        // 按钮逻辑保持不变
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
                let template = r.message;

                // 1. 填充 Parameters
                frm.clear_table('parameters');
                (template.parameters || []).forEach(row => {
                    let new_row = frm.add_child('parameters');
                    // 复制基础属性
                    ['parameter_name', 'description', 'constraint_type', 'readonly_value',
                        'join_to_hash', 'binding_field', 'target_field', 'doctype_selector'].forEach(k => {
                            new_row[k] = row[k];
                        });

                    // 复制默认值定义
                    ['value_float', 'value_integer', 'value_format', 'value_doctype'].forEach(k => {
                        if (row[k] !== undefined) new_row[k] = row[k];
                    });

                    // 确定初始 parameter_value
                    let defaultVal = row.parameter_default_value;

                    // 根据类型回填到具体的 value_xxx 字段，确保 UI 显示正确
                    if (defaultVal) {
                        if (row.constraint_type === 'Float') new_row.value_float = defaultVal;
                        else if (row.constraint_type === 'Integer') new_row.value_integer = defaultVal;
                        else if (row.constraint_type === 'Doctype') new_row.value_doctype = defaultVal;
                        else if (row.constraint_type === 'Format') new_row.value_format = defaultVal;

                        new_row.parameter_value = defaultVal;
                    }
                });
                frm.refresh_field('parameters');

                // 2. 填充 UOMs
                frm.clear_table('uoms');
                (template.uoms || []).forEach(row => {
                    let u = frm.add_child('uoms');
                    u.uom = row.uom;
                    u.conversion_factor = row.conversion_factor;
                });
                frm.refresh_field('uoms');

                // 3. 填充主表字段
                if (template.item_group) frm.set_value('item_group', template.item_group);

                // 4. 加载完成后，立即触发一次 Format 字段的计算
                trigger_preview_calculation(frm);
            }
        });
    }
});

// --- 子表事件监听 ---
frappe.ui.form.on('Item Parameter Definition', {
    // 监听所有具体值字段的变化
    value_float: (frm, cdt, cdn) => sync_value_and_trigger(frm, cdt, cdn, 'value_float'),
    value_integer: (frm, cdt, cdn) => sync_value_and_trigger(frm, cdt, cdn, 'value_integer'),
    value_doctype: (frm, cdt, cdn) => sync_value_and_trigger(frm, cdt, cdn, 'value_doctype'),

    // Format 模板本身改变时也重新计算
    value_format: (frm, cdt, cdn) => sync_value_and_trigger(frm, cdt, cdn, 'value_format'),

    constraint_type(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        // 清理不相关的字段
        ['value_float', 'value_integer', 'value_doctype', 'value_format'].forEach(f => {
            if (!f.includes((row.constraint_type || '').toLowerCase())) {
                frappe.model.set_value(cdt, cdn, f, null);
            }
        });
        frappe.model.set_value(cdt, cdn, 'parameter_value', null);
    }
});

function sync_value_and_trigger(frm, cdt, cdn, source_field) {
    let row = locals[cdt][cdn];
    let val = row[source_field];

    // 处理 Link 类型可能存在的 undefined
    if (frappe.get_meta(cdt).fields.find(f => f.fieldname == source_field && f.fieldtype == 'Link')) {
        val = String(val || "");
    } else if (val === null || val === undefined) {
        val = null;
    } else {
        val = String(val);
    }

    // 1. 同步到通用值字段
    frappe.model.set_value(cdt, cdn, 'parameter_value', val);

    // 2. 触发预览计算 (核心改动：任何参数变动都会触发 Format 行的重算)
    trigger_preview_calculation(frm);
}