/**
 * Created by denislavrov on 18/02/16.
 */

var app_identifier = "";
var called = false;

function checker(app_id){
    app_identifier = app_id;
    setInterval(checkBuild, 3000);
}

function checkBuild(){
    $.ajax({
        url: "/ios/" + app_identifier + "/build_status",
        success: function(data) {
            if (data == "Done"){
                //window.location.href =  "/ios/" + app_identifier + "/plist";
                if (!called) {
                    called = true;
                    window.location.href = "itms-services://?action=download-manifest&url=https://deniss-MacBook-Pro.local:8443/static/com.bahus.ForceTorch.plist";
                    //window.location.href = "itms-services://?action=download-manifest&url=https://dl.dropboxusercontent.com/s/cuj0n5m3i83fp0j/com.bahus.ForceTorch.plist";
                }
            }
        }
    })
}