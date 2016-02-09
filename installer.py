import subprocess
import os
import re
import mmap


def findFileByType(appcontent, extension):
	for file in appcontent:
		if file.endswith(extension):
			return file
	return None


def replaceBundleID(appath):
	for path, dirs, _ in os.walk(appath):
		for ddir in dirs:
			if ddir.endswith(".xcodeproj") and ddir != "Pods.xcodeproj":
				pbxpath = path + "/" + ddir + "/project.pbxproj"
				pbxfile = open(pbxpath)
				pbxmem = mmap.mmap(pbxfile.fileno(), 0, access=mmap.ACCESS_READ)
				bundle_start = pbxmem.find(b"PRODUCT_BUNDLE_IDENTIFIER = ")
				bundle_off = pbxmem[bundle_start:].find(b";")
				bundle_id = pbxmem[bundle_start + len(b"PRODUCT_BUNDLE_IDENTIFIER = "): bundle_start+bundle_off].decode("UTF-8")
				group_id = bundle_id[:bundle_id.rfind(".")]
				print("Replacing Group ID " + group_id)
				os.system("LC_ALL=C find . -type f -exec sed -i '' 's/"+group_id+"/"+BUNDLEGROUP+"/g' {} +")
				return

BUILDPATH = "/Users/denislavrov/Documents/AppSourcePath"
REPO = "https://github.com/fullstackio/FlappySwift.git"
BUNDLEGROUP = "com.bahus"
XCODESCRIPT = """tell application "Xcode"
	activate
	open "%s"
	clean
	build
	launch
	tell application "System Events"
		perform (keystroke "r" using command down)
	end tell
end tell"""

print("Downloading " + REPO)
git = subprocess.Popen(("git", "clone", REPO), cwd=BUILDPATH, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
gitout, giterr = git.stdout.read(), git.stderr.read()

gitapp = ""

if len(gitout) > 0:
	print("Downloading Finished")
	gitapp = re.search(b'\'.+\'', gitout).group(0).replace(b"'", b"").decode("UTF-8")
elif len(gitout) == 0 and len(giterr) > 0:
	print("Already Downloaded")
	gitapp = re.search(b'\'.+\'', giterr).group(0).replace(b"'", b"").decode("UTF-8")
else:
	print("Something failed, aborting")
	print(gitout)
	print(giterr)
	exit(1)

app_path = BUILDPATH + "/" + gitapp
os.chdir(app_path)
appcontent = os.listdir(app_path)

if 'Podfile' in appcontent:
	print("You app uses CocoaPods, installing the required pods now")
	os.system("pod install")
elif 'Cartfile' in appcontent:
	print("Carthage not supported yet, sorry I will add support soon :)") # TODO
else:
	print("No dependency manager detected, building normally") # TODO build from .project

replaceBundleID(BUILDPATH + "/" + gitapp)
appworkspace = findFileByType(appcontent, ".xcworkspace")
app_proj = findFileByType(appcontent, ".xcodeproj")
print(appworkspace)
if appworkspace is not None:
	os.system("osascript -e '" + XCODESCRIPT.format(app_path + "/" + appworkspace) + "'")
elif app_proj is not None:
	os.system("osascript -e '" + XCODESCRIPT.format(app_path + "/" + app_proj) + "'")
else:
	print("Did not find project or workspace, cannot build")
