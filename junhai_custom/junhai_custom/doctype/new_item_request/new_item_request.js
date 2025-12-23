// Copyright (c) 2025, BIoT and contributors
// For license information, please see license.txt

// --- 工具函数：防抖动，避免频繁请求 ---
const trigger_preview_calculation = frappe.utils.debounce((frm) => {
    // 1. 收集当前所有非 Format 类型的参数值作为上下文
    let context_data = {};
    let format_rows = [];

    (frm.doc.parameters || []).forEach(row => {
        if (row.constraint_type !== 'Format') {
            // 确保数值类型正确转换
            let val = row.parameter_value;
            if (row.constraint_type === 'Integer' || row.constraint_type === 'Float') {
                val = flt(val);
            }
            context_data[row.parameter_name] = val;
        } else {
            format_rows.push(row);
        }
    });

    if (format_rows.length === 0) return;

    // 2. 调用后端 API 进行 Jinja2 渲染
    frappe.call({
        method: 'junhai_custom.api.new_item_request.preview_parameters',
        args: {
            parameters: frm.doc.parameters,
            context: context_data
        },
        freeze: false,
        callback: (r) => {
            if (r.message) {
                let has_changes = false;
                // 设置标志位，防止回写时再次触发计算
                frm._is_system_updating = true;

                $.each(frm.doc.parameters, function (i, row) {
                    if (r.message[row.name] !== undefined && row.parameter_value !== r.message[row.name]) {
                        frappe.model.set_value(row.doctype, row.name, 'parameter_value', r.message[row.name]);
                        has_changes = true;
                    }
                });

                // 解除标志位
                frm._is_system_updating = false;

                if (has_changes) {
                    frm.refresh_field('parameters');
                }
            }
        }
    });
}, 500);


// --- 全局查重函数 (保持不变) ---
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

// --- 主表逻辑 (保持不变) ---
frappe.ui.form.on('New Item Request', {
    refresh(frm) {
        // 初始化标志位
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
                let template = r.message;

                // 标记为系统更新，避免填充时触发多次计算
                frm._is_system_updating = true;

                // 1. 填充 Parameters
                frm.clear_table('parameters');
                (template.parameters || []).forEach(row => {
                    let new_row = frm.add_child('parameters');
                    ['parameter_name', 'description', 'constraint_type', 'readonly_value',
                        'join_to_hash', 'binding_field', 'target_field', 'doctype_selector'].forEach(k => {
                            new_row[k] = row[k];
                        });
                    ['value_float', 'value_integer', 'value_format', 'value_doctype'].forEach(k => {
                        if (row[k] !== undefined) new_row[k] = row[k];
                    });

                    let defaultVal = row.parameter_default_value;
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

                if (template.item_group) frm.set_value('item_group', template.item_group);

                // 解除标志位并手动触发一次计算
                frm._is_system_updating = false;
                trigger_preview_calculation(frm);
            }
        });
    }
});

// --- 子表事件监听 (核心修改部分) ---
frappe.ui.form.on('Item Parameter Definition', {
    // 监听特定类型字段
    value_float: (frm, cdt, cdn) => sync_value_and_trigger(frm, cdt, cdn, 'value_float'),
    value_integer: (frm, cdt, cdn) => sync_value_and_trigger(frm, cdt, cdn, 'value_integer'),
    value_doctype: (frm, cdt, cdn) => sync_value_and_trigger(frm, cdt, cdn, 'value_doctype'),
    value_format: (frm, cdt, cdn) => sync_value_and_trigger(frm, cdt, cdn, 'value_format'),

    // 🌟 新增：直接监听 parameter_value 的变化
    parameter_value: (frm, cdt, cdn) => {
        // 如果是系统正在更新（比如 Format 字段回写），则忽略，防止死循环
        if (frm._is_system_updating) return;

        // 触发重新计算
        trigger_preview_calculation(frm);
    },

    constraint_type(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        // 切换类型时，清理旧数据
        frm._is_system_updating = true; // 暂时锁住，防止清空操作触发不必要的计算
        ['value_float', 'value_integer', 'value_doctype', 'value_format'].forEach(f => {
            if (!f.includes((row.constraint_type || '').toLowerCase())) {
                frappe.model.set_value(cdt, cdn, f, null);
            }
        });
        frappe.model.set_value(cdt, cdn, 'parameter_value', null);
        frm._is_system_updating = false;
    }
});

function sync_value_and_trigger(frm, cdt, cdn, source_field) {
    // 如果是系统正在更新，直接跳过
    if (frm._is_system_updating) return;

    let row = locals[cdt][cdn];
    let val = row[source_field];

    if (frappe.get_meta(cdt).fields.find(f => f.fieldname == source_field && f.fieldtype == 'Link')) {
        val = String(val || "");
    } else if (val === null || val === undefined) {
        val = null;
    } else {
        val = String(val);
    }

    // 1. 同步到 parameter_value
    // 注意：这里设置 parameter_value 会触发上面的 parameter_value 监听
    // 但因为我们没有设置 _is_system_updating = true，所以它会正确地流向 trigger_preview_calculation
    // 为了效率，我们可以临时锁一下，或者直接在这里触发计算而不依赖级联触发

    frm._is_system_updating = true; // 锁住 parameter_value 的监听
    frappe.model.set_value(cdt, cdn, 'parameter_value', val);
    frm._is_system_updating = false; // 解锁

    // 2. 手动触发计算
    trigger_preview_calculation(frm);
}