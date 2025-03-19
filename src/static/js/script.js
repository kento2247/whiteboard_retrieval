document.addEventListener("DOMContentLoaded", function () {
    const menuBtn = document.getElementById("menu-btn");
    const menu = document.getElementById("menu");
    const overlay = document.createElement("div");

    // オーバーレイ要素を作成
    overlay.classList.add("menu-overlay");
    document.body.appendChild(overlay);

    // メニューを開閉する関数
    function toggleMenu() {
        menu.classList.toggle("open");
        overlay.classList.toggle("show");

        // メニューが開いたらオーバーレイの left 位置を調整
        if (menu.classList.contains("open")) {
            overlay.style.left = `${menu.offsetWidth}px`; // メニューの幅分ずらす
            overlay.style.width = `calc(100% - ${menu.offsetWidth}px)`;
        } else {
            overlay.style.left = "100%"; // 画面外に移動して消す
        }
    }

    // ハンバーガーボタンをクリックで開閉
    menuBtn.addEventListener("click", toggleMenu);

    // オーバーレイをクリックしたらメニューを閉じる
    overlay.addEventListener("click", function () {
        menu.classList.remove("open");
        overlay.classList.remove("show");
    });
});
