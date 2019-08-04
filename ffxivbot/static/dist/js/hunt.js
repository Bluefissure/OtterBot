var server = "lnxy";
var arr = true;
var hw = true;
var sb = true;
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
        server = localStorage.getItem("server");
        arr = localStorage.getItem("arr") === "true";
        hw = localStorage.getItem("hw") === "true";
        sb = localStorage.getItem("sb") === "true";
    }
    updateHidden()
    setInterval('autoRefresh()',300000);
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
            $(tempHiddenTag[i]).addClass("hidden");
        }
        // 移除拉诺西亚的按钮和表格的Class
        $("#lnxy").removeClass("btn-secondary");
        $(".lnxy").removeClass("hidden");
    }
    if (server === "zszq") {
        let tempButtonList = allServersButton.concat();
        let tempHiddenTag = allServersHiddenTag.concat();

        tempHiddenTag.splice(1, 1);
        tempButtonList.splice(1, 1);

        for (let i = 0; i < tempButtonList.length; i++) {
            $(tempButtonList[i]).addClass("btn-secondary");
            $(tempHiddenTag[i]).addClass("hidden");
        }
        $("#zszq").removeClass("btn-secondary");
        $(".zszq").removeClass("hidden");
    }
    if (server === "hyqd") {
        let tempButtonList = allServersButton.concat();
        let tempHiddenTag = allServersHiddenTag.concat();

        tempHiddenTag.splice(2, 1);
        tempButtonList.splice(2, 1);

        for (let i = 0; i < tempButtonList.length; i++) {
            $(tempButtonList[i]).addClass("btn-secondary");
            $(tempHiddenTag[i]).addClass("hidden");
        }
        $("#hyqd").removeClass("btn-secondary");
        $(".hyqd").removeClass("hidden");
    }
    if (server === "mdn") {
        let tempButtonList = allServersButton.concat();
        let tempHiddenTag = allServersHiddenTag.concat();

        tempHiddenTag.splice(3, 1);
        tempButtonList.splice(3, 1);

        for (let i = 0; i < tempButtonList.length; i++) {
            $(tempButtonList[i]).addClass("btn-secondary");
            $(tempHiddenTag[i]).addClass("hidden");
        }
        $("#mdn").removeClass("btn-secondary");
        $(".mdn").removeClass("hidden");
    }
    if (server === "syzd") {
        let tempButtonList = allServersButton.concat();
        let tempHiddenTag = allServersHiddenTag.concat();

        tempHiddenTag.splice(4, 1);
        tempButtonList.splice(4, 1);

        for (let i = 0; i < tempButtonList.length; i++) {
            $(tempButtonList[i]).addClass("btn-secondary");
            $(tempHiddenTag[i]).addClass("hidden");
        }
        $("#syzd").removeClass("btn-secondary");
        $(".syzd").removeClass("hidden");
    }
    if (server === "jyzy") {
        let tempButtonList = allServersButton.concat();
        let tempHiddenTag = allServersHiddenTag.concat();

        tempHiddenTag.splice(5, 1);
        tempButtonList.splice(5, 1);

        for (let i = 0; i < tempButtonList.length; i++) {
            $(tempButtonList[i]).addClass("btn-secondary");
            $(tempHiddenTag[i]).addClass("hidden");
        }
        $("#jyzy").removeClass("btn-secondary");
        $(".jyzy").removeClass("hidden");
    }
    if (server === "myc") {
        let tempButtonList = allServersButton.concat();
        let tempHiddenTag = allServersHiddenTag.concat();

        tempHiddenTag.splice(6, 1);
        tempButtonList.splice(6, 1);

        for (let i = 0; i < tempButtonList.length; i++) {
            $(tempButtonList[i]).addClass("btn-secondary");
            $(tempHiddenTag[i]).addClass("hidden");
        }
        $("#myc").removeClass("btn-secondary");
        $(".myc").removeClass("hidden");
    }
    if (server === "yx") {
        let tempButtonList = allServersButton.concat();
        let tempHiddenTag = allServersHiddenTag.concat();

        tempHiddenTag.splice(7, 1);
        tempButtonList.splice(7, 1);

        for (let i = 0; i < tempButtonList.length; i++) {
            $(tempButtonList[i]).addClass("btn-secondary");
            $(tempHiddenTag[i]).addClass("hidden");
        }
        $("#yx").removeClass("btn-secondary");
        $(".yx").removeClass("hidden");
    }
    if (server === "hyh") {
        let tempButtonList = allServersButton.concat();
        let tempHiddenTag = allServersHiddenTag.concat();

        tempHiddenTag.splice(8, 1);
        tempButtonList.splice(8, 1);

        for (let i = 0; i < tempButtonList.length; i++) {
            $(tempButtonList[i]).addClass("btn-secondary");
            $(tempHiddenTag[i]).addClass("hidden");
        }
        $("#hyh").removeClass("btn-secondary");
        $(".hyh").removeClass("hidden");
    }
    if (server === "cft") {
        let tempButtonList = allServersButton.concat();
        let tempHiddenTag = allServersHiddenTag.concat();

        tempHiddenTag.splice(9, 1);
        tempButtonList.splice(9, 1);

        for (let i = 0; i < tempButtonList.length; i++) {
            $(tempButtonList[i]).addClass("btn-secondary");
            $(tempHiddenTag[i]).addClass("hidden");
        }
        $("#cft").removeClass("btn-secondary");
        $(".cft").removeClass("hidden");
    }
    if (server === "sqh") {
        let tempButtonList = allServersButton.concat();
        let tempHiddenTag = allServersHiddenTag.concat();

        tempHiddenTag.splice(10, 1);
        tempButtonList.splice(10, 1);

        for (let i = 0; i < tempButtonList.length; i++) {
            $(tempButtonList[i]).addClass("btn-secondary");
            $(tempHiddenTag[i]).addClass("hidden");
        }
        $("#sqh").removeClass("btn-secondary");
        $(".sqh").removeClass("hidden");
    }
    if (server === "byx") {
        let tempButtonList = allServersButton.concat();
        let tempHiddenTag = allServersHiddenTag.concat();

        tempHiddenTag.splice(11, 1);
        tempButtonList.splice(11, 1);

        for (let i = 0; i < tempButtonList.length; i++) {
            $(tempButtonList[i]).addClass("btn-secondary");
            $(tempHiddenTag[i]).addClass("hidden");
        }
        $("#byx").removeClass("btn-secondary");
        $(".byx").removeClass("hidden");
    }
    if (server === "bjhx") {
        let tempButtonList = allServersButton.concat();
        let tempHiddenTag = allServersHiddenTag.concat();

        tempHiddenTag.splice(12, 1);
        tempButtonList.splice(12, 1);

        for (let i = 0; i < tempButtonList.length; i++) {
            $(tempButtonList[i]).addClass("btn-secondary");
            $(tempHiddenTag[i]).addClass("hidden");
        }
        $("#bjhx").removeClass("btn-secondary");
        $(".bjhx").removeClass("hidden");
    }
}
function autoRefresh()
{
       window.location.reload();
}
