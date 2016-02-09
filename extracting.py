import csv, json


def extract_github_id(url):
    string = "github.com/"
    github = url.find(string)
    if github < 0:
        return None
    idpart = url[github + len(string):]
    parts = idpart.split("/")
    return (parts[0], parts[1])


with open('all_extracted.csv', 'r') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        appdict = {"name": row[0], "description": row[1], "repo":row[2]}
        github_id = extract_github_id(row[2])
        if github_id is not None:
            filename = "github.{}.{}.json".format(github_id[0], github_id[1])
            with open("appfiles/" + filename, 'w') as appfile:
                json.dump(appdict, appfile)