import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import urllib.request
from PIL import Image
import os

WIKI_URL = "https://en.wikipedia.org"


def create_img_folder(sport, league):
    path = os.path.join(sport, league, "img")
    if not os.path.exists(path):
        os.makedirs(path)


def create_team_folder(sport, league, team):
    team_name = team.replace(" ", "_")
    path = os.path.join(sport, league, "img", team_name)
    if not os.path.exists(path):
        os.makedirs(path)


def write_from_url_to_file(url, sport, league, team, small_size=100):
    format_ = url.split(".")[-1]
    team_name = team.replace(" ", "_")
    filename_original = f'{sport}/{league}/img/{team_name}/{team_name}_original.{format_}'
    filename_small = f'{sport}/{league}/img/{team_name}/{team_name}_small.{format_}'

    full_url = f"https:{url}"
    urllib.request.urlretrieve(full_url, filename_original)

    image = Image.open(filename_original)
    width, height = image.size
    new_width, new_height = 0, 0
    if width >= height:
        ratio = width / height
        new_height = small_size
        new_width = int(ratio * small_size)
    elif height > width:
        ratio = height / width
        new_width = small_size
        new_height = int(ratio * small_size)

    img_resized = image.resize((new_width, new_height))
    img_resized.save(filename_small)

    return full_url


def exceptions(sport, league, team):
    json_path = os.path.join(sport, league, f"{league}_exceptions.json")
    if not os.path.exists(json_path):
        return None

    exceptions_file = open(json_path)
    exceptions_dict = json.load(exceptions_file)
    key = next((key for key in exceptions_dict.keys() if key in team), None)
    if key is not None:
        write_from_url_to_file(exceptions_dict[key], sport, league, team)
        return exceptions_dict[key]
    else:
        return None


def download_image(sport, league, team):
    create_team_folder(sport, league, team)
    exception_source = exceptions(sport, league, team)
    if exception_source is None:
        team_search = f'{team.replace(" ", "+")}+{sport}'
        team_search_link = f"{WIKI_URL}/w/index.php?go=Go&search={team_search}&title=Special:Search&ns0=1"
        res = requests.get(team_search_link)
        bs_res = BeautifulSoup(res.text, "html.parser")
        if bs_res.find("div", {"class": "mw-search-result-heading"}):
            href_article = bs_res.find("div", {"class": "mw-search-result-heading"}).find("a").get("href")
            article = requests.get(f"{WIKI_URL}{href_article}")
            bs_article = BeautifulSoup(article.text, "html.parser")
        else:
            bs_article = bs_res

        if bs_article.find("td", {"class": "infobox-image"}):
            href_img = bs_article.find("td", {"class": "infobox-image"}).find("a").find("img").get("src")
            source = write_from_url_to_file(href_img, sport, league, team)
            return source
        else:
            print("--------Cant download---------")
            return None
    else:
        return exception_source


def download_images():
    sources = {}
    sport = input("Sport: ")
    league = input("League: ")
    create_img_folder(sport, league)
    teams_file = open(f'{sport}/{league}/{league}_teams.txt', 'r')
    teams = teams_file.read().splitlines()

    print(f"Total {len(teams)} teams")
    for i, team in enumerate(teams):
        print(i, team)
        source = download_image(sport, league, team)
        sources[team] = source

    with open(os.path.join(sport, league, f"{league}_sources.json"), 'w') as f:
        json.dump(sources, f)


if __name__ == "__main__":
    download_images()
