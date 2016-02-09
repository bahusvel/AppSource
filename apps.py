import click
import os
import gitcontroller as gc

APPSOURCE_INDEX = "https://github.com/bahusvel/AppSource-Index.git"
APPSOURCE_REPO = "https://github.com/bahusvel/AppSource.git"

APPSTORAGE = click.get_app_dir("AppSource")
STORAGEINDEX = APPSTORAGE+"/index"
STORAGE_LOCAL_INDEX = APPSTORAGE+"/localindex"
STORAGECLI = APPSTORAGE+"/cli"
STORAGEBUILD = APPSTORAGE+"/build"


@click.group()
def apps():
	click.echo("Welcome to AppSource")


@click.command()
def install():
	pass


@click.command()
def search():
	pass


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


def check_create(path):
	if not os.path.exists(path):
		os.mkdir(path)

# command layout
apps.add_command(install)
apps.add_command(search)
apps.add_command(update)
apps.add_command(upgrade)

if __name__ == '__main__':
	apps()