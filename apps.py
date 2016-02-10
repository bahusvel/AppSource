import click
import os
import gitcontroller as gc
from fscontroller import read_appfile
import extracting
import installer

APPSOURCE_INDEX = "https://github.com/bahusvel/AppSource-Index.git"
APPSOURCE_REPO = "https://github.com/bahusvel/AppSource.git"

APPSTORAGE = click.get_app_dir("AppSource")
STORAGEINDEX = APPSTORAGE+"/index"
STORAGEIOS = STORAGEINDEX+"/ios"
STORAGEMACOSX = STORAGEINDEX+"/macosx"
STORAGE_LOCAL_INDEX = APPSTORAGE+"/localindex"
STORAGECLI = APPSTORAGE+"/cli"
STORAGEBUILD = APPSTORAGE+"/build"
NEW_BUNDLE_ID = "com.bahus"


class TYPE:
	IOS = "IOS"
	MACOSX = "MACOSX"

@click.group()
def apps():
	click.echo("Welcome to AppSource")


@click.command()
@click.option("--url")
@click.argument("name")
def install(url, name):
	if name is None and url is None:
		name = click.prompt("Enter the module name")
	if name is not None and url is None:
		file = "{}/{}.json".format(STORAGEIOS, name)
		if os.path.exists(file):
			appdict = read_appfile(file)
			url = appdict["repo"]
		else:
			click.secho("The module you requested is not in the index", err=True)
			url = click.prompt("Please enter the url for the module")
	if url is not None:
		check_create(STORAGEBUILD)
		os.chdir(STORAGEBUILD)
		github_id = extracting.extract_github_id(url)
		appid = "github.{}.{}".format(github_id[0], github_id[1])
		gc.gitclone(url, aspath=appid)
		#installer.build_install(appid, STORAGEBUILD, NEW_BUNDLE_ID)


@click.command()
@click.option("--searchmethod", type=click.Choice(["QUICK", "FULL"]))
@click.argument("search_term")
def search(search_term, searchmethod):
	if searchmethod is None:
		searchmethod = "QUICK"
	apps = search_backend(search_term, entity_type=TYPE.IOS, searchtype=searchmethod)
	for app in apps:
		appdict = read_appfile(STORAGEIOS + "/" + app)
		click.secho("{} ({}) @ {}".format(appdict["name"], app[:-5], appdict["repo"]))


def search_backend(term, searchtype="QUICK", entity_type=TYPE.IOS):
	if searchtype == "QUICK":
		items = list_type(entity_type)
		return list(filter(lambda x: term in x.lower(), items))
	elif searchtype == "FULL":
		pass
	else:
		raise Exception("Invalid search method " + searchtype)


def list_type(entity_type):
	if entity_type == TYPE.IOS:
		searchpath = STORAGEIOS
	elif entity_type == TYPE.MACOSX:
		searchpath = STORAGEMACOSX
	else:
		raise Exception(str(entity_type) + "is not supported")
	items = os.listdir(searchpath)
	return list(filter(lambda x: x.endswith(".json"), items))


@click.command()
def update():
	check_create(APPSTORAGE)
	if not os.path.exists(STORAGEINDEX):
		os.chdir(APPSTORAGE)
		gc.gitclone(APPSOURCE_INDEX, aspath="index")
	else:
		os.chdir(STORAGEINDEX)
		gc.gitpull()


@click.command()
@click.option("--local/--remote", default=False)
def upgrade(local):
	check_create(APPSTORAGE)
	if not local:
		if not os.path.exists(STORAGECLI):
			os.chdir(APPSTORAGE)
			gc.gitclone(APPSOURCE_REPO, aspath="cli")
			os.chdir(STORAGECLI)
		else:
			os.chdir(STORAGECLI)
			gc.gitpull()
	if not local:
		os.system("pip install --upgrade .")
	else:
		os.system("pip install --upgrade --editable .")


@click.command()
def publish():
	pass


def check_create(path):
	if not os.path.exists(path):
		os.mkdir(path)

# command layout
apps.add_command(install)
apps.add_command(search)
apps.add_command(update)
apps.add_command(upgrade)
apps.add_command(publish)

if __name__ == '__main__':
	apps()