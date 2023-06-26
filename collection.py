import os
import time
import requests
from bs4 import BeautifulSoup

api_url = 'https://www.boardgamegeek.com/xmlapi2'
username = 'Hhoffman'
output_dir = 'collection'
html_dir = '.'
collection_file = f'{output_dir}/collection.xml'

download_files = False
download_collection_file = False

os.makedirs(output_dir, exist_ok=True)

# Get Collection XML
if not os.path.isfile(collection_file) or download_collection_file:
    print('Downloading collection...')
    while True:
        collection_response = requests.get(f'{api_url}/collection?username={username}&own=1')
        if collection_response.status_code == 202:
            time.sleep(10)
        elif collection_response.status_code == 200:
            break
        else:
            raise Exception(f"Error occurred: {collection_response.status_code}")
    with open(collection_file, 'wb') as file:
        file.write(collection_response.content)
        print(f'Collection file written to {collection_file}')

with open(collection_file, 'rb') as file:
    collection_soup = BeautifulSoup(file, 'xml')

# Extract item IDs
items = [item['objectid'] for item in collection_soup.find_all('item')]
print(f"Processing {len(items)} items...")
remaining_items = len(items)

# Lists to hold games for each player count
games = [[] for _ in range(10)]

# Get images and details for each item
for item_id in items:
    remaining_items -= 1
    print(f"Remaining items: {remaining_items}")
    thing_file = f'{output_dir}/thing_{item_id}.xml'
    if not os.path.isfile(thing_file) or download_files:
        print('Downloading thing details...')
        while True:
            thing_response = requests.get(f'{api_url}/thing?id={item_id}')
            if thing_response.status_code == 202:
                time.sleep(10)
            elif thing_response.status_code == 200:
                break
            else:
                raise Exception(f"Error occurred: {thing_response.status_code}")
        with open(thing_file, 'wb') as file:
            file.write(thing_response.content)
            print(f'Thing file written to {thing_file}')
    with open(thing_file, 'rb') as file:
        thing_soup = BeautifulSoup(file, 'xml')
    image_url = thing_soup.find('image').text
    thumbnail_url = thing_soup.find('thumbnail').text
    title = thing_soup.find('name', {'type': 'primary'})['value']
    minplayers = int(thing_soup.find('minplayers')['value'])
    maxplayers = int(thing_soup.find('maxplayers')['value'])

    # Make sure the player counts are in the expected range
    minplayers = max(minplayers, 1)
    maxplayers = min(maxplayers, 10)

    yearpublished = thing_soup.find('yearpublished')['value']
    description = thing_soup.find('description').text
    image_file = f'{output_dir}/{title}_image.jpg'
    thumbnail_file = f'{output_dir}/{title}_thumbnail.jpg'
    if not os.path.isfile(image_file) or download_files:
        print(f"Downloading image for {title}...")
        time.sleep(10)
        image_response = requests.get(image_url)
        with open(image_file, 'wb') as file:
            file.write(image_response.content)
            print(f'Image file written to {image_file}')
    if not os.path.isfile(thumbnail_file) or download_files:
        print(f"Downloading thumbnail for {title}...")
        time.sleep(10)
        thumbnail_response = requests.get(thumbnail_url)
        with open(thumbnail_file, 'wb') as file:
            file.write(thumbnail_response.content)
            print(f'Thumbnail file written to {thumbnail_file}')
    for i in range(int(minplayers), int(maxplayers) + 1):
        games[i - 1].append((title, thumbnail_file, image_file))
    with open(f'{html_dir}/{title}_details.html', 'w', encoding='utf-8') as details_file:
        details_file.write(f'<html><head><title>{title}</title></head><body>')
        details_file.write(f'<h1 style="text-align:center;">{title}</h1>')
        details_file.write(f'<img src="{image_file}" style="display:block;margin-left:auto;margin-right:auto;width:50%;">')
        details_file.write(f'<table><tr><td>Min Players</td><td>{minplayers}</td></tr>')
        details_file.write(f'<tr><td>Max Players</td><td>{maxplayers}</td></tr>')
        details_file.write(f'<tr><td>Year Published</td><td>{yearpublished}</td></tr>')
        details_file.write(f'<tr><td>Description</td><td>{description}</td></tr></table>')
        details_file.write('</body></html>')
        print(f'Details file written to {title}_details.html')

print('All files have been downloaded. The collection is complete.')

# Create HTML files for player counts
for i, game_list in enumerate(games, start=1):
    with open(f'{html_dir}/{i}.html', 'w', encoding='utf-8') as html_file:
        html_file.write('<html><head><title>Games for ' + str(i) + ' players</title></head><body>')
        html_file.write('<div style="display:flex;flex-wrap:wrap;">')
        for title, thumbnail_file, image_file in sorted(game_list, key=lambda x: x[0]):
            html_file.write(f'<div style="width:200px;"><a href="{image_file}"><img src="{thumbnail_file}" alt="{title}"></a><p>{title}</p></div>')
        html_file.write('</div></body></html>')
        print(f'HTML file written for {i} players')

# Create menu HTML
with open(f'{html_dir}/menu.html', 'w', encoding='utf-8') as menu_file:
    menu_file.write('<html><head><title>Menu</title></head><body>')
    for i in range(1, 11):
        menu_file.write(f'<a href="{i}.html"><button style="width:100px;height:100px;">{i}</button></a>')
    menu_file.write('</body></html>')
    print('Menu HTML file written.')
