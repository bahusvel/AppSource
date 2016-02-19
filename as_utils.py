import os


def execute_in(path, function, create=False):
	cwd = os.getcwd()
	if not os.path.exists(path):
		os.mkdir(path)
	os.chdir(path)
	function()
	os.chdir(cwd)
