import webbrowser
import spotipy
import pandas as pd
import numpy as np
import tkinter as tk
from spotipy.oauth2 import SpotifyClientCredentials
from collections import defaultdict
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import cdist
import tkinter.font as tkFont


class RecommendSong:
    @staticmethod
    def find_song(name, year):
        song_data = defaultdict()
        results = sp.search(q='track: {} year: {}'.format(name,year), limit=1)
        if not results['tracks']['items']:
            return None

        results = results['tracks']['items'][0]

        track_id = results['id']
        audio_features = sp.audio_features(track_id)[0]

        song_data['name'] = [results['name']]
        song_data['year'] = [year]
        song_data['explicit'] = [int(results['explicit'])]
        song_data['duration_ms'] = [results['duration_ms']]
        song_data['popularity'] = [results['popularity']]

        for key, value in audio_features.items():
            song_data[key] = value

        return pd.DataFrame(song_data)

    @staticmethod
    def flatten_dict_list(dict_list):
        flattened_dict = defaultdict()
        for key in dict_list[0].keys():
            flattened_dict[key] = []

        for dictionary in dict_list:
            for key, value in dictionary.items():
                flattened_dict[key].append(value)

        return flattened_dict

    def get_song_data(self, song, data):
        try:
            song_data = data[(data['name'] == song['name'])
                             & (data['year'] == song['year'])].iloc[0]
            return song_data

        except IndexError:
            return self.find_song(song['name'], song['year'])

    def get_mean_vector(self, song_list, data):
        song_vectors = []
        X = data.select_dtypes(np.number)
        number_cols = list(X.columns)

        for song in song_list:
            song_data = self.get_song_data(song, data)
            if song_data is None:
                print('Warning: {} does not exist in Spotify or in database'.format(song['name']))
                continue
            song_vector = song_data[number_cols].values
            song_vectors.append(song_vector)

        song_matrix = np.array(list(song_vectors))
        return np.mean(song_matrix, axis=0)

    def recommend_songs(self, song_list, data,  n_songs=10):
        X = data.select_dtypes(np.number)
        number_cols = list(X.columns)
        metadata_cols = ['name', 'year', 'artists', 'id']
        song_dict = self.flatten_dict_list(song_list)

        song_center = self.get_mean_vector(song_list, data)
        scaler = StandardScaler().fit(X)
        scaled_data = scaler.transform(data[number_cols])
        scaled_song_center = scaler.transform(song_center.reshape(1, -1))
        distances = cdist(scaled_song_center, scaled_data, 'cosine')

        index = list(np.argsort(distances)[:, :n_songs][0])

        rec_songs = data.iloc[index]
        rec_songs = rec_songs[~rec_songs['name'].isin(song_dict['name'])]
        return rec_songs[metadata_cols].to_dict(orient='records')


class Gui(tk.Frame):
    def __init__(self, master=None, data=None):
        super().__init__(master)
        self.master = master
        self.data = data
        self.widgets()

    def widgets(self):
        lab_font = tkFont.Font(size=20, weight="bold")
        title_font = tkFont.Font(size=15, weight="bold")
        self.master.geometry("900x700")
        name = tk.StringVar()
        year = tk.StringVar()
        self.master.title("Recommend me")
        frame1 = tk.Frame(self.master, width=700)
        frame1.pack()
        frame2 = tk.LabelFrame(self.master, pady=20,width=900)
        frame2.pack()
        label = tk.Label(frame1, text=' WELCOME ', font=lab_font, pady=30)
        label.grid(row=0, columnspan=2)
        label2 = tk.Label(frame1, text=' Enter Song Name:', padx=100)
        label3 = tk.Label(frame1, text=' Enter Year :', padx=100)
        label2.grid(row=1, column=0)
        label3.grid(row=2, column=0)
        en1 = tk.Entry(frame1, textvariable=name,width = 35)
        en2 = tk.Entry(frame1, textvariable=year,width = 35)
        en1.grid(row=1, column=1)
        en2.grid(row=2, column=1)
        sub = tk.Button(frame1, text='SUBMIT', command=lambda: self.action(name.get(), year.get(), frame2))
        sub.grid(row=3, columnspan=2)
        title1 = tk.Label(frame2, text='SongName', font=title_font, padx=50, pady=30)
        title2 = tk.Label(frame2, text='Artist', font=title_font, padx=50, pady=30)
        title3 = tk.Label(frame2, text='Play Now', font=title_font, padx=50, pady=30)
        title1.grid(row=0, column=0)
        title2.grid(row=0, column=1)
        title3.grid(row=0, column=2)

    def action(self, name, year, frame):
        res = RecommendSong()
        results = res.recommend_songs(self.list(name,year), self.data)
        dframe = pd.DataFrame.from_dict(results)
        print(dframe)

        self.display_df(dframe, frame)

    def display_df(self, df, frame):
        for index in df.index:
            col1 = tk.Label(frame, text=df['name'][index], pady=10)
            col2 = tk.Label(frame, text=df['artists'][index], pady=10)
            col3 = self.call_button(frame, df['id'][index])
            col1.grid(row=index + 1, column=0)
            col2.grid(row=index + 1, column=1)
            col3.grid(row=index + 1, column=2)

    def call_button(self, frame, id):
        return tk.Button(frame, text='Press here', command=lambda: self.webup(id), pady=10)

    def webup(self, id):
        webbrowser.open("http://open.spotify.com/track/" + id)
    def list(self,name,year):
        n=name.split(",")
        y=year.split(",")
        lis = list()
        for (a,b) in zip(n,y):
            dic = {'name':a,'year':int(b)}
            lis.append(dic)
        return lis

if __name__ == '__main__':
    cid = 'c96e11730a834654ac170873971a1ca4'
    secret = '5a32234f65df4e04afc9f13267d8a8bf'
    client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
    sp = spotipy.Spotify(client_credentials_manager =client_credentials_manager)
    # ------------------------------------------------------------------------------------------------
    spotify_data = pd.read_csv('./data.csv.zip')
    # ------------------------------------------------------------------------------------------------

    top = tk.Tk()
    app = Gui(top, spotify_data)
    top.mainloop()
