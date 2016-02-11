import click
import os
import shutil
import as_gitcontroller as gc
from as_fscontroller import read_appfile
import extracting
import as_installer as installer

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
		app_path = STORAGEBUILD+"/"+appid
		if os.path.exists(app_path):
			shutil.rmtree(app_path)
		gc.gitclone(url, aspath=appid)
		identities = installer.get_identities()
		click.secho(
		"""The app you have chosen will need to be signed,
		in order to sign the app you need to have an active Apple Developer account,
		you are also requried to generate wildcard AppID and Mobile Provisioning Profile for that AppID"""
		)
		if len(identities) > 1:
			s_identity = click.prompt("Please choose the signing identity", type=click.Choice(identities))
		elif len(identities) == 1:
			s_identity = identities[0]
		else:
			click.secho("No developer identities were found on your machine!", err=True)
			exit(1)
		installer.build_prep(app_path, NEW_BUNDLE_ID)

		#compiling
		workspace = installer.get_workspace(app_path)
		project = installer.get_project(app_path)
		if workspace is not None:
			click.secho("The app your are building uses a workspace")
			scheme = click.prompt("Please enter the scheme name to build the app")
			installer.build_workspace(workspace, scheme, s_identity)
		elif project is not None:
			installer.build_project(project, s_identity)
		else:
			click.secho("Could not find project or workspace, cannot build the app", err=True)
			exit(1)

		# installing
		bundles = installer.deep_folder_find(app_path, ".app")
		if len(bundles) > 1:
			bundle = click.prompt("Please choose the correct bundle to deploy", type=click.Choice(bundles))
		elif len(bundles) == 1:
			bundle = bundles[0]
		else:
			click.secho("Could not find an App Bundle, maybe compiler failed?", err=True)
			exit(1)
		installer.install_to_device(bundle)


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
def clean():
	shutil.rmtree(STORAGEBUILD)
	os.mkdir(STORAGEBUILD)


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
apps.add_command(clean)

if __name__ == '__main__':
	apps()