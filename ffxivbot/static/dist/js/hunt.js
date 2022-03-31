let server = "myc";
let allServers = ["hyh", "syzd", "hyqd", "lnxy", "myc", "yzhy", "wxxr", "cxwz", "cft", "sqh", "byx", "bjhx", "lrzq", "fxzj", "lcsd", "zszq", "yx", "jyzy", "mdn", "hmcw", "rfhw", "hpy", "sjt", "ylh", "tyhh", "yxjd", "hcc"];
let allServersButton = ["#hyh", "#syzd", "#hyqd", "#lnxy", "#myc", "#yzhy", "#wxxr", "#cxwz", "#cft", "#sqh", "#byx", "#bjhx", "#lrzq", "#fxzj", "#lcsd", "#zszq", "#yx", "#jyzy", "#mdn", "#hmcw", "#rfhw", "#hpy", "#sjt", "#ylh", "#tyhh", "#yxjd", "#hcc"];
let allServersHiddenTag = [".hyh", ".syzd", ".hyqd", ".lnxy", ".myc", ".yzhy", ".wxxr", ".cxwz", ".cft", ".sqh", ".byx", ".bjhx", ".lrzq", ".fxzj", ".lcsd", ".zszq", ".yx", ".jyzy", ".mdn", ".hmcw", ".rfhw", ".hpy", ".sjt", ".ylh", ".tyhh", ".yxjd", ".hcc"];


$(document).ready(function () {
    if (typeof Storage !== "undefined") {
        if (localStorage.getItem("server") === null) {
            localStorage.setItem("server", server);
        }
        if (localStorage.getItem("arr") === null) {
            localStorage.setItem("arr", true);
        }
        if (localStorage.getItem("hw") === null) {
            localStorage.setItem("hw", true);
        }
        if (localStorage.getItem("sb") === null) {
            localStorage.setItem("sb", true);
        }
        if (localStorage.getItem("shb") === null) {
            localStorage.setItem("shb", true);
        }
        if (localStorage.getItem("ew") === null) {
            localStorage.setItem("ew", true);
        }
        if (localStorage.getItem("cd") === null) {
            localStorage.setItem("cd", false);
        }
        server = localStorage.getItem("server");
    }
    let buttons = ["arr", "hw", "sb", "shb", "ew", "cd"];
    for (let button_id in buttons) {
        let button = buttons[button_id];
        $("#"+button).on("click", function () {
            localStorage.setItem(button, !(localStorage.getItem(button) === "true"));
            updateHidden();
        });
    }
    for (let server_id in allServers) {
        let server = allServers[server_id];
        $("#"+server).on("click", function () {
            localStorage.setItem("server", server);
            updateHidden();
        });
    }
    updateHidden();
    setInterval('autoRefresh()', 300000);
});

function updateHidden() {
    let buttons = ["arr", "hw", "sb", "shb", "ew"];
    for (let button_id in buttons) {
        let button = buttons[button_id];
        if (localStorage.getItem(button) === "true") {
            $("."+button).removeClass("hide-monster");
            $("#"+button).removeClass("btn-secondary");
        } else {
            $("."+button).addClass("hide-monster");
            $("#"+button).addClass("btn-secondary");
        }
    }
    if (localStorage.getItem("cd") === "true"){
        $(".notcd").addClass("hide-cd");
        $("#cd").removeClass("btn-secondary");
    } else {
        $(".notcd").removeClass("hide-cd");
        $("#cd").addClass("btn-secondary");
    }
    let server = localStorage.getItem("server");
    let tempButtonList = allServersButton.concat();
    let tempHiddenTag = allServersHiddenTag.concat();
    let server_idx = tempHiddenTag.indexOf("."+server);
    if (server_idx < 0)
        return
    tempHiddenTag.splice(server_idx, 1);
    tempButtonList.splice(server_idx, 1);
    for (let i = 0; i < tempButtonList.length; i++) {
        $(tempButtonList[i]).addClass("btn-secondary");
        $(tempHiddenTag[i]).addClass("hide-server");
    }
    $("#"+server).removeClass("btn-secondary");
    $("."+server).removeClass("hide-server");
}

function autoRefresh() {
    window.location.reload();
}
