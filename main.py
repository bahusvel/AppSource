import subprocess
import os
import re

BUILDPATH = "/Users/denislavrov/Documents/AppSourcePath"
REPO = "https://github.com/amitburst/HackerNews.git"

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

