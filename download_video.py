import argparse
import json
import os
import sys
import tempfile
import subprocess

import yt_dlp
from PIL import Image

CONFIG_FILE = 'videoConfig.json'
JS_CONFIG_FILE = 'public/js/videoConfig.js'


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    else:
        # Create default config
        config = {
            "videos": [
                {"id": "VIDEO1", "name": "FullOfLies-Eminem", "duration": 0},
                {"id": "VIDEO2", "name": "Discovery", "duration": 0},
                {"id": "VIDEO3", "name": "The_Carbon_Connection", "duration": 0}
            ]
        }
        save_config(config)
    return config


def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)


def add_video(config, name, duration=0):
    if len(config['videos']) >= 3:
        print("Configuration is full. Please specify a video slot to replace.")
        return config
    new_id = f"VIDEO{len(config['videos']) + 1}"
    config['videos'].append({"id": new_id, "name": name, "duration": duration})
    print(f"Added {new_id}: {name} (duration: {duration}s)")
    save_config(config)
    generate_js_config(config)  # Automatically generate JS config
    return config


def replace_video(config, replace_id, new_name, duration=0):
    for video in config['videos']:
        if video['id'] == replace_id:
            old_name = video['name']
            video['name'] = new_name
            video['duration'] = duration
            print(f"Replaced {replace_id}: {old_name} with {new_name} (duration: {duration}s)")
            save_config(config)
            generate_js_config(config)  # Automatically generate JS config
            return video['id'], old_name, new_name
    print(f"No video found with ID {replace_id}")
    return None, None, None


def view_videos(config):
    print("Current video entries:")
    for video in config['videos']:
        print(f"{video['id']}: {video['name']}")


def generate_js_config(config):
    # Start with an empty string
    js_content = ""

    # Iterate over the videos and define global variables
    for video in config['videos']:
        js_content += f'var {video["id"]} = "{video["name"]}";\n'

    # Write the content to videoConfig.js
    with open(JS_CONFIG_FILE, 'w') as f:
        f.write(js_content)
    print(f"Generated JavaScript configuration at '{JS_CONFIG_FILE}'")


def manage_videos(config):
    while True:
        print("\nVideo Management Menu:")
        print("1. Add a new video")
        print("2. Replace an existing video")
        print("3. View current videos")
        print("4. Generate JavaScript configuration")
        print("5. Exit")
        choice = input("Select an option (1-5): ").strip()

        if choice == '1':
            if len(config['videos']) >= 3:
                print("Configuration is full. Please replace an existing video instead.")
            else:
                new_name = input(f"Enter name for VIDEO{len(config['videos']) + 1}: ").strip()
                config = add_video(config, new_name)
        elif choice == '2':
            view_videos(config)
            replace_id = input("Enter the ID of the video to replace (e.g., VIDEO1): ").strip().upper()
            new_name = input(f"Enter new name for {replace_id}: ").strip()
            replaced_id, old_name, new_name = replace_video(config, replace_id, new_name)
            if replaced_id:
                # Clean up old video and thumbnail
                delete_video_files(replaced_id, old_name)
                # Download and possibly concatenate videos
                if len(urls) > 1:
                    info_dict = download_multiple_videos(urls, new_name, replaced_id, old_name)
                else:
                    info_dict = download_video(urls[0], new_name, replaced_id, old_name)
                if not info_dict:
                    sys.exit(1)
        elif choice == '3':
            view_videos(config)
        elif choice == '4':
            generate_js_config(config)
        elif choice == '5':
            break
        else:
            print("Invalid choice. Please select a valid option.")


def delete_video_files(video_id, video_name):
    # Define paths
    video_path_mp4 = f'public/videos/{video_name}.mp4'
    video_path_webm = f'public/videos/{video_name}.webm'
    thumbnail_path = f'public/img/{video_name}.png'

    # Delete video files
    for path in [video_path_mp4, video_path_webm]:
        if os.path.exists(path):
            os.remove(path)
            print(f"Deleted video file '{path}'")

    # Delete thumbnail file
    if os.path.exists(thumbnail_path):
        os.remove(thumbnail_path)
        print(f"Deleted thumbnail '{thumbnail_path}'")


def download_video(url, name, replace_id=None, old_name=None):
    ydl_opts = {
        'outtmpl': f'public/videos/{name}.%(ext)s',  # Save video in public/videos with custom name
        'format': 'bestvideo+bestaudio/best',  # Download best quality
        'merge_output_format': 'mp4',  # Ensure output is mp4
        'writethumbnail': True,  # Enable thumbnail download
        'thumbnailformat': 'webp',  # Download thumbnail in webp format
        'quiet': False,
        'no_warnings': True,
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',  # Ensure mp4 format
        }],
        'postprocessor_args': {
            'FFmpegVideoConvertor': ['-ac', '1']  # Convert audio to mono
        },
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            print(f"Starting video download: '{url}'")
            info_dict = ydl.extract_info(url, download=True)
            print("Video download complete.")
            
            # Get video duration
            duration = info_dict.get('duration', 0)
            print(f"Video duration: {duration}s")
            
            return {'filepath': f'public/videos/{name}.mp4', 'duration': duration}
        except yt_dlp.utils.DownloadError as e:
            print(f"An error occurred while downloading the video: {e}")
            return None


def convert_thumbnail(original_thumbnail_path, name, width=810, height=449):
    print(f"Attempting to convert and resize thumbnail from: {original_thumbnail_path}")
    try:
        with Image.open(original_thumbnail_path) as img:
            print(f"Original thumbnail size: {img.size} and format: {img.format}")

            # Determine the appropriate resampling filter
            try:
                resampling_filter = Image.Resampling.LANCZOS  # For Pillow >=10.0.0
            except AttributeError:
                resampling_filter = Image.LANCZOS  # For Pillow <10.0.0

            resized_img = img.resize((width, height), resampling_filter)
            print(f"Resized thumbnail to: {resized_img.size}")

            # Define the new path in 'public/img'
            thumbnail_png_path = f'public/img/{name}.png'
            resized_img.save(thumbnail_png_path, format='PNG')
            print(f"Thumbnail saved to '{thumbnail_png_path}'")

            # Optional: Delete the original thumbnail to save space
            os.remove(original_thumbnail_path)
            print(f"Deleted original thumbnail '{original_thumbnail_path}'")
    except IOError as e:
        print(f"Error processing the thumbnail image: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during thumbnail conversion: {e}")


def download_multiple_videos(urls, name, replace_id=None, old_name=None):
    # Create a temporary directory for intermediate files
    with tempfile.TemporaryDirectory() as temp_dir:
        video_files = []
        total_duration = 0
        individual_durations = []
        
        # Download each video separately
        for i, url in enumerate(urls):
            temp_name = f"{name}_part{i}"
            ydl_opts = {
                'outtmpl': os.path.join(temp_dir, f'{temp_name}.%(ext)s'),
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
                'writethumbnail': True if i == 0 else False,  # Only get thumbnail from first video
                'thumbnailformat': 'webp',
                'quiet': False,
                'no_warnings': True,
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    print(f"Starting download of part {i+1}: '{url}'")
                    info_dict = ydl.extract_info(url, download=True)
                    video_files.append(os.path.join(temp_dir, f'{temp_name}.mp4'))
                    # Add duration of each video
                    duration = info_dict.get('duration', 0)
                    individual_durations.append(duration)
                    total_duration += duration
                    print(f"Part {i+1} duration: {duration}s")
                except yt_dlp.utils.DownloadError as e:
                    print(f"Error downloading video part {i+1}: {e}")
                    return None

        if not video_files:
            return None

        print(f"Individual video durations: {individual_durations}")
        print(f"Total duration before concatenation: {total_duration}s")

        # Create file list for FFmpeg
        file_list_path = os.path.join(temp_dir, 'file_list.txt')
        with open(file_list_path, 'w') as f:
            for video_file in video_files:
                f.write(f"file '{video_file}'\n")

        # Verify the actual duration using ffprobe after concatenation
        output_path = f'public/videos/{name}.mp4'
        try:
            subprocess.run([
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', file_list_path, '-c', 'copy', output_path
            ], check=True, capture_output=True)
            
            # Verify final duration with ffprobe
            try:
                result = subprocess.run([
                    'ffprobe', '-v', 'quiet',
                    '-print_format', 'json',
                    '-show_format',
                    output_path
                ], capture_output=True, text=True, check=True)
                probe_data = json.loads(result.stdout)
                actual_duration = float(probe_data['format']['duration'])
                print(f"Actual concatenated video duration (ffprobe): {actual_duration}s")
                total_duration = actual_duration  # Use the actual duration instead
            except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not verify final duration: {e}")
            
            print(f"Successfully concatenated videos (final duration: {total_duration}s)")
            
            # Process thumbnail from the first video's thumbnail
            thumbnail_path = os.path.join(temp_dir, f'{name}_part0.webp')
            if os.path.exists(thumbnail_path):
                print(f"Thumbnail downloaded at '{thumbnail_path}'")
                convert_thumbnail(thumbnail_path, name, width=810, height=449)
            else:
                print("Thumbnail was not downloaded.")
            
            return {'filepath': output_path, 'duration': total_duration}
        except subprocess.CalledProcessError as e:
            print(f"Error concatenating videos: {e.stderr.decode()}")
            return None


def main():
    parser = argparse.ArgumentParser(description='Manage and download YouTube videos.')
    parser.add_argument('--manage', action='store_true', help='Manage video entries')
    parser.add_argument('--download', nargs='+', metavar='URL NAME [REPLACE_ID]',
                        help='Download video(s). For multiple videos, separate URLs with commas. They will be concatenated.')
    args = parser.parse_args()

    config = load_config()

    if args.manage:
        manage_videos(config)
    elif args.download:
        if len(args.download) < 2:
            print("Error: --download requires at least 2 arguments: URL and NAME.")
            sys.exit(1)
        
        # Split URLs if there are multiple
        urls = [url.strip() for url in args.download[0].split(',')]
        name = args.download[1]
        replace_id = args.download[2].upper() if len(args.download) >= 3 else None

        if replace_id:
            # Replace specified video slot
            if len(urls) > 1:
                info_dict = download_multiple_videos(urls, name, replace_id, None)
            else:
                info_dict = download_video(urls[0], name, replace_id, None)
                
            if info_dict:
                replaced_id, old_name, new_name = replace_video(config, replace_id, name, info_dict.get('duration', 0))
                if replaced_id:
                    # Clean up old video and thumbnail
                    delete_video_files(replaced_id, old_name)
            else:
                sys.exit(1)
        else:
            if len(config['videos']) >= 3:
                print("Configuration is full. Please specify a video slot to replace using the --download option.")
                print("Usage: --download URL NAME REPLACE_ID (e.g., --download 'url' 'name' 'VIDEO1')")
                sys.exit(1)
            else:
                if len(urls) > 1:
                    info_dict = download_multiple_videos(urls, name)
                else:
                    info_dict = download_video(urls[0], name)
                    
                if info_dict:
                    config = add_video(config, name, info_dict.get('duration', 0))
                else:
                    sys.exit(1)


if __name__ == "__main__":
    main()
