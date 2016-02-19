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
                if (!called) {
                    called = true;
                    window.location.href = "itms-services://?action=download-manifest&url=https://deniss-MacBook-Pro.local:8443/ios/plist/"+app_identifier+".plist";
                }
            }
        }
    })
}