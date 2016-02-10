import os
import subprocess
import github
import click

GITHUB = None


def gitclone(url, aspath=None):
	if aspath is None:
		os.system("git clone --recursive " + url)
	else:
		os.system("git clone --recursive " + url + " " + aspath)


def gitaddsubmodule(url, pathname=None):
	if pathname is not None:
		os.system("git submodule add " + url + " " + pathname)
	else:
		os.system("git submodule add " + url)
	cwd = os.getcwd()
	os.chdir(pathname)
	os.system("git submodule update --init --recursive")
	os.chdir(cwd)


def gitinit():
	os.system("git init")


def gitpull():
	os.system("git pull")


def gitadd(file):
	os.system("git add " + "\"" + file + "\"")


def gitcommit(message):
	os.system("git commit -a -m " + "\"" + message + "\"")


def isdiff():
	diff = subprocess.check_output(["git", "diff", "--shortstat"], universal_newlines=True)
	return diff != ""


def gitpush(create_branch=False):
	if create_branch:
		os.system("git push -u origin master")
	else:
		os.system("git push")


def getremote():
	out = subprocess.check_output(["git", "remote", "-v"], universal_newlines=True)
	if out == "":
		return out
	splits = out.split("\t")[1].split(" ")[0]
	return splits


def addremote(url):
	os.system("git remote add origin " + url)


def github_login():
	global GITHUB
	if GITHUB is None:
		username = click.prompt("Please enter your GitHub Username")
		password = click.prompt("Please enter your GitHub Password", hide_input=True)
		GITHUB = github.Github(username, password)
	return GITHUB


def github_create_repo(name):
	github_login().get_user().create_repo(name)


def get_cor_index():
	for repo in github_login().get_user().get_repos():
		if repo.name == "COR-Index":
			return repo
	return None


def fork_on_github(repo="bahusvel/COR-Index"):
	reporepr = github_login().get_repo(repo)
	return github_login().get_user().create_fork(reporepr)


def github_pull_request(to, username, repo, title):
	reporepr = github_login().get_repo(to)
	reporepr.create_pull(title, title, "master", username+":"+repo)


def gitupsync(message):
	os.system("git add .")
	os.system("git commit -a -m \"" + message + "\"")

