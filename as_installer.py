import os
import mmap
import subprocess
import apps
import plistlib


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


def get_identities(developer=True, distribution=False):
	output = subprocess.check_output(["security", "find-identity", "-p", "codesigning"], universal_newlines=True)
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


def local_profiles():
	user_dir = os.path.expanduser("~")
	profiles_dir = user_dir+"/Library/MobileDevice/Provisioning Profiles/"
	profiles_files = os.listdir(profiles_dir)
	profiles = []
	for profile_file in profiles_files:
		profiles.append(profiles_dir+profile_file)
	return profiles


def filtered_profiles(team=None, app_id=None, type=None):
	profile_dicts = {}
	filtered = []
	for profile_path in local_profiles():
		plist_string = plist_from_profile(profile_path)
		plist_dict = plistlib.loads(plist_string)
		profile_dicts[profile_path] = plist_dict
	profiles = list(profile_dicts.keys())
	if team is None:
		filtered = profiles
	else:
		for profile in profiles:
			profile_dict = profile_dicts[profile]
			if profile_dict["ApplicationIdentifierPrefix"][0] == team:
				filtered.append(profile)
	if app_id is not None:
		profiles = filtered
		filtered = []
		for profile in profiles:
			profile_dict = profile_dicts[profile]
			prof_app_id = profile_dict["Entitlements"]["application-identifier"]
			prof_app_id = prof_app_id.replace(profile_dict["ApplicationIdentifierPrefix"][0]+".", "")
			if prof_app_id == app_id:
				filtered.append(profile)
	# return dict[name]->file
	prof_name_dict = {}
	for profile in filtered:
		prof_dict = profile_dicts[profile]
		prof_name_dict[prof_dict["Name"]] = profile
	return prof_name_dict


def plist_from_profile(profile_path):
	out = subprocess.check_output(["security", 'cms', "-D", "-i", profile_path])
	return out


def team_id_from_identity(identity):
	start = identity.find("(")
	end = identity.rfind(")")
	return identity[start+1:end]


def build_workspace(app_workspace, scheme, signing_identity):
	if app_workspace is not None:
		datapath = os.path.dirname(os.path.abspath(app_workspace))
		os.system("xcodebuild -derivedDataPath \"{}/\" -workspace {} -scheme {} CODE_SIGN_IDENTITY=\"{}\"".format(datapath, app_workspace, scheme, signing_identity))


def build_project(app_proj, signing_identity):
	if app_proj is not None:
		datapath = os.path.dirname(os.path.abspath(app_proj))
		os.system("xcodebuild -derivedDataPath \"{}/\" -project {} CODE_SIGN_IDENTITY=\"{}\"".format(datapath, app_proj, signing_identity))


def build_prep(app_path, new_group_id):
	check_install_dependencies(app_path)
	bundle_id = find_bundle_id(app_path)
	if bundle_id is None:
		print("Could not find the bundle id")
		exit(1)
	print(bundle_id)
	replace_bundle_id(app_path, bundle_id, new_group_id)

#build("github.fullstackio.FlappySwift", "/Users/denislavrov/Library/Application Support/AppSource/build", "com.bahus")
#print(get_identities())

#print(get_schemes("/Users/denislavrov/Library/Application Support/AppSource/build/github.AaronRandall.Megabite/Megabite.xcworkspace"))
#print(team_id_from_identity("iPhone Distribution: Denis Lavrov (THZ88VX669)"))