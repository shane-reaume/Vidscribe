# Vidscribe

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.2-blue.svg)

A Flask-based application for video processing, speech-to-text transcription, and content search. Upload videos, process them into searchable transcripts, and easily find specific content within your video collection.

## Demo

Watch the application in action:

[![Vidscribe UI Demo](https://img.youtube.com/vi/Aupg10YgHL8/0.jpg)](https://www.youtube.com/watch?v=Aupg10YgHL8)

*Click the image above to watch the demo on YouTube*

## Features

- **Video Management:** Download and manage up to 3 videos in your workspace
- **Speech Recognition:** Automatically transcribes speech using Google Speech Recognition
- **Real-Time Updates:** Watch transcription progress in real-time
- **Content Search:** Search through transcriptions to find specific moments in videos
- **Background Noise Reduction:** Enhanced audio processing for better voice clarity
- **CLI Tools:** Convenient command-line tools for video management

## Installation

### Prerequisites

- Python 3.11^
- FFmpeg (for video processing)
- Git

### Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/shane-reaume/Vidscribe.git
   cd Vidscribe
   ```

2. **Create and Activate Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Starting the Application

1. **Start the Server**
   ```bash
   python api.py
   ```

2. **Access the UI**
   - Open http://localhost:4000/public/ in your web browser
   - You'll see three video slots: VIDEO1, VIDEO2, and VIDEO3

### Adding Videos

1. **Using the CLI**
   ```bash
   # Download a video into a specific slot
   python download_video.py --download 'VIDEO_URL' 'VIDEO_NAME' 'SLOT_ID'
   
   # Example:
   python download_video.py --download 'https://www.youtube.com/watch?v=example' 'my_video' 'VIDEO1'
   ```

2. **Multiple Videos at Once**
   ```bash
   # Concatenate multiple videos
   python download_video.py --download 'URL1,URL2' 'combined_video' 'VIDEO1'
   ```

### Processing Videos

1. In the web UI (http://localhost:4000/public/), locate your video slot
2. Click the "Process Video" button
3. Watch the real-time transcription progress
4. Once complete, the transcription will be saved as JSON

### Searching Content

1. Visit http://localhost:4000/public/search
2. Enter your search terms (comma-separated for multiple terms)
3. Results will show timestamps where the terms appear in your videos

### CLI Commands

```bash
# Download a video
python download_video.py --download 'VIDEO_URL' 'VIDEO_NAME' 'SLOT_ID'

# Clean workspace (removes all processed files)
python download_video.py --wipeData

# Manage videos interactively
python download_video.py --manage
```

## File Structure

```
Vidscribe/
├── asc/                      # Processed audio clips
├── public/
│   ├── videos/              # Downloaded videos
│   ├── img/                 # Video thumbnails
│   ├── results-json/        # Transcription results
│   └── js/                  # Frontend scripts
├── crux_processor/          # Core processing logic
├── api.py                   # Flask API server
├── download_video.py        # CLI tool
└── requirements.txt         # Python dependencies
```

## Troubleshooting

- **No Audio Detected**: Try adjusting the video's volume or using a video with clearer audio
- **Transcription Errors**: Ensure good internet connection for Google Speech API
- **Video Processing Failed**: Make sure FFmpeg is installed and accessible
- **UI Not Loading**: Verify the server is running on port 4000

## Data Management

- Use `python download_video.py --wipeData` to clean all processed files
- Each video slot (VIDEO1, VIDEO2, VIDEO3) can hold one video
- Replacing a video in a slot automatically cleans up old files

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Submit a Pull Request

## License

This project is licensed under the MIT License.
