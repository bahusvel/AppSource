import flask
from flask import Flask
import apps
import os

app = Flask("AppSource")


@app.route("/", methods=['GET'])
def root():
	return "<a href=\"/ios\">iOS Apps</a>"


@app.route("/ios")
def ios_apps():
	index_apps = os.listdir(apps.STORAGEINDEX+"/ios")
	apps_html = ""
	for index_app in index_apps:
		app_name = index_app.replace(".json", "")
		apps_html += "<a href=\"/ios/{}\">{}</a>\n<br>".format(app_name, app_name)
	return apps_html


@app.route("/ios/<appname>")
def ios_app(appname):
	return appname


@app.route("/ios/<appname>/install")
def install_ios(appname):
	return "plist"


app.debug = True
app.run(host='0.0.0.0', port=8080)
