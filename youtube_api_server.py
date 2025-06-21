from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os

YOUTUBE_API_KEY = os.getenv("AIzaSyAq--GwhFEwrU0Cgsl3FPqxcJy2cL5MLDE", "AIzaSyAq--GwhFEwrU0Cgsl3FPqxcJy2cL5MLDE")

def clean_search_query(query):
    return query.strip()

class YouTubeAPI:
    def __init__(self):
        self.service = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    
    def search_videos(self, query, max_results=3):
        try:
            query = clean_search_query(query)
            search_response = self.service.search().list(
                q=query,
                part='id,snippet',
                maxResults=max_results,
                order='viewCount',
                type='video',
                relevanceLanguage='tr',
                regionCode='TR'
            ).execute()
            
            video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
            if not video_ids:
                return []
            
            videos_response = self.service.videos().list(
                part='snippet,statistics',
                id=','.join(video_ids)
            ).execute()
            
            videos = []
            for item in videos_response.get('items', []):
                video_id = item['id']
                snippet = item['snippet']
                stats = item['statistics']
                videos.append({
                    'id': video_id,
                    'title': snippet['title'],
                    'channel': snippet['channelTitle'],
                    'url': f"https://www.youtube.com/watch?v={video_id}",
                    'views': int(stats.get('viewCount', 0)),
                    'likes': int(stats.get('likeCount', 0)),
                    'thumbnail': snippet['thumbnails']['medium']['url']
                })
            
            videos.sort(key=lambda x: x['likes'], reverse=True)
            return videos[:max_results]
        except HttpError as e:
            return {"error": f"YouTube API error: {e.resp.status} {e.content.decode()}"}
        except Exception as e:
            return {"error": str(e)}

app = Flask(__name__)
yt_api = YouTubeAPI()

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    max_results = request.args.get('max_results', default=3, type=int)
    if not query:
        return jsonify({"error": "Missing 'q' parameter"}), 400
    result = yt_api.search_videos(query, max_results=max_results)
    return jsonify(result)

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
