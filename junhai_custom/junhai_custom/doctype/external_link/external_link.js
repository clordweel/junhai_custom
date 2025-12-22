frappe.ui.form.on('External Link', {
    refresh: function (frm) {
        // 1. 获取 Hash 标识
        const current_hash = window.location.hash;

        // 2. 识别跳转指令
        if (current_hash.includes('jump') && frm.doc.target_link) {

            frappe.show_alert({
                message: __("正在执行跳转配置..."),
                indicator: 'blue'
            });

            // 延迟执行，确保页面数据加载完毕
            setTimeout(() => {
                // 判断是否在新标签页打开
                if (frm.doc.new_tab) {
                    window.open(frm.doc.target_link, "_blank");
                } else {
                    window.location.href = frm.doc.target_link;
                }

                // 判断跳转后是否返回之前页面
                // 注意：如果是在当前页跳转(new_tab=0)，返回逻辑通常在点击浏览器后退时生效
                // 如果是新标签页跳转(new_tab=1)，我们可以让原页面直接退回列表页
                if (frm.doc.return_to_previous) {
                    // 如果是跳转到新标签，ERPNext 这一页立刻返回上一路径（通常是列表）
                    if (frm.doc.new_tab) {
                        window.history.back();
                    } else {
                        // 如果是当前页跳转，我们无法控制外部站点的行为，
                        // 但可以在 URL 中尝试修改历史记录（此场景较复杂，通常依赖浏览器后退）
                        console.log("当前页跳转，请手动点击浏览器后退返回。");
                    }
                }
            }, 600);
        }

        // 3. 同时也更新手动按钮的逻辑，使其遵循勾选框设置
        if (frm.doc.target_link) {
            frm.add_custom_button(__('Jump To'), function () {
                if (frm.doc.new_tab) {
                    window.open(frm.doc.target_link, "_blank");
                } else {
                    window.location.href = frm.doc.target_link;
                }

                if (frm.doc.return_to_previous && frm.doc.new_tab) {
                    window.history.back();
                }
            });
        }
    }
});