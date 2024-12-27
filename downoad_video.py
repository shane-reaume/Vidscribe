import yt_dlp
import argparse
import os
from PIL import Image
import requests
from io import BytesIO
import re
import sys

def parse_arguments():
    parser = argparse.ArgumentParser(description='Download YouTube videos and their thumbnails.')
    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument('name', help='Custom name for the video and thumbnail files')
    return parser.parse_args()

def ensure_directories():
    os.makedirs('public/videos', exist_ok=True)
    os.makedirs('public/img', exist_ok=True)

def validate_url(url):
    # Simple regex to validate YouTube URLs
    youtube_regex = re.compile(
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/)?([\w-]{11})'
    )
    return youtube_regex.match(url)

def sanitize_filename(name):
    # Remove invalid characters from filename
    return re.sub(r'[\\/*?:"<>|]', "", name)

def download_video(url, name):
    ydl_opts = {
        'outtmpl': f'public/videos/{name}.%(ext)s',  # Save video in public/videos with custom name
        'format': 'bestvideo+bestaudio/best',       # Download best quality
        'merge_output_format': 'mp4',               # Ensure output is mp4
        'writesubtitles': False,
        'writeautomaticsub': False,
        'quiet': False,
        'no_warnings': True,
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',  # Ensure mp4 format
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info_dict = ydl.extract_info(url, download=True)
            print("\nDownload Complete!")
            return info_dict
        except yt_dlp.utils.DownloadError as e:
            print(f"An error occurred while downloading the video: {e}")
            return None

def download_and_resize_thumbnail(thumbnail_url, name, width=810, height=449):
    try:
        response = requests.get(thumbnail_url, timeout=10)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        resized_img = img.resize((width, height), Image.ANTIALIAS)
        thumbnail_path = f'public/img/{name}.png'
        resized_img.save(thumbnail_path, format='PNG')
        print(f"Thumbnail saved to {thumbnail_path}")
    except requests.exceptions.RequestException as e:
        print(f"Network error while downloading the thumbnail: {e}")
    except IOError as e:
        print(f"Error processing the thumbnail image: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def main():
    args = parse_arguments()
    url = args.url
    name = sanitize_filename(args.name)

    if not validate_url(url):
        print("Invalid YouTube URL provided.")
        sys.exit(1)

    ensure_directories()

    info_dict = download_video(url, name)
    if not info_dict:
        return

    # Get thumbnail URL
    thumbnail_url = info_dict.get('thumbnail')
    if not thumbnail_url:
        print("No thumbnail found for this video.")
        return

    download_and_resize_thumbnail(thumbnail_url, name)

if __name__ == "__main__":
    main()
