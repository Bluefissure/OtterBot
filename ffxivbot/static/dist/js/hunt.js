var server = "lnxy";
var arr = true;
var hw = true;
var sb = true;
var cd = false;
var allServersButton = ["#lnxy", "#zszq", "#hyqd", "#mdn", "#syzd", "#jyzy", "#myc", "#yx", "#hyh", "#cft", "#sqh", "#byx", "#bjhx"]
var allServersHiddenTag = [".lnxy", ".zszq", ".hyqd", ".mdn", ".syzd", ".jyzy", ".myc", ".yx", ".hyh", ".cft", ".sqh", ".byx", ".bjhx"]

$(document).ready(function () {
    if (typeof Storage !== "undefined") {
        if (localStorage.getItem("server") === null) {
            localStorage.setItem("server", server);
        }
        if (localStorage.getItem("arr") === null) {
            localStorage.setItem("arr", arr);
        }
        if (localStorage.getItem("hw") === null) {
            localStorage.setItem("hw", hw);
        }
        if (localStorage.getItem("sb") === null) {
            localStorage.setItem("sb", sb);
        }
        if (localStorage.getItem("cd") === null) {
            localStorage.setItem("cd", cd);
        }
        server = localStorage.getItem("server");
        arr = localStorage.getItem("arr") === "true";
        hw = localStorage.getItem("hw") === "true";
        sb = localStorage.getItem("sb") === "true";
        cd = localStorage.getItem("cd") === "true";
    }
    updateHidden();
    setInterval('autoRefresh()', 300000);
});
$(document).ready(function () {
    $("#arr").on("click", function () {
        if (arr) {
            arr = false;
        } else if (!arr) {
            arr = true;
        }
        localStorage.setItem("arr", arr);
        updateHidden()
    });
    $("#hw").on("click", function () {
        if (hw) {
            hw = false;
        } else if (!hw) {
            hw = true;
        }
        localStorage.setItem("hw", hw);
        updateHidden()
    });
    $("#sb").on("click", function () {
        if (sb) {
            sb = false;
        } else if (!sb) {
            sb = true;
        }
        localStorage.setItem("sb", sb);
        updateHidden()
    });
    $("#cd").on("click", function () {
        if (cd) {
            cd = false;
        } else if (!cd) {
            cd = true;
        }
        localStorage.setItem("cd", cd);
        updateHidden()
    });
    $("#lnxy").on("click", function () {
        server = "lnxy";
        localStorage.setItem("server", "lnxy");
        updateHidden()
    });
    $("#zszq").on("click", function () {
        server = "zszq";
        localStorage.setItem("server", "zszq");
        updateHidden()
    });
    $("#hyqd").on("click", function () {
        server = "hyqd";
        localStorage.setItem("server", "hyqd");
        updateHidden()
    });
    $("#mdn").on("click", function () {
        server = "mdn";
        localStorage.setItem("server", "mdn");
        updateHidden()
    });
    $("#syzd").on("click", function () {
        server = "syzd";
        localStorage.setItem("server", "syzd");
        updateHidden()
    });
    $("#jyzy").on("click", function () {
        server = "jyzy";
        localStorage.setItem("server", "jyzy");
        updateHidden()
    });
    $("#myc").on("click", function () {
        server = "myc";
        localStorage.setItem("server", "myc");
        updateHidden()
    });
    $("#yx").on("click", function () {
        server = "yx";
        localStorage.setItem("server", "yx");
        updateHidden()
    });
    $("#hyh").on("click", function () {
        server = "hyh";
        localStorage.setItem("server", "hyh");
        updateHidden()
    });
    $("#cft").on("click", function () {
        server = "cft";
        localStorage.setItem("server", "cft");
        updateHidden()
    });
    $("#sqh").on("click", function () {
        server = "sqh";
        localStorage.setItem("server", "sqh");
        updateHidden()
    });
    $("#byx").on("click", function () {
        server = "byx";
        localStorage.setItem("server", "byx");
        updateHidden()
    });
    $("#bjhx").on("click", function () {
        server = "bjhx";
        localStorage.setItem("server", "bjhx");
        updateHidden()
    });
});

function updateHidden() {
    if (arr) {
        $(".arr").removeClass("hide");
        $("#arr").removeClass("btn-secondary");
    }
    if (!arr) {
        $(".arr").addClass("hide");
        $("#arr").addClass("btn-secondary");
    }
    if (hw) {
        $(".hw").removeClass("hide");
        $("#hw").removeClass("btn-secondary");
    }
    if (!hw) {
        $(".hw").addClass("hide");
        $("#hw").addClass("btn-secondary");
    }
    if (sb) {
        $(".sb").removeClass("hide");
        $("#sb").removeClass("btn-secondary");
    }
    if (!sb) {
        $(".sb").addClass("hide");
        $("#sb").addClass("btn-secondary");
    }
    if (cd){
        $(".notcd").addClass("hide-cd");
        $("#cd").removeClass("btn-secondary");
    }
    if (!cd){
        $(".notcd").removeClass("hide-cd");
        $("#cd").addClass("btn-secondary");
    }
    if (server === "lnxy") {
        // 将列表放进临时列表内
        let tempButtonList = allServersButton.concat();
        let tempHiddenTag = allServersHiddenTag.concat();
        // 移除列表内的拉诺西亚
        tempHiddenTag.splice(0, 1);
        tempButtonList.splice(0, 1);
        // 轮询并添加除拉诺西亚的各服狩猎怪表格的Class
        for (let i = 0; i < tempButtonList.length; i++) {
            $(tempButtonList[i]).addClass("btn-secondary");
            $(tempHiddenTag[i]).addClass("hide-server");
        }
        // 移除拉诺西亚的按钮和表格的Class
        $("#lnxy").removeClass("btn-secondary");
        $(".lnxy").removeClass("hide-server");
    }
    if (server === "zszq") {
        let tempButtonList = allServersButton.concat();
        let tempHiddenTag = allServersHiddenTag.concat();

        tempHiddenTag.splice(1, 1);
        tempButtonList.splice(1, 1);

        for (let i = 0; i < tempButtonList.length; i++) {
            $(tempButtonList[i]).addClass("btn-secondary");
            $(tempHiddenTag[i]).addClass("hide-server");
        }
        $("#zszq").removeClass("btn-secondary");
        $(".zszq").removeClass("hide-server");
    }
    if (server === "hyqd") {
        let tempButtonList = allServersButton.concat();
        let tempHiddenTag = allServersHiddenTag.concat();

        tempHiddenTag.splice(2, 1);
        tempButtonList.splice(2, 1);

        for (let i = 0; i < tempButtonList.length; i++) {
            $(tempButtonList[i]).addClass("btn-secondary");
            $(tempHiddenTag[i]).addClass("hide-server");
        }
        $("#hyqd").removeClass("btn-secondary");
        $(".hyqd").removeClass("hide-server");
    }
    if (server === "mdn") {
        let tempButtonList = allServersButton.concat();
        let tempHiddenTag = allServersHiddenTag.concat();

        tempHiddenTag.splice(3, 1);
        tempButtonList.splice(3, 1);

        for (let i = 0; i < tempButtonList.length; i++) {
            $(tempButtonList[i]).addClass("btn-secondary");
            $(tempHiddenTag[i]).addClass("hide-server");
        }
        $("#mdn").removeClass("btn-secondary");
        $(".mdn").removeClass("hide-server");
    }
    if (server === "syzd") {
        let tempButtonList = allServersButton.concat();
        let tempHiddenTag = allServersHiddenTag.concat();

        tempHiddenTag.splice(4, 1);
        tempButtonList.splice(4, 1);

        for (let i = 0; i < tempButtonList.length; i++) {
            $(tempButtonList[i]).addClass("btn-secondary");
            $(tempHiddenTag[i]).addClass("hide-server");
        }
        $("#syzd").removeClass("btn-secondary");
        $(".syzd").removeClass("hide-server");
    }
    if (server === "jyzy") {
        let tempButtonList = allServersButton.concat();
        let tempHiddenTag = allServersHiddenTag.concat();

        tempHiddenTag.splice(5, 1);
        tempButtonList.splice(5, 1);

        for (let i = 0; i < tempButtonList.length; i++) {
            $(tempButtonList[i]).addClass("btn-secondary");
            $(tempHiddenTag[i]).addClass("hide-server");
        }
        $("#jyzy").removeClass("btn-secondary");
        $(".jyzy").removeClass("hide-server");
    }
    if (server === "myc") {
        let tempButtonList = allServersButton.concat();
        let tempHiddenTag = allServersHiddenTag.concat();

        tempHiddenTag.splice(6, 1);
        tempButtonList.splice(6, 1);

        for (let i = 0; i < tempButtonList.length; i++) {
            $(tempButtonList[i]).addClass("btn-secondary");
            $(tempHiddenTag[i]).addClass("hide-server");
        }
        $("#myc").removeClass("btn-secondary");
        $(".myc").removeClass("hide-server");
    }
    if (server === "yx") {
        let tempButtonList = allServersButton.concat();
        let tempHiddenTag = allServersHiddenTag.concat();

        tempHiddenTag.splice(7, 1);
        tempButtonList.splice(7, 1);

        for (let i = 0; i < tempButtonList.length; i++) {
            $(tempButtonList[i]).addClass("btn-secondary");
            $(tempHiddenTag[i]).addClass("hide-server");
        }
        $("#yx").removeClass("btn-secondary");
        $(".yx").removeClass("hide-server");
    }
    if (server === "hyh") {
        let tempButtonList = allServersButton.concat();
        let tempHiddenTag = allServersHiddenTag.concat();

        tempHiddenTag.splice(8, 1);
        tempButtonList.splice(8, 1);

        for (let i = 0; i < tempButtonList.length; i++) {
            $(tempButtonList[i]).addClass("btn-secondary");
            $(tempHiddenTag[i]).addClass("hide-server");
        }
        $("#hyh").removeClass("btn-secondary");
        $(".hyh").removeClass("hide-server");
    }
    if (server === "cft") {
        let tempButtonList = allServersButton.concat();
        let tempHiddenTag = allServersHiddenTag.concat();

        tempHiddenTag.splice(9, 1);
        tempButtonList.splice(9, 1);

        for (let i = 0; i < tempButtonList.length; i++) {
            $(tempButtonList[i]).addClass("btn-secondary");
            $(tempHiddenTag[i]).addClass("hide-server");
        }
        $("#cft").removeClass("btn-secondary");
        $(".cft").removeClass("hide-server");
    }
    if (server === "sqh") {
        let tempButtonList = allServersButton.concat();
        let tempHiddenTag = allServersHiddenTag.concat();

        tempHiddenTag.splice(10, 1);
        tempButtonList.splice(10, 1);

        for (let i = 0; i < tempButtonList.length; i++) {
            $(tempButtonList[i]).addClass("btn-secondary");
            $(tempHiddenTag[i]).addClass("hide-server");
        }
        $("#sqh").removeClass("btn-secondary");
        $(".sqh").removeClass("hide-server");
    }
    if (server === "byx") {
        let tempButtonList = allServersButton.concat();
        let tempHiddenTag = allServersHiddenTag.concat();

        tempHiddenTag.splice(11, 1);
        tempButtonList.splice(11, 1);

        for (let i = 0; i < tempButtonList.length; i++) {
            $(tempButtonList[i]).addClass("btn-secondary");
            $(tempHiddenTag[i]).addClass("hide-server");
        }
        $("#byx").removeClass("btn-secondary");
        $(".byx").removeClass("hide-server");
    }
    if (server === "bjhx") {
        let tempButtonList = allServersButton.concat();
        let tempHiddenTag = allServersHiddenTag.concat();

        tempHiddenTag.splice(12, 1);
        tempButtonList.splice(12, 1);

        for (let i = 0; i < tempButtonList.length; i++) {
            $(tempButtonList[i]).addClass("btn-secondary");
            $(tempHiddenTag[i]).addClass("hide-server");
        }
        $("#bjhx").removeClass("btn-secondary");
        $(".bjhx").removeClass("hide-server");
    }
}

function autoRefresh() {
    window.location.reload();
}
