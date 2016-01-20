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
REPO = "https://github.com/amitburst/HackerNews.git"
BUNDLEGROUP = "com.bahus"
XCODESCRIPT = """tell application "Xcode"
	activate
	open "/Users/denislavrov/Documents/AppSourcePath/HackerNews/HackerNews.xcworkspace"
	clean
	build
	launch
	tell application "System Events"
		perform (keystroke "r" using command down)
	end tell
end tell"""

git = subprocess.Popen(("git", "clone", REPO), cwd=BUILDPATH, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
gitout, giterr = git.stdout.read(), git.stderr.read()

gitapp = ""

if len(gitout) > 0:
	print("Downloading Finished")
	gitapp = re.search(b'\'.+\'', gitout).group(0).replace(b"'", b"").decode("UTF-8")
elif len(gitout) == 0 and b'already exists' in giterr:
	print("Already Downloaded")
	gitapp = re.search(b'\'.+\'', giterr).group(0).replace(b"'", b"").decode("UTF-8")
else:
	exit(1)

appcontent = os.listdir(BUILDPATH + "/" + gitapp)

if 'Podfile' in appcontent:
	print("You app uses CocoaPods, installing the required pods now")
	os.chdir(BUILDPATH + "/" + gitapp)
	#os.system("pod install")
	appworkspace = findFileByType(appcontent, ".xcworkspace")
	replaceBundleID(BUILDPATH + "/" + gitapp)
	#useful command to get schemes in workspaces
	#os.system("xcodebuild -list -workspace " + apptarget)
	print(BUILDPATH + "/" + gitapp + "/" + appworkspace)
	os.system("osascript -e '" + XCODESCRIPT + "'")
elif 'Cartfile' in appcontent:
	print("Carthage not supported yet, sorry I will add support soon :)") # TODO
else:
	print("No dependency manager detected") # TODO build from .project

