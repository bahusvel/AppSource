/**
 * Created by denislavrov on 18/02/16.
 */

var app_identifier = "";

function checker(app_id){
    app_identifier = app_id;
    setInterval(checkBuild, 1000);
}

function checkBuild(){
    $.ajax({
        url: "/ios/" + app_identifier + "/build_status",
        success: function(data) {
            if (data == "Done"){
                window.location.href =  "/ios/" + app_identifier + "/plist";
            }
        }
    })
}