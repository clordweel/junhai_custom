frappe.ui.form.on('Item Group', {
    refresh: function (frm) {
        if (!frm.is_new()) {
            // 添加一个名为“税务管理”的下拉菜单
            frm.add_custom_button(__('清理旧版模板 (全局)'), function () {
                // 执行清理逻辑
                handle_cleanup(frm);
            }, __('税务工具'));

            frm.add_custom_button(__('同步至下属物料'), function () {
                // 执行同步逻辑
                handle_sync(frm);
            }, __('税务工具'));

            // 将菜单加粗或变色，突出显示
            frm.page.set_inner_btn_group_dot(__('税务工具'), 'orange');
        }
    }
});

// --- 清理逻辑 ---
function handle_cleanup(frm) {
    frappe.confirm(__('<b>危险操作：</b>此功能将全局删除所有标题含“(销项)”或“(进项)”的旧版模板并强制解绑物料。确定执行吗？'), () => {
        frappe.prompt([
            { label: '请输入 CLEANUP 确认', fieldname: 'confirm', fieldtype: 'Data', reqd: 1 }
        ], (data) => {
            if (data.confirm === 'CLEANUP') {
                frappe.call({
                    method: "junhai_custom.api.tax.bulk_cleanup_tax_templates",
                    args: { keyword: "(销项)" },
                    callback: function () {
                        frappe.call({
                            method: "junhai_custom.api.tax.bulk_cleanup_tax_templates",
                            args: { keyword: "(进项)" },
                            callback: function (r) {
                                frappe.show_alert({ message: __('旧版模板清理完成'), indicator: 'green' });
                            }
                        });
                    }
                });
            }
        }, __('安全验证'), __('执行清理'));
    });
}

// --- 同步逻辑 ---
function handle_sync(frm) {
    if (frm.is_dirty()) {
        frappe.msgprint(__('请先保存当前物料组的修改，再执行同步。'));
        return;
    }
    frappe.confirm(__('确定要根据当前税率 {0}% 同步至该组及其子组的所有物料吗？', [frm.doc.custom_standard_tax_rate]), () => {
        frappe.show_alert({ message: __('正在同步，请稍候...'), indicator: 'blue' });
        frappe.call({
            method: "junhai_custom.api.tax.sync_group_taxes_to_items",
            args: { item_group: frm.doc.name },
            callback: function (r) {
                if (r.message) {
                    frappe.msgprint(r.message.message);
                }
            }
        });
    });
}