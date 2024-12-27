import yt_dlp

# Define download options
ydl_opts = {
    'outtmpl': '%(id)s.%(ext)s',  # Output filename format
    'quiet': False,                # Set to True to disable verbose output
    # Add more options as needed
}

# Create a YtDlp object with the specified options
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    # Extract information and download the video
    result = ydl.extract_info('https://www.youtube.com/watch?v=TnnV2_QTYl4', download=True)

    # Handle playlists or single videos
    if 'entries' in result:
        # It's a playlist or a list of videos
        video = result['entries'][0]  # Get the first video in the playlist
    else:
        # It's a single video
        video = result

    # Get the direct video URL (might require additional steps)
    # Note: 'url' may refer to the best available format's URL
    video_url = video.get('url', None)
    print(f"Direct video URL: {video_url}")
