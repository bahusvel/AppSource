import click
import os
import shutil
import json
import as_gitcontroller as gc
from as_fscontroller import read_appfile, write_appfile
import as_extracting
import as_installer as installer


def check_create(path):
	if not os.path.exists(path):
		os.mkdir(path)

APPSOURCE_INDEX = "https://github.com/bahusvel/AppSource-Index.git"
APPSOURCE_REPO = "https://github.com/bahusvel/AppSource.git"
APPSOURCE_REPO_ID = "bahusvel/AppSource"

APPSTORAGE = click.get_app_dir("AppSource")
check_create(APPSTORAGE)
STORAGEINDEX = APPSTORAGE+"/index"
STORAGEIOS = STORAGEINDEX+"/ios"
STORAGEMACOSX = STORAGEINDEX+"/macosx"
STORAGE_LOCAL_INDEX = APPSTORAGE+"/localindex"
STORAGECLI = APPSTORAGE+"/cli"
STORAGEBUILD = APPSTORAGE+"/build"
check_create(STORAGEBUILD)
STORAGESETTINGS = APPSTORAGE+"/settings.json"
settings_dict = {}


class TYPE:
	IOS = "IOS"
	MACOSX = "MACOSX"


@click.group()
def apps():
	global settings_dict
	click.echo("Welcome to AppSource")
	if not os.path.exists(STORAGESETTINGS):
		open(STORAGESETTINGS, "w").close()
	with open(STORAGESETTINGS, "r+") as settings_file:
		fcontents = settings_file.read()
		if fcontents is not "":
			settings_dict = json.loads(fcontents)
		else:
			settings_dict = {}
		if "group_id" not in settings_dict:
			click.secho("This software requires a new Group ID that will be used to sign the applications." + ""
			"This Group ID must match your wildcard App ID and provisioning profile, and it will be used for all of your apps")
			group_id = click.prompt("Please enter the Group ID in format [TLD].[GROUPNAME] e.g: com.bahus")
			settings_dict["group_id"] = group_id
		if "store_github_account" not in settings_dict:
			click.secho("AppSource uses and regularly interacts with GitHub, a lot of its functionality depends on this integration." + ""
			"Allow it to remember your github credentials so that you wont be nagged to enter them every time.")
			settings_dict["store_github_account"] = click.confirm("Would you like the system to remember your github credentials? ", default=True)
		if settings_dict["store_github_account"] and "github_username" not in settings_dict:
			settings_dict["github_username"] = click.prompt("Please enter your GitHub Username")
			settings_dict["github_password"] = click.prompt("Please enter your GitHub Password", hide_input=True)
		if settings_dict["store_github_account"] and "appsource_stared" not in settings_dict:
			try:
				gc.github_star(gc.github_get_repo_by_name(APPSOURCE_REPO_ID))
				settings_dict["appsource_stared"] = True
			except Exception:
				click.secho("Failed starring AppSource")
		#write the settings back
		settings_file.seek(0)
		json.dump(settings_dict, settings_file)


@click.command()
@click.option("--url")
@click.argument("name")
def get(url, name):
	get_backend(url, name, os.getcwd())


def get_backend(url, name, path):
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
		github_id = as_extracting.extract_github_id(url)
		if name is not None:
			appid = name
		else:
			appid = "github.{}.{}".format(github_id[0], github_id[1])
		app_path = path+"/"+appid
		if os.path.exists(app_path):
			shutil.rmtree(app_path)
		gc.gitclone(url, aspath=app_path)
	return appdict, app_path


def get_identity():
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
	return s_identity

@click.command()
@click.option("--url")
@click.argument("name")
def install(url, name):
		appdict, app_path = get_backend(url, name, STORAGEBUILD)
		s_identity = get_identity()
		installer.build_prep(app_path, settings_dict["group_id"])

		#compiling
		workspace = installer.get_workspace(app_path)
		project = installer.get_project(app_path)
		if workspace is not None:
			click.secho("The app your are building uses a workspace")
			installer.refresh_workspaces(project)
			schemes = installer.get_schemes(workspace)
			if appdict["name"] in schemes:
				scheme = appdict["name"]
			else:
				scheme = click.prompt("Please enter the scheme name to build the app", type=click.Choice(schemes))
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
			locate = click.confirm("Would you like to locate it manually?", default=False)
			if not locate:
				exit(1)
			bundle = click.prompt("Please enter the app bundle location")
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
	if len(apps) == 0:
		click.secho("Nothing found for \"{}\"".format(search_term))
		click.secho("Make sure to update your index using: \"apps update\"")


@click.command()
@click.argument("ipa_path")
@click.option("--profile_path")
def resign(ipa_path, profile_path):
	if not (ipa_path.endswith(".ipa") or ipa_path.endswith(".IPA")):
		click.secho("Non IPA File was supplied")
	ipa_resign_tool = STORAGECLI+"/ipa_sign.sh"
	s_identity = get_identity()
	if profile_path is None:
		profiles = installer.filtered_profiles(team=installer.team_id_from_identity(s_identity), app_id="*")
		profile = click.prompt("Please choose a profile to embed into IPA", type=click.Choice(list(profiles.keys())))
		profile_path = profiles[profile]
	os.chdir(os.path.dirname(ipa_path))
	os.system("bash \"{}\" {} {} \"{}\"".format(ipa_resign_tool, ipa_path, profile_path, s_identity))


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
	if not os.path.exists(STORAGEINDEX):
		os.chdir(APPSTORAGE)
		gc.gitclone(APPSOURCE_INDEX, aspath="index")
	else:
		os.chdir(STORAGEINDEX)
		gc.gitpull()


@click.command()
@click.option("--local/--remote", default=False)
def upgrade(local):
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
def sync():
	sync_backend()


def sync_backend():
	commited = False
	if not os.path.exists(".git"):
		if click.confirm("This is not a git repository, would you like to initialize it as git?", default=True):
			gc.gitinit()
		else:
			click.secho("Operation aborted", err=True)
			exit(1)
	if gc.getremote() != "":
		if gc.isdiff():
			if click.confirm("You have modified the app do you want to commit?"):
				msg = click.prompt("Please enter a commit message")
				gc.gitupsync(msg)
				commited = True
		gc.gitpull()
		if commited:
			gc.gitpush()
	else:
		click.secho("You do not have git remote setup", err=True)
		if click.confirm("Do you want one setup automatically?"):
			gc.github_login()
			name = click.prompt("Please enter the name for the repo")
			remote = gc.github_create_repo(name).clone_url
		else:
			click.secho("You will have to create a repository manually and provide the clone url")
			remote = click.prompt("Please enter the url")
		gc.addremote(remote)
		gc.gitadd(".")
		gc.gitcommit("Initializing repo")
		gc.gitpush(create_branch=True)


@click.command()
def publish():
	entitypath = os.getcwd()
	username = gc.github_login().get_user().login
	sync_backend()
	localindex = gc.get_appsource_index()
	if localindex is None:
		localindex = gc.fork_on_github("bahusvel/AppSource-Index")
	if not os.path.exists(STORAGE_LOCAL_INDEX):
		os.chdir(APPSTORAGE)
		gc.gitclone(localindex.clone_url, aspath="localindex")
	os.chdir(STORAGE_LOCAL_INDEX)
	gc.gitpull()
	# create corfile here
	app_dict = {}
	app_id = click.prompt("Please enter the App ID for your application")
	app_dict["name"] = app_id[app_id.rfind(".")+1:]
	app_dict["description"] = click.prompt("Please enter a short description for your app")
	os.chdir(entitypath)
	app_dict["repo"] = gc.getremote()
	public_appfile_path = STORAGE_LOCAL_INDEX+"/ios/" + app_id + ".json"
	write_appfile(app_dict, public_appfile_path)
	os.chdir(STORAGE_LOCAL_INDEX)
	gc.gitadd(public_appfile_path)
	gc.gitcommit("Added " + app_id)
	gc.gitpush()
	try:
		gc.github_pull_request(localindex.full_name, username, "AppSource-Index", "Add " + app_id)
	except Exception:
		click.secho("Pull request failed, please create one manualy", err=True)


# command layout
apps.add_command(install)
apps.add_command(search)
apps.add_command(update)
apps.add_command(upgrade)
apps.add_command(publish)
apps.add_command(sync)
apps.add_command(clean)
apps.add_command(get)
apps.add_command(resign)

if __name__ == '__main__':
	apps()