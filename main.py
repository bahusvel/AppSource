import subprocess
import os
import re


def findFileByType(appcontent, extension):
	for file in appcontent:
		if file.endswith(extension):
			return file
	return None

BUILDPATH = "/Users/denislavrov/Documents/AppSourcePath"
REPO = "https://github.com/amitburst/HackerNews.git"
BUNDLEGROUP = "com.bahus"

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
	os.system("pod install")
	appworkspace = findFileByType(appcontent, ".xcworkspace")
	appproject = findFileByType(appcontent, ".xcodeproj")
	# Change bundle ID
	print(appproject)
	exit(0)
	#useful command to get schemes in workspaces
	#os.system("xcodebuild -list -workspace " + apptarget)
	os.system("xcodebuild -workspace " + appworkspace + " -scheme " + gitapp)
elif 'Cartfile' in appcontent:
	print("Carthage not supported yet, sorry I will add support soon :)") # TODO
else:
	print("No dependency manager detected") # TODO build from .project

