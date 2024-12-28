import argparse
import json
import os
import sys

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
                {"id": "VIDEO1", "name": "FullOfLies-Eminem"},
                {"id": "VIDEO2", "name": "Discovery"},
                {"id": "VIDEO3", "name": "The_Carbon_Connection"}
            ]
        }
        save_config(config)
    return config


def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)


def add_video(config, name):
    if len(config['videos']) >= 3:
        print("Configuration is full. Please specify a video slot to replace.")
        return config
    new_id = f"VIDEO{len(config['videos']) + 1}"
    config['videos'].append({"id": new_id, "name": name})
    print(f"Added {new_id}: {name}")
    save_config(config)
    generate_js_config(config)  # Automatically generate JS config
    return config


def replace_video(config, replace_id, new_name):
    for video in config['videos']:
        if video['id'] == replace_id:
            old_name = video['name']
            video['name'] = new_name
            print(f"Replaced {replace_id}: {old_name} with {new_name}")
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
            return info_dict
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


def main():
    parser = argparse.ArgumentParser(description='Manage and download YouTube videos.')
    parser.add_argument('--manage', action='store_true', help='Manage video entries')
    parser.add_argument('--download', nargs='+', metavar='URL NAME [REPLACE_ID]',
                        help='Download a specific video. Optionally specify REPLACE_ID to replace an existing video slot.')
    args = parser.parse_args()

    config = load_config()

    if args.manage:
        manage_videos(config)
    elif args.download:
        # Handle --download with variable arguments
        if len(args.download) < 2:
            print("Error: --download requires at least 2 arguments: URL and NAME.")
            sys.exit(1)
        url = args.download[0]
        name = args.download[1]
        replace_id = args.download[2].upper() if len(args.download) >= 3 else None

        if replace_id:
            # Replace specified video slot
            replaced_id, old_name, new_name = replace_video(config, replace_id, name)
            if replaced_id:
                # Clean up old video and thumbnail
                delete_video_files(replaced_id, old_name)
                # Proceed to download the new video
                info_dict = download_video(url, new_name, replaced_id, old_name)
                if not info_dict:
                    sys.exit(1)
                # Identify the downloaded thumbnail
                original_thumbnail_path = f'public/videos/{new_name}.webp'
                if os.path.exists(original_thumbnail_path):
                    print(f"Thumbnail downloaded at '{original_thumbnail_path}'")
                    convert_thumbnail(original_thumbnail_path, new_name, width=810, height=449)
                else:
                    print("Thumbnail was not downloaded.")
        else:
            # Attempt to add a new video
            if len(config['videos']) >= 3:
                print("Configuration is full. Please specify a video slot to replace using the --download option.")
                print("Usage: --download URL NAME REPLACE_ID (e.g., --download 'url' 'name' 'VIDEO1')")
                sys.exit(1)
            else:
                # Add the video
                config = add_video(config, name)
                # Proceed to download the new video
                info_dict = download_video(url, name)
                if not info_dict:
                    sys.exit(1)
                # Identify the downloaded thumbnail
                original_thumbnail_path = f'public/videos/{name}.webp'
                if os.path.exists(original_thumbnail_path):
                    print(f"Thumbnail downloaded at '{original_thumbnail_path}'")
                    convert_thumbnail(original_thumbnail_path, name, width=810, height=449)
                else:
                    print("Thumbnail was not downloaded.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
