frappe.pages['coa-manager'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: '君海科目表管理',
		single_column: true
	});

	page.main.html(`
        <div style="padding: 50px; text-align: center;">
            <h3>科目表模板部署工具</h3>
            <p>点击下方按钮，将“君海标准科目表”安装到 ERPNext 核心目录中，以便在创建公司时使用。</p>
            <br>
            <button class="btn btn-primary btn-lg" id="btn-install">
                安装/更新 模板
            </button>
            <button class="btn btn-danger btn-lg" id="btn-remove" style="margin-left: 20px;">
                卸载/重置 模板
            </button>
            <br><br>
            <div id="status-area" style="margin-top: 20px; font-weight: bold;"></div>
        </div>
    `);

	// 绑定安装事件
	page.main.find('#btn-install').on('click', function () {
		frappe.call({
			method: 'junhai_custom.utils.coa_manager.install_coa_template',
			callback: function (r) {
				if (r.message.status === 'success') {
					frappe.msgprint(r.message.message);
					page.main.find('#status-area').html('<span style="color:green">已安装</span>');
				} else {
					frappe.throw(r.message.message);
				}
			}
		});
	});

	// 绑定卸载事件
	page.main.find('#btn-remove').on('click', function () {
		frappe.call({
			method: 'junhai_custom.utils.coa_manager.remove_coa_template',
			callback: function (r) {
				frappe.msgprint(r.message.message);
				page.main.find('#status-area').html('<span style="color:red">未安装</span>');
			}
		});
	});
}