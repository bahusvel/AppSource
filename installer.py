import os
import mmap

CODE_SIGN_IDENTITY = ""
PROVISIONING_PROFILE = ""

def findFileByType(appcontent, extension):
	for file in appcontent:
		if file.endswith(extension):
			return file
	return None


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
					return group_id
				else:
					return None


def replace_bundle_id(appath, old_group_id, new_group_id):
	os.chdir(appath)
	os.system("LC_ALL=C find . -type f -exec sed -i '' 's/"+old_group_id+"/"+new_group_id+"/g' {} +")
	return True


def build_install(appid, buildpath, new_group_id):
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

	replace_bundle_id(app_path, "io.fullstack", new_group_id)
	appworkspace = findFileByType(appcontent, ".xcworkspace")
	app_proj = findFileByType(appcontent, ".xcodeproj")
	if appworkspace is not None:
		os.system("xcodebuild -workspace {} -scheme {}".format(app_proj, ""))
	elif app_proj is not None:
		os.system("xcodebuild -project {} CODE_SIGN_IDENTITY=\"{}\" PROVISIONING_PROFILE=\"{}\"".format(app_proj, CODE_SIGN_IDENTITY, PROVISIONING_PROFILE))
	else:
		print("Did not find project or workspace, cannot build")

#build_install("github.fullstackio.FlappySwift", "/Users/denislavrov/Library/Application Support/AppSource/build", "com.bahus")