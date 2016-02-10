import json
import os


def read_appfile(path_to_corfile):
	with open(path_to_corfile, 'r') as local_corfile:
			local_cordict = json.loads(local_corfile.read())
	return local_cordict


def write_appfile(cordict, path_to_corfile):
	with open(path_to_corfile, 'w') as corfile:
			json.dump(cordict, corfile)


def git_exists():
	return os.path.exists(".git")
