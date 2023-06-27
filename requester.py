import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import numpy as np
import pandas as pd
from tabulate import tabulate
from transformers import pipeline
from bs4 import BeautifulSoup
import requests
from tqdm import tqdm
import re
from unidecode import unidecode
import os

client_id = "" ### Insert Spotify app id here
client_secret = "" ### Insert Spotify app secret here

#Authentication - without user
client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager = client_credentials_manager)

# add_lyrics = pass

# all = sp.recommendation_genre_seeds()['genres']

# print(all)
def main():
    combine = input("Combine Datasets? (Leave empty if no, else any value and press enter):")
    if combine:
        input_dir1 = "./" + input("Directory 1: ")
        input_dir2 = "./" + input("Directory 2: ")
        filename1 = input_dir1 + "/" + input_dir1 + "_cleaned.csv"
        filename2 = input_dir2 + "/" + input_dir2 + "_cleaned.csv"
        output_dir = "./" + "combined3"
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        output_fn = output_dir + "/" + output_dir + "_cleaned.csv"
        output_split = output_dir + "/" + output_dir 
        combineData(filename1, filename2, output_fn)
        prepData(output_fn, output_split)

    else:
        outdir = './' + input("enter name of directory to create: ")
        if not os.path.exists(outdir):
            os.mkdir(outdir)

        # fullname = os.path.join(outdir, outname)    
        initial_tracks = outdir.replace("./", "") + ".csv"
        add_lyrics = initial_tracks.split(".")[0] + '_lyrics' + ".csv"
        clean_lyrics = initial_tracks.split(".")[0] + '_cleaned' + ".csv"

        ##seed_genres to generate tracks from
        track_genres = [['hip-hop', 'chill'], ['hip-hop', 'party'], ['rock', 'country'], ['electronic', 'pop'], ['romance', 'chill'], ['indie', 'pop'], ['rock', 'indie']]
        ##model genres to classify the lyrics to
        genres = ['hip-hop', 'pop', 'country', 'rock', 'electronic', 'indie', 'chill', 'party', 'romance']
        full_initial = os.path.join(outdir, initial_tracks)
        full_add = os.path.join(outdir, add_lyrics)
        full_clean = os.path.join(outdir, clean_lyrics)
        full_split = outdir + '/' + initial_tracks.split(".")[0]

        print("Getting Initial Tracks...")
        getTracks(track_genres, full_initial)
        print("Adding Lyrics to Tracks...")
        addLyrics(full_initial, full_add)
        print("Cleaning Dataset...")
        cleanDataset(genres, full_add, full_clean)
        print("Prepping Dataset for model...")
        prepData(full_clean, full_split)
        print("DATA GENERATION COMPLETE!")



####################################################### GENERATE DATA ############################################################
def getTracks(genres, output_fn):
    data = {"Name": [], "Artist": [], "Genres": []}
    for genre in tqdm(genres, desc = "Loading genres ..."):
        print("genre: ", genre)
        for i in range(5):
            print("generating", i)
            recs = sp.recommendations(market = "US", seed_genres = genre, limit = 100)['tracks']
            count = 0
            for track in tqdm(recs, desc = "Loading tracks ..."):
                count += 1
                currTrack = sp.track(track['uri'])
                artist = sp.artist(currTrack["album"]["artists"][0]["uri"])
                genres = artist["genres"]
                artist_name = artist["name"]
                name = currTrack["name"]
                data["Name"].append(name)
                data["Artist"].append(artist_name)
                data["Genres"].append(genres)
    df = pd.DataFrame(data, columns = ["Name", "Artist", "Genres"])
    print(tabulate(df.head(20), headers='keys', tablefmt='psql'))
    df.to_csv(output_fn, index = False)


####################################################### ADD LYRICS ############################################################
def addLyrics(input_fn, output_fn):
    song_df = pd.read_csv(input_fn) ########### CHANGE BACK
    # song_df = pd.read_csv(output_fn)

    names = song_df['Name']
    artists = song_df['Artist']

    def scrape_lyrics(artistname, songname, count_missing):
        artistname2 = unidecode(str(artistname.replace(' ','-')) if ' ' in artistname else str(artistname)).replace("'", "").replace(".", "").replace("&", "and").replace('$', "-").replace("?", "").replace("!", "")

        songname_parenth = re.sub("[\(\[].*?[\)\]]", "", songname).strip()

        songname2 = unidecode(str(songname_parenth.replace(' ','-')) if ' ' in songname_parenth else str(songname_parenth)).replace("'", "").replace("&", "and").replace('$', "-").replace("?", "").replace("!", "")

        page = requests.get('https://genius.com/'+ artistname2 + '-' + songname2 + '-' + 'lyrics')
        html = BeautifulSoup(page.text, 'html.parser')
        lyrics1 = html.find_all("div", class_="lyrics")
        lyrics2 = html.find_all("div", class_="Lyrics__Container-sc-1ynbvzw-5 Dzxov")
        CLEANR = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6})')
        lyrics = None
        if lyrics1:
            lyrics = ''
            for i in lyrics1:
                lyrics += i.get_text()
            # lyrics = lyrics1.get_text()
        elif lyrics2:
            lyrics = ''
            for i in lyrics2:
                lyrics += str(i)
            # lyrics = lyrics2.get_text()
            clean_lyrics = re.sub(CLEANR, " ", lyrics)
            clean_lyrics = " ".join(clean_lyrics.split())

            lyrics = clean_lyrics
        elif lyrics1 == lyrics2 == None:
            lyrics = None

            count_missing += 1 
        if lyrics == None:
            count_missing += 1

        return lyrics, count_missing

    def lyrics_to_frame(df1):
        lyrics_missing = 0
        for i,x in tqdm(enumerate(df1["Name"]), desc="Loading..."):
            # if i <= 3000:
            #     ######## since it stopped at 3000, continue from here
            #     continue
            test, lyrics_missing = scrape_lyrics(df1["Artist"][i], x, lyrics_missing)
            df1.loc[i, 'lyrics'] = test
            if i % 500 == 0:
                df1.to_csv(output_fn)
                print("Total Lines:", i, "Total Missing:", lyrics_missing)
        return df1
    lyrics_to_frame(song_df)
    # print(tabulate(song_df.head(5), headers='keys', tablefmt='psql'))
    song_df.to_csv(output_fn)

########################################################## CONVERT RAW DATA TO CLEANED DATASET ############################################################

def cleanDataset(genres, input_fn, output_fn):
    read_df = pd.read_csv(input_fn)

    read_df.dropna(axis='index', how='any', inplace=True)
    read_df.reset_index(inplace=True)
    read_df.drop('Unnamed: 0', axis = 1, inplace=True)
    classifier = pipeline("zero-shot-classification", model="valhalla/distilbart-mnli-12-3")
    new_data = pd.DataFrame( columns = ["Name", 'lyrics'].extend(genres))
    df_genres = read_df["Genres"]
    df_names = read_df["Name"]
    df_lyrics = read_df['lyrics']

    for i in tqdm(range(len(df_genres))):

        attributes = classifier(df_genres[i], candidate_labels=genres)

        numIndex = len([x for x in attributes['scores'] if x > 0.2])
        new_genres = attributes['labels'][0:numIndex]

        new_row = {"Name": df_names[i], "lyrics": df_lyrics[i]}
        genre_map = {k: k in new_genres for k in genres}

        new_row.update(genre_map)


        new_data = pd.concat([new_data, pd.DataFrame([new_row])], ignore_index=True)

    print(tabulate(new_data.head(20), headers='keys', tablefmt='psql'))
    new_data.to_csv(output_fn)


######################################################## DROP COLUMNS AND SPLIT INTO TRAIN, VALIDATION, TEST ##################################################
def prepData(input_fn, output_fn):
    cleaned_df = pd.read_csv(input_fn, index_col = False)
    cleaned_df.drop_duplicates(subset="Name", inplace=True)
    shuffled = cleaned_df.sample(frac=1, random_state=77)
    if 'Unnamed: 0' in shuffled:
        shuffled.drop('Unnamed: 0', axis = 1, inplace=True)
    train, validate, test = np.split(shuffled, [int(0.8*len(shuffled)), int(0.9 * len(shuffled))])
    train.to_csv(output_fn + '_train.csv', index=False)
    validate.to_csv(output_fn + '_validate.csv', index=False)
    test.to_csv(output_fn + '_test.csv', index=False)

def combineData(input_fn1, input_fn2, output_fn):
    file1 = pd.read_csv(input_fn1, index_col = False)
    if "Unnamed: 0" in file1:
        file1.drop('Unnamed: 0', axis=1, inplace=True)
    file2 = pd.read_csv(input_fn2, index_col = False)
    if "Unnamed: 0" in file2:
        file2.drop('Unnamed: 0', axis=1, inplace=True)
    concatenated = pd.concat([file1, file2])
    concatenated.to_csv(output_fn, index = False)
    

main()
