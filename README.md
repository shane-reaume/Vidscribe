# videoAnalysisUI3

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.2-blue.svg)

## Table of Contents

- [Description](#description)
- [Features](#features)
- [Folder Structure](#folder-structure)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
- [Usage](#usage)
  - [Running the API](#running-the-api)
  - [Accessing the UI](#accessing-the-ui)
- [CLI Scripts](#cli-scripts)
  - [`--download`](#download)
  - [`--manage`](#manage)
- [API Endpoints](#api-endpoints)
- [Contributing](#contributing)
- [License](#license)

## Description

**videoAnalysisUI3** is a robust Flask-based application designed for video processing and analysis. It provides a user-friendly UI for managing videos, processing them into audio clips, transcribing speech, and searching through transcriptions. The API facilitates seamless integration and extensibility, allowing for the addition of new features and services.

## Features

- **Video Processing:** Automatically splits videos into audio clips of configurable duration.
- **Speech Recognition:** Transcribes audio clips using Google Speech Recognition.
- **Real-Time Updates:** Utilizes Server-Sent Events (SSE) to provide real-time transcription progress.
- **Search Functionality:** Allows searching through transcribed text to find specific keywords and their corresponding timestamps.
- **CLI Tools:** Offers command-line interfaces for downloading new videos and managing application features.
- **Extensible API:** Built on Flask and Flask-RESTful, making it easy to add or modify API endpoints.

## Folder Structure

videoAnalysisUI3/
├── asc/
│   └── <movie_name>/
│       ├── <movie_name>-000.wav
│       ├── <movie_name>-mini-000.wav
│       └── ...
│── crux_processor/
│       └── __init__.py
│       ├── video_per_second.py
│       └── ...
├── public/
│   ├── results-json/
│   │   └── <movie_name>-dialog.json
│   ├── videos/
│   │   └── <movie_name>.mp4
│   └── js/
│       ├── tg.js
│       └── videoConfig.js
│       ├── ...
├── api.py
├── videoConfig.json
├── requirements.txt
├── README.md
└── ...


- **`asc/`**: Contains audio clips extracted from videos.
- **`public/`**: Hosts static UI files and results in JSON format.
- **`video_api/`**: Contains Flask RESTful API services.
- **`video_per_second.py`**: Handles video processing and transcription.
- **`videoConfig.js` & `tg.js`**: Frontend configuration and JavaScript functionalities.
- **`requirements.txt`**: Lists all Python dependencies.

## Installation

### Prerequisites

- **Miniconda3** (Recommended for managing Python environments)
- **Python 3.11**

### Setup

1. **Clone the Repository**

   ```bash
   git clone https://github.com/shane-reaume/videoAnalysisUI3.git
   cd videoAnalysisUI3
   ```
2. Install Miniconda3

    Download and install Miniconda3 from here.

3. Create a New Conda Environment
  
    ```bash
    Copy code
    conda create -n video_api_env python=3.11
    conda activate video_api_env
    ```

4. Install Dependencies

   - Make sure pip is up-to-date and setuptools are the latest

     ```bash
     python -m pip install --upgrade pip
     pip install --upgrade setuptools
     ```
   - Generate requirements.txt

     ```bash
     pip install pipreqs
     pipreqs /path/to/videoAnalysisUI3 --force
     ```
   - Install Required Libraries

     ```bash
     pip install -r requirements.txt
     ```

## Usage

### Running the API
Start the Flask API by executing:

  ```bash
      python api.py
  ```

Upon running, the UI will automatically open in your default browser.

### Accessing the UI

- Navigate to http://localhost:4000/public/ in your web browser to access the user interface.
- The UI allows you to:
  - Upload and manage videos.
  - Process videos into audio clips.
  - View real-time transcription progress.
  - Search through transcriptions.

## CLI Scripts
The application includes command-line interface (CLI) scripts to enhance functionality and ease of use.

`--download`
Facilitates downloading new videos into the application.

Usage:

```bash
  python video_per_second.py --download <video_url_or_identifier>
```

Example:

```bash
  python video_per_second.py --download https://example.com/video.mp4
```

Description:

- Downloads the specified video and saves it to the public/videos/ directory.
- Automatically processes the downloaded video for transcription.

`--manage`
Provides management features for the application, such as listing processed videos, deleting videos, or updating configurations.

Usage:

```bash
  python video_per_second.py --manage <action> [options]
```

Examples:

- List All Processed Videos

```bash
  python video_per_second.py --manage list_videos
```

- Delete a Specific Video

```bash
  python video_per_second.py --manage delete_video <movie_name>
```

- Update Configuration Settings

```bash
  python video_per_second.py --manage update_config --clip_duration 15
```

Description:

- list_videos: Displays a list of all videos currently processed and available in the system.
- delete_video: Removes a specified video and its associated data from the system.
- update_config: Allows updating configuration settings like clip_duration.

Note: Ensure you provide the necessary arguments based on the action you intend to perform.

## API Endpoints
_To be updated once all endpoints are finalized. For now, refer to the api.py file for available endpoints._

### Example Endpoints

- Process Video

```http
POST /api/process
```

Description: Processes a specified video for transcription.

- Search Transcriptions

```http
POST /api/search
```

Description: Searches through transcribed text for specified keywords.

_Please update this section with detailed information about each API endpoint, including request and response formats, parameters, and examples._

## Contributing
Contributions are welcome! Please follow these steps:

1. Fork the Repository
2. Create a New Branch

    ```bash
    git checkout -b feature/YourFeatureName
    ```

3. Commit Your Changes

    ```bash
    git commit -m "Add some feature"
    ```

4. Push to the Branch

    ```bash
    git push origin feature/YourFeatureName
    ```

5. Open a Pull Request

License
This project is licensed under the MIT License. See the LICENSE file for details.
