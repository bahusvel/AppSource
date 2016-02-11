import os
import mmap
import subprocess


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
					group_id = bundle_id[1:bundle_id.rfind(".")]
					return group_id


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


def build(appid, buildpath, new_group_id, signing_identity):
	app_path = buildpath + "/" + appid
	os.chdir(app_path)
	appcontent = os.listdir(app_path)

	if 'Podfile' in appcontent:
		print("You app uses CocoaPods, installing the required pods now")
		os.system("pod install")
	elif 'Cartfile' in appcontent:
		print("Carthage not supported yet, sorry I will add support soon :)") # TODO
	else:
		print("No dependency manager detected, building normally")

	bundle_id = find_bundle_id(app_path)
	if bundle_id is None:
		Exception("Could not find the bundle id")
	print(bundle_id)
	replace_bundle_id(app_path, bundle_id, new_group_id)
	appworkspace = findFileByType(appcontent, ".xcworkspace")
	app_proj = findFileByType(appcontent, ".xcodeproj")
	if appworkspace is not None:
		os.system("xcodebuild -workspace {} -scheme {}".format(app_proj, ""))
	elif app_proj is not None:
		os.system("xcodebuild -project {} CODE_SIGN_IDENTITY=\"{}\"".format(app_proj, signing_identity))
	else:
		print("Did not find project or workspace, cannot build")

#build("github.fullstackio.FlappySwift", "/Users/denislavrov/Library/Application Support/AppSource/build", "com.bahus")
#print(get_identities())

#print(deep_folder_find("/Users/denislavrov/Library/Application Support/AppSource/build/github.mukeshthawani.Calculator", ".xcodeproj"))