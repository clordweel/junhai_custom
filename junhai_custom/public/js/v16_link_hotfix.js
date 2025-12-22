$(document).on('app_ready', function () {
    console.log("v16_link_hotfix.js loaded.");
    // 监听路由变化和初次加载，确保脚本在每次页面加载/切换时都运行

    // 立即执行一次修复
    fixBrokenLinks();

    // 监听路由变化 (适用于单页应用导航)
    frappe.router.on('change', function () {
        // 延迟执行，确保新页面内容（链接）已经完全渲染完毕
        setTimeout(fixBrokenLinks, 300);
    });


    /**
     * 查找页面上所有<a>标签中错误的 '/app/' 路径，并替换为正确的 '/desk/'
     */
    function fixBrokenLinks() {
        // 查找页面上所有<a>标签（链接）
        const links = document.querySelectorAll('a');

        links.forEach(link => {
            let currentHref = link.getAttribute('href');

            // 检查链接是否是相对路径，并且包含了错误的 '/app/' 路径
            if (currentHref && currentHref.startsWith('/app/')) {

                // 将错误的 '/app/' 替换为正确的 '/desk/'
                let newHref = currentHref.replace('/app/', '/desk/');

                // 更新链接的 href 属性
                link.setAttribute('href', newHref);

                // (可选) 打印日志： console.log(`Link Fixed: ${currentHref} -> ${newHref}`);
            }
        });
    }
});
