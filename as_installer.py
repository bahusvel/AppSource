import os
import mmap
import subprocess
import apps


def findFileByType(appcontent, extension):
	for file in appcontent:
		if file.endswith(extension):
			return file
	return None


def deep_folder_find(app_path, extension):
	files = []
	for path, dirs, _ in os.walk(app_path):
		for ddir in dirs:
			if ddir.endswith(extension):
				files.append(path+"/"+ddir)
	return files


def deep_file_find(path, ends):
	result_files = []
	for path, _, files in os.walk(path):
		for file in files:
			full_path = path+"/"+file
			if full_path.endswith(ends):
				result_files.append(full_path)
	return result_files


def find_bundle_id(appath):
	for path, dirs, _ in os.walk(appath):
		for ddir in dirs:
			if ddir.endswith(".xcodeproj") and ddir != "Pods.xcodeproj":
				pbxpath = path + "/" + ddir + "/project.pbxproj"
				pbxfile = open(pbxpath)
				pbxmem = mmap.mmap(pbxfile.fileno(), 0, access=mmap.ACCESS_READ)
				searchstr = b"PRODUCT_BUNDLE_IDENTIFIER = "
				bundle_start = pbxmem.find(searchstr)
				if bundle_start > 0:
					bundle_off = pbxmem[bundle_start:].find(b";")
					bundle_id = pbxmem[bundle_start + len(searchstr): bundle_start+bundle_off].decode("UTF-8")
					group_id = bundle_id[:bundle_id.rfind(".")]
					group_id = group_id.replace("\"", "")
					return group_id
	# check the info plist
	for plist in deep_file_find(appath, "Info.plist"):
		with open(plist, 'r') as plistfile:
			plistmem = mmap.mmap(plistfile.fileno(), 0, access=mmap.ACCESS_READ)
			searchstr = b"<key>CFBundleIdentifier</key>"
			identifierkey = plistmem.find(searchstr)
			if identifierkey > 0:
				identifier = plistmem[len(searchstr)+identifierkey:]
				id_start = identifier.find(b"<string>") + len(b"<string>")
				id_end = identifier.find(b"</string>")
				full_id = identifier[id_start:id_end]
				bundle_id = full_id[:full_id.rfind(b".")]
				return bundle_id.decode("ascii")


def replace_bundle_id(appath, old_group_id, new_group_id):
	os.chdir(appath)
	os.system("LC_ALL=C find . -type f -exec sed -i '' 's/"+old_group_id+"/"+new_group_id+"/g' {} +")
	return True


def get_identities():
	output = subprocess.check_output(["security", "find-identity", "-v", "-p", "codesigning"], universal_newlines=True)
	identities = set()
	for line in output.split("\n"):
		left = line.find("\"")
		if left > 0:
			right = line.find("\"", left+1)
			name = line[left+1:right]
			if "iPhone Developer:" in name:
				identities.add(name)
	return list(identities)


def install_to_device(bundle_path):
	# requires https://github.com/phonegap/ios-deploy
	os.system("ios-deploy --justlaunch --bundle \"{}\"".format(bundle_path))


def check_install_dependencies(app_path):
	os.chdir(app_path)
	appcontent = os.listdir(app_path)
	if 'Podfile' in appcontent:
		print("You app uses CocoaPods, installing the required pods now")
		os.system("pod install")
	elif 'Cartfile' in appcontent:
		print("Carthage not supported yet, sorry I will add support soon :)") # TODO
	else:
		print("No dependency manager detected, building normally")


def get_workspace(app_path):
	appcontent = os.listdir(app_path)
	appworkspace = findFileByType(appcontent, ".xcworkspace")
	return appworkspace


def get_project(app_path):
	appcontent = os.listdir(app_path)
	app_proj = findFileByType(appcontent, ".xcodeproj")
	return app_proj


def refresh_workspaces(app_proj):
	command = apps.STORAGECLI+"/refresh_workspaces.rb"
	os.system("ruby \"{}\" \"{}\"".format(command, app_proj))


def get_schemes(app_workspace):
	schemes = []
	output = subprocess.check_output(["xcodebuild", "-list", "-workspace", app_workspace], universal_newlines=True)
	schemes_start = output.find("Schemes:") + len("Schemes:") + 1
	if schemes_start > 0:
		for scheme in output[schemes_start:].splitlines():
			nscheme = scheme.replace(" ", "")
			if nscheme != "":
				schemes.append(nscheme)
	return schemes


def build_workspace(app_workspace, scheme, signing_identity):
	if app_workspace is not None:
		os.system("xcodebuild -workspace {} -scheme {} CODE_SIGN_IDENTITY=\"{}\"".format(app_workspace, scheme, signing_identity))


def build_project(app_proj, signing_identity):
	if app_proj is not None:
		os.system("xcodebuild -project {} CODE_SIGN_IDENTITY=\"{}\"".format(app_proj, signing_identity))


def build_prep(app_path, new_group_id):
	check_install_dependencies(app_path)
	bundle_id = find_bundle_id(app_path)
	if bundle_id is None:
		Exception("Could not find the bundle id")
		exit(1)
	print(bundle_id)
	replace_bundle_id(app_path, bundle_id, new_group_id)

#build("github.fullstackio.FlappySwift", "/Users/denislavrov/Library/Application Support/AppSource/build", "com.bahus")
#print(get_identities())

#print(get_schemes("/Users/denislavrov/Library/Application Support/AppSource/build/github.AaronRandall.Megabite/Megabite.xcworkspace"))