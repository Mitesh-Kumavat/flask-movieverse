import os
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def get_movie_trailer(title):
    print("START FINDING TRAILER")
    search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={title} trailer&key={YOUTUBE_API_KEY}"
    response = requests.get(search_url)
    if response.status_code == 200:
        data = response.json()
        if 'items' in data and len(data['items']) > 0:
            video_id = data['items'][0]['id']['videoId']
            trailer_url = f"https://www.youtube.com/embed/{video_id}?&autoplay=1&mute=0&rel=0"
            return trailer_url
    return None

def calculate_similarity(search_query, movies_df):
    movies_df['combined_features'] = movies_df['original_title'] + ' ' + movies_df['description'] + ' ' + movies_df['genre']
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(movies_df['combined_features'])
    query_vector = vectorizer.transform([search_query])
    cosine_sim = cosine_similarity(query_vector, tfidf_matrix).flatten()
    top_indices = cosine_sim.argsort()[-16:][::-1]
    top_movies = movies_df.iloc[top_indices][['imdb_title_id', 'original_title', 'img', 'year', 'avg_vote', 'description', 'genre']].to_dict(orient='records')

    return top_movies
