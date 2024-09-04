import requests
from bs4 import BeautifulSoup
import json
import urllib.parse
import yt_dlp
from moviepy.editor import VideoFileClip
import os
import whisper
import torch

# Load Whisper model and move to GPU if available
model = whisper.load_model("base")
if torch.cuda.is_available():
    model.to("cuda")
    print("cuda")

def fetch_links_and_titles(query, num_results=15):
    """Fetch search result links and titles from Google."""
    results = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    query = f"site:facebook.com {query}"
    query = urllib.parse.quote_plus(query)
    url = f"https://www.google.com/search?q={query}&num={num_results}&tbm=vid"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        search_results = soup.find_all('a', href=True)
        
        for result in search_results:
            href = result['href']
            if href.startswith('/url?q='):
                link = href.split('/url?q=')[1].split('&')[0]
                parent = result.find_parent('div')
                title_tag = parent.find('h3') if parent else None
                if not title_tag:
                    title_tag = soup.find('h3', text=True)
                title = title_tag.get_text() if title_tag else 'No title available'
                results.append({
                    'link': link,
                    'title': title
                })
                if len(results) >= num_results:
                    break
    except Exception as e:
        print(f"An error occurred: {e}")
    
    return results

def save_results_to_json(all_results, filename):
    """Save the dictionary of all results to a JSON file."""
    try:
        with open(filename, mode='w', encoding='utf-8') as file:
            json.dump(all_results, file, indent=4)
        print(f"Results saved to {filename}")
    except Exception as e:
        print(f"An error occurred while saving to JSON: {e}")

def load_queries_from_json(filename):
    """Load queries from a JSON file."""
    try:
        with open(filename, mode='r', encoding='utf-8') as file:
            data = json.load(file)
            return data.get('queries', [])
    except Exception as e:
        print(f"An error occurred while loading queries from JSON: {e}")
        return []

def download_video(url, output_path='video.mp4'):
    try:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': output_path,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return output_path
    except Exception as e:
        print(f"Error downloading video: {e}")
        return None

def extract_audio_from_video(video_path, audio_path='audio.wav'):
    try:
        video = VideoFileClip(video_path)
        audio = video.audio
        audio.write_audiofile(audio_path)
        audio.close()
        video.close()
        return audio_path
    except Exception as e:
        print(f"Error extracting audio: {e}")
        return None

def transcribe_audio(audio_path):
    result = model.transcribe(audio_path, word_timestamps=True)
    return result["text"]

def process_videos_and_transcribe(queries, output_json):
    all_results = {}
    final_results = []

    for query in queries:
        print(f"Processing query: {query}")
        results = fetch_links_and_titles(query)
        all_results[query] = results

        for video in results:
            title = video.get('title', 'No Title')
            link = video.get('link', '')

            video_path = download_video(link)
            if video_path is None:
                continue

            audio_path = extract_audio_from_video(video_path, f"{title[:50]}.wav")
            if audio_path is None:
                continue

            transcription = transcribe_audio(audio_path)

            final_results.append({
                'title': title,
                'url': link,
                'transcription': transcription
            })

            # Cleanup
            try:
                os.remove(video_path)
            except Exception as e:
                print(f"Error during cleanup of video file: {e}")

    with open(output_json, 'w') as f:
        json.dump(final_results, f, indent=4)

    print(f"Final results saved to {output_json}")

if __name__ == "__main__":
    input_json_filename = "queries.json"
    output_json_filename = "final_output.json"
    
    queries = load_queries_from_json(input_json_filename)
    process_videos_and_transcribe(queries, output_json_filename)
