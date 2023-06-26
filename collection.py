import requests
from bs4 import BeautifulSoup
from pathlib import Path
import time
import os

def sanitize(filename: str) -> str:
    # Many characters are not allowed in Windows filenames
    for character in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
        filename = filename.replace(character, '')
    return filename

def download_file(url, path):
    if not os.path.exists(path):
        print(f'Downloading {url}...')
        response = requests.get(url, stream=True)
        with open(path, 'wb') as out_file:
            out_file.write(response.content)
        print(f'File written to {path}')
        time.sleep(10)

bgg_url = 'https://boardgamegeek.com/xmlapi2'
username = 'Hhoffman'
collection_file = 'collection.xml'
html_dir = '.'
output_dir = 'collection'
download_files = False

# Create directories if they don't exist
Path(html_dir).mkdir(parents=True, exist_ok=True)
Path(output_dir).mkdir(parents=True, exist_ok=True)

if download_files:
    collection_url = f'{bgg_url}/collection?username={username}&own=1'
    download_file(collection_url, collection_file)
    time.sleep(5)  # Delay to respect API guidelines

# Parse the collection XML
with open(collection_file, 'r', encoding='utf-8') as file:
    collection_content = file.read()
collection_soup = BeautifulSoup(collection_content, 'xml')
items = collection_soup.find_all('item')

# Prepare list to store games per player count
games = [[] for _ in range(10)]  # Games for 1 to 10 players

# Go through all items in the collection
total_items = len(items)
for i, item in enumerate(items, start=1):
    item_id = item['objectid']
    thing_file = f'{output_dir}/thing_{item_id}.xml'
    
    if download_files:
        # Get thing XML
        thing_url = f'{bgg_url}/thing?id={item_id}'
        download_file(thing_url, thing_file)
    
    # Parse thing XML
    with open(thing_file, 'r', encoding='utf-8') as file:
        thing_content = file.read()
    thing_soup = BeautifulSoup(thing_content, 'xml')
    thumbnail_url = thing_soup.find('thumbnail').text
    image_url = thing_soup.find('image').text
    title = sanitize(thing_soup.find('name')['value'])
    thumbnail_file = f'{output_dir}/{title}_thumbnail.jpg'
    image_file = f'{output_dir}/{title}_image.jpg'
    
    # Download image and thumbnail
    download_file(thumbnail_url, thumbnail_file)
    download_file(image_url, image_file)

    # Find and adjust player count
    minplayers = int(thing_soup.find('minplayers')['value'])
    maxplayers = int(thing_soup.find('maxplayers')['value'])
    minplayers = max(minplayers, 1)
    maxplayers = min(maxplayers, 10)

    # Store game info in relevant player count lists
    for i in range(minplayers, maxplayers + 1):
        games[i - 1].append((title, thumbnail_file, image_file))

    print(f'Processed {title}. Remaining items: {total_items - i}')
    
# Create index HTML
with open(f'{html_dir}/index.html', 'w', encoding='utf-8') as index_file:
    index_file.write('<html><head><title>Collection</title></head><body>\n')
    index_file.write('<div style="display: flex; flex-wrap: wrap; justify-content: space-around;">\n')
    for game in sorted(games[0], key=lambda x: x[0]):  # Sorting games by title
        title, thumbnail_file, image_file = game
        index_file.write(f'<div><a href="{image_file}"><img src="{thumbnail_file}" alt="{title}" width="200"></a><p>{title}</p></div>\n')
    index_file.write('</div></body></html>\n')
    print(f'Index file written to index.html')

# Create player count HTMLs
for i, game_list in enumerate(games, start=1):
    with open(f'{html_dir}/{i}.html', 'w', encoding='utf-8') as player_file:
        player_file.write('<html><head><title>Collection for ' + str(i) + ' players</title></head><body>\n')
        player_file.write('<div style="display: flex; flex-wrap: wrap; justify-content: space-around;">\n')
        for game in sorted(game_list, key=lambda x: x[0]):  # Sorting games by title
            title, thumbnail_file, image_file = game
            player_file.write(f'<div><a href="{image_file}"><img src="{thumbnail_file}" alt="{title}" width="200"></a><p>{title}</p></div>\n')
        player_file.write('</div></body></html>\n')
        print(f'Player count file written to {i}.html')

# Create menu HTML
with open(f'{html_dir}/menu.html', 'w', encoding='utf-8') as menu_file:
    menu_file.write('<html><head><title>Menu</title></head><body>\n')
    for i in range(1, 11):
        menu_file.write(f'<a href="{i}.html"><button>{i}</button></a>\n')
    menu_file.write('</body></html>\n')
    print(f'Menu file written to menu.html')
