from flask import Flask, url_for, Response, request, redirect
import apps
import os
import threading
import time
from as_fscontroller import read_appfile
from flask import make_response
from functools import wraps, update_wrapper
from datetime import datetime

app = Flask("AppSource")
STORAGEOTA = apps.APPSTORAGE + "/ota"
apps.check_create(STORAGEOTA)
STORAGECERTS = apps.APPSTORAGE + "/certs"
apps.check_create(STORAGECERTS)


def nocache(view):
	@wraps(view)
	def no_cache(*args, **kwargs):
		response = make_response(view(*args, **kwargs))
		response.headers['Last-Modified'] = datetime.now()
		response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
		response.headers['Pragma'] = 'no-cache'
		response.headers['Expires'] = '-1'
		return response

	return update_wrapper(no_cache, view)


@app.route("/", methods=['GET'])
def root():
	return """
	<a href="{}">iOS Apps</a><br>
	<a href="{}">Download Certificate</a><br>
	""".format(url_for("ios_apps"), url_for("cert"))


@app.route("/ios")
def ios_apps():
	index_apps = os.listdir(apps.STORAGEINDEX + "/ios")
	apps_html = ""
	for index_app in index_apps:
		app_id = index_app[:-5]
		app_dict = read_appfile(apps.STORAGEINDEX + "/ios/" + index_app)
		apps_html += "<a href=\"{}\">{}</a>\n<br>".format(url_for("ios_app", app_id=app_id), app_dict["name"])
	return apps_html


@app.route("/ios/<app_id>")
def ios_app(app_id):
	app_file = app_id + ".json"
	app_dict = read_appfile(apps.STORAGEINDEX + "/ios/" + app_file)
	return """
	<h1>{}</h1>
	<a href="{}"><button type="button">Install</button></a><br>
	<a href="{}">Repository</a><br>
	<p>{}</p><br>
	""".format(app_dict["name"], url_for("install_ios", app_id=app_id), app_dict["repo"], app_dict["description"])


@app.route("/ios/<app_id>/install")
@nocache
def install_ios(app_id):
	threading.Thread(target=build_backend, args=(app_id,)).start()
	return """
	<head>
	</head>
	<body>
	<script src="//ajax.googleapis.com/ajax/libs/jquery/1.6.4/jquery.min.js"></script>
	<script src="{}"></script>
	<script>checker('{}')</script>
	<div id="loader" class="loader">Please wait your app is being built</div>
	</body>
	""".format(url_for("static", filename="checkBuild.js"), app_id)


def build_backend(app_id):
	print("Building the App")
	app_file = app_id + ".json"
	app_dict = read_appfile(apps.STORAGEINDEX + "/ios/" + app_file)
	build_lock = "{}/{}.lock".format(STORAGEOTA, app_id)
	if not os.path.exists(build_lock):
		open(build_lock, 'w').close()
	else:
		print("App is already building!!!")
	time.sleep(1)
	os.remove(build_lock)
	print("Finished building the app")


@app.route("/ios/<app_id>/build_status")
@nocache
def build_status(app_id):
	build_lock = "{}/{}.lock".format(STORAGEOTA, app_id)
	if os.path.exists(build_lock):
		return "Build"
	else:
		return "Done"


@app.route("/ios/<app_id>/plist")
@nocache
def app_plist(app_id):
	return """
	<a href="itms-services://?action=download-manifest&url={}">Click me!<a>
	""".format("https://192.168.3.6:8080/static/app.ipa", time.time())


@app.route("/ios/<app_id>/real")
@nocache
def app_real_plist(app_id):
	with open("static/com.bahus.ForceTorch.plist") as plist_file:
		return plist_file.read()


@app.route("/ios/<app_id>/ipa/app.ipa")
@nocache
def app_ipa(app_id):
	with open("static/app.ipa", "rb") as ipa_file:
		return ipa_file


@app.route("/cert/ssl.p12")
def cert():
	with open(STORAGECERTS+"/pkcs.p12", 'rb') as cert:
		response = Response(cert.read(), mimetype="application/x-pkcs12")
		return response


def run_app():
	if not os.path.exists(STORAGECERTS + "/cert.pem"):
		cdir = os.getcwd()
		os.chdir(STORAGECERTS)
		os.system(
			"openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes")
		os.system("openssl pkcs12 -export -nodes -out pkcs.p12 -in cert.pem -inkey key.pem -name AppSource -passout pass:appsource")
		os.chdir(cdir)
	cert = STORAGECERTS + "/cert.pem"
	key = STORAGECERTS + "/key.pem"
	app.debug = True
	app.run(host='0.0.0.0', port=8080, ssl_context=(cert, key))


if __name__ == '__main__':
	run_app()
