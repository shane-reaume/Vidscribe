import moviepy.editor as mp
import json
import os
from pydub import AudioSegment
from pydub.effects import normalize
import speech_recognition as sr
import io
import queue
import threading
import logging
import numpy as np
from scipy.signal import butter, filtfilt
import subprocess

# Configure logging for better debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

recognizer = sr.Recognizer()

# Configure audio preprocessing parameters
SAMPLE_RATE = 16000  # Hz
LOW_CUTOFF = 50  # Hz (lowered from 80 to catch more voice content)
HIGH_CUTOFF = 4000  # Hz (increased from 3300 to preserve more voice harmonics)
NOISE_REDUCE_TIME = 0.25  # seconds (reduced from 0.5 to be less aggressive)
ENERGY_THRESHOLD = 150  # lowered from 300 to detect softer speech

def butter_bandpass(lowcut, highcut, fs, order=5):
    nyquist = 0.5 * fs
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = butter(order, [low, high], btype='band')
    return b, a

def apply_bandpass_filter(data, fs, lowcut, highcut, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = filtfilt(b, a, data)
    return y

class Stream(object):
    def __init__(self):
        self.q = queue.Queue()

    def send_message(self, message):
        """Send a message to the queue."""
        self.q.put(message)

    def event_stream(self):
        """Generator that yields messages from the queue as Server-Sent Events."""
        while True:
            message = self.q.get()
            yield f'data: {message}\n\n'

class RequestSpeech(object):
    clip_duration = 10  # Duration in seconds for each clip

    def repair_mp4(self, video_path):
        """
        Attempts to repair a corrupted MP4 file by re-encoding it.
        Returns the path to the repaired file.
        """
        try:
            repaired_path = video_path.replace('.mp4', '_repaired.mp4')
            logging.info(f"Attempting to repair video file: {video_path}")
            
            # Use ffmpeg to re-encode the video
            subprocess.run([
                'ffmpeg', '-i', video_path,
                '-c:v', 'copy', '-c:a', 'copy',
                '-movflags', '+faststart',
                repaired_path
            ], check=True, capture_output=True)
            
            # If successful, replace the original file
            os.replace(repaired_path, video_path)
            logging.info(f"Successfully repaired video file: {video_path}")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to repair video file: {e.stderr.decode()}")
            return False

    def processSpeech(self, movie_name, stream_instance=None):
        if not movie_name:
            logging.error("No Movie name provided, exiting.")
            if stream_instance:
                message = {
                    "type": "error",
                    "text": "Error: No Movie name provided."
                }
                stream_instance.send_message(json.dumps(message))
            return

        clip_duration = self.clip_duration
        movie_path = os.path.join("public", "videos", f"{movie_name}.mp4")
        asc_dir = os.path.join("asc", movie_name)
        dialog_json = os.path.join("public", "results-json", f"{movie_name}-dialog.json")
        
        # Create necessary directories
        os.makedirs(asc_dir, exist_ok=True)
        os.makedirs(os.path.dirname(dialog_json), exist_ok=True)
        
        # Try to load the video, repair if needed
        try:
            full_movie = mp.VideoFileClip(movie_path)
        except Exception as e:
            logging.error(f"Error loading video '{movie_name}.mp4': {e}")
            # Attempt to repair the video
            if self.repair_mp4(movie_path):
                try:
                    full_movie = mp.VideoFileClip(movie_path)
                    logging.info(f"Successfully loaded repaired video: {movie_path}")
                except Exception as e:
                    logging.error(f"Failed to load video even after repair: {e}")
                    if stream_instance:
                        message = {
                            "type": "error",
                            "text": f"Failed to load video even after repair attempt: {e}"
                        }
                        stream_instance.send_message(json.dumps(message))
                    return
            else:
                if stream_instance:
                    message = {
                        "type": "error",
                        "text": f"Failed to repair corrupted video file: {movie_path}"
                    }
                    stream_instance.send_message(json.dumps(message))
                return

        total_duration = full_movie.duration
        logging.info(f"Loaded video '{movie_name}.mp4' successfully. Total duration: {total_duration} seconds")
        if stream_instance:
            message = {
                "type": "info",
                "text": f"Loaded video '{movie_name}.mp4' successfully. Duration: {total_duration} seconds"
            }
            stream_instance.send_message(json.dumps(message))

        # Calculate number of clips needed
        clip_length = int(total_duration / clip_duration)
        clip_length_remainder = total_duration % clip_duration
        if clip_length_remainder > 0:
            clip_length += 1
            
        logging.info(f"Video will be split into {clip_length} clips of {clip_duration} seconds each")
        if stream_instance:
            message = {
                "type": "info",
                "text": f"Video will be split into {clip_length} clips of {clip_duration} seconds each"
            }
            stream_instance.send_message(json.dumps(message))

        clip_wav_list = []

        # Path to check if pre-processing is complete
        pre_google_processes = os.path.join(asc_dir, f"{movie_name}-mini-000.wav")

        if not os.path.isfile(pre_google_processes):
            # Split the movie into clips
            logging.info(f"Cutting video into {clip_duration} second clips...")
            if stream_instance:
                message = {
                    "type": "info",
                    "text": f"Cutting video into {clip_duration} second clips..."
                }
                stream_instance.send_message(json.dumps(message))
            
            for x in range(clip_length):
                start_seconds = x * clip_duration
                end_seconds = min(start_seconds + clip_duration, total_duration)
                
                try:
                    clip = full_movie.subclip(start_seconds, end_seconds)
                    clip_path = os.path.join(asc_dir, f"{movie_name}-{x:03d}.wav")
                    clip.audio.write_audiofile(clip_path, verbose=False)
                    clip_wav_list.append(clip_path)
                    logging.info(f"Created audio clip {x+1}/{clip_length}: {clip_path} ({start_seconds}-{end_seconds}s)")
                    if stream_instance:
                        message = {
                            "type": "info",
                            "text": f"Created audio clip {x+1}/{clip_length}: {start_seconds}-{end_seconds}s"
                        }
                        stream_instance.send_message(json.dumps(message))
                except Exception as e:
                    logging.error(f"Failed to create audio clip {x+1}/{clip_length}: {e}")
                    if stream_instance:
                        message = {
                            "type": "error",
                            "text": f"Failed to create audio clip {x+1}/{clip_length}: {e}"
                        }
                        stream_instance.send_message(json.dumps(message))
                    continue

            # Convert to mono and update clip_wav_list
            clip_wav_list = self.pydub_to_audio(asc_dir, movie_name, clip_length, stream_instance)

        # Rebuild clip_wav_list from directory if empty
        if not clip_wav_list:
            logging.info("Rebuilding clip_wav_list from existing .wav files.")
            if stream_instance:
                message = {
                    "type": "info",
                    "text": "Rebuilding clip_wav_list from existing .wav files."
                }
                stream_instance.send_message(json.dumps(message))
            for file in os.listdir(asc_dir):
                if file.endswith(".wav"):
                    wav_path = os.path.join(asc_dir, file)
                    clip_wav_list.append(wav_path)
                    logging.info(f"Found existing audio clip: {wav_path}")
                    if stream_instance:
                        message = {
                            "type": "info",
                            "text": f"Found existing audio clip: {wav_path}"
                        }
                        stream_instance.send_message(json.dumps(message))

        # Sort the clip_wav_list based on clip number extracted from filename
        try:
            clip_wav_list = sorted(
                clip_wav_list,
                key=lambda x: int(os.path.basename(x).split('-')[-1].split('.wav')[0])
            )
            logging.info("Sorted clip_wav_list for accurate mapping.")
            if stream_instance:
                message = {
                    "type": "info",
                    "text": "Sorted audio clips for accurate mapping."
                }
                stream_instance.send_message(json.dumps(message))
        except Exception as e:
            logging.error(f"Error sorting clip_wav_list: {e}")
            if stream_instance:
                message = {
                    "type": "error",
                    "text": f"Error sorting clip_wav_list: {e}"
                }
                stream_instance.send_message(json.dumps(message))
            return

        # Continue with transcription
        wav_dict = {}
        for ct, wa in enumerate(clip_wav_list):
            try:
                with sr.AudioFile(wa) as source:
                    # Adjust for ambient noise with gentler settings
                    recognizer.adjust_for_ambient_noise(source, duration=NOISE_REDUCE_TIME)
                    # Use lower energy threshold for better voice detection
                    recognizer.energy_threshold = ENERGY_THRESHOLD
                    audio = recognizer.record(source)
                    
                # Use more lenient recognition settings
                recog = recognizer.recognize_google(
                    audio,
                    language="en-US",
                    show_all=False
                )
                wav_dict[f"{movie_name}-{ct:03d}"] = recog
                logging.info(f"Transcribed [{movie_name}-{ct:03d}]: {recog}")
                if stream_instance:
                    location_seconds = f"{ct * clip_duration}-{(ct + 1) * clip_duration}"
                    message = {
                        "type": "transcription",
                        "clip": f"{movie_name}-{ct:03d}",
                        "text": recog
                    }
                    stream_instance.send_message(json.dumps(message))
            except sr.UnknownValueError:
                wav_dict[f"{movie_name}-{ct:03d}"] = "NO AUDIO"
                logging.warning(f"No audio detected in clip {wa}.")
                if stream_instance:
                    location_seconds = f"{ct * clip_duration}-{(ct + 1) * clip_duration}"
                    message = {
                        "type": "warning",  # Changed from error to warning
                        "clip": f"{movie_name}-{ct:03d}",
                        "text": f"No speech detected in this segment"  # More user-friendly message
                    }
                    stream_instance.send_message(json.dumps(message))
            except sr.RequestError as e:
                wav_dict[f"{movie_name}-{ct:03d}"] = "TRANSCRIPTION ERROR"
                logging.error(f"Could not request results from Google Speech Recognition service; {e}")
                if stream_instance:
                    message = {
                        "type": "error",
                        "clip": f"{movie_name}-{ct:03d}",
                        "text": f"TRANSCRIPTION ERROR: {e}"
                    }
                    stream_instance.send_message(json.dumps(message))
            except Exception as e:
                wav_dict[f"{movie_name}-{ct:03d}"] = "TRANSCRIPTION ERROR"
                logging.error(f"Error transcribing clip {wa}: {e}")
                if stream_instance:
                    message = {
                        "type": "error",
                        "clip": f"{movie_name}-{ct:03d}",
                        "text": f"TRANSCRIPTION ERROR: {e}"
                    }
                    stream_instance.send_message(json.dumps(message))

        # Save transcriptions to JSON as a list containing the existing dictionary
        try:
            os.makedirs(os.path.dirname(dialog_json), exist_ok=True)
            with io.open(dialog_json, "w", encoding='utf-8') as the_dialog:
                # Wrap wav_dict in a list
                json.dump([wav_dict], the_dialog, indent=4, sort_keys=True, ensure_ascii=False)
                logging.info(f"Saved transcriptions to {dialog_json}")
                if stream_instance:
                    message = {
                        "type": "info",
                        "text": f"Saved transcriptions to {dialog_json}"
                    }
                    stream_instance.send_message(json.dumps(message))
        except Exception as e:
            logging.error(f"Failed to write transcriptions to {dialog_json}: {e}")
            if stream_instance:
                message = {
                    "type": "error",
                    "text": f"Failed to write transcriptions to {dialog_json}: {e}"
                }
                stream_instance.send_message(json.dumps(message))

    def pydub_to_audio(self, asc_dir, movie_name, clip_length, stream_instance):
        """
        Converts stereo WAV files to mono and applies audio preprocessing for better voice clarity.
        Steps:
        1. Convert to mono
        2. Normalize audio
        3. Apply gentler bandpass filter to focus on voice frequencies
        """
        logging.info("Converting clips to mono audio and applying voice enhancement...")
        if stream_instance:
            message = {
                "type": "info",
                "text": "Converting clips to mono audio and applying voice enhancement..."
            }
            stream_instance.send_message(json.dumps(message))

        mini_clip_wav_list = []
        for x in range(clip_length):
            try:
                input_wav = os.path.join(asc_dir, f"{movie_name}-{x:03d}.wav")
                output_wav = os.path.join(asc_dir, f"{movie_name}-mini-{x:03d}.wav")
                
                if not os.path.exists(input_wav):
                    logging.warning(f"Input file not found: {input_wav}")
                    continue
                    
                # Load audio and convert to mono
                sound = AudioSegment.from_wav(input_wav)
                sound = sound.set_channels(1)
                
                # Normalize audio (less aggressively)
                sound = normalize(sound, headroom=0.1)  # Added headroom to prevent clipping
                
                # Convert to numpy array for scipy processing
                samples = np.array(sound.get_array_of_samples())
                
                # Apply gentler bandpass filter
                filtered_samples = apply_bandpass_filter(
                    samples,
                    sound.frame_rate,
                    LOW_CUTOFF,
                    HIGH_CUTOFF,
                    order=3  # Reduced from 5 to make filter gentler
                )
                
                # Convert back to AudioSegment
                filtered_sound = sound._spawn(filtered_samples.astype(np.int16))
                
                # Export processed audio
                filtered_sound.export(output_wav, format="wav")
                mini_clip_wav_list.append(output_wav)
                
                # Remove original file
                os.remove(input_wav)
                
                logging.info(f"Processed and enhanced audio: {output_wav}")
                if stream_instance:
                    message = {
                        "type": "info",
                        "text": f"Processed and enhanced audio: {output_wav}"
                    }
                    stream_instance.send_message(json.dumps(message))
            except Exception as e:
                logging.warning(f"Failed to process clip {x}: {e}")
                if stream_instance:
                    message = {
                        "type": "error",
                        "text": f"Failed to process clip {x}: {e}"
                    }
                    stream_instance.send_message(json.dumps(message))
                continue

        return mini_clip_wav_list

class RequestUiSearch(object):
    clip_duration = RequestSpeech.clip_duration

    def uiSearch(self, ui_search_input, video_set):
        second_sets = {}
        try:
            word_list = [word.strip().lower() for word in ui_search_input.split(",") if word.strip()]
            logging.info(f"Search terms: {word_list}")

            # Collect all dialog JSON file paths
            dialog_json_list = []
            for key, video_name in video_set.items():
                dialog_json_path = os.path.join("public", "results-json", f"{video_name}-dialog.json")
                if os.path.isfile(dialog_json_path):
                    dialog_json_list.append(dialog_json_path)
                    logging.info(f"Added dialog JSON path: {dialog_json_path}")
                else:
                    logging.warning(f"Dialog JSON file does not exist: {dialog_json_path}")

            # Function to find words in strings
            def words_in_string(a_string, word_list):
                true_sets = []
                for phrase in word_list:
                    if phrase in a_string:
                        true_sets.append(a_string.replace("-", " "))
                return sorted(true_sets, reverse=True)

            # Aggregate transcriptions from all JSON files
            dialog_data = {}
            for dialog_json_path in dialog_json_list:
                try:
                    with open(dialog_json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                            dialog_data.update(data[0])
                            logging.info(f"Loaded data from {dialog_json_path}")
                        else:
                            logging.warning(f"Unexpected JSON structure in {dialog_json_path}")
                except Exception as e:
                    logging.warning(f"Failed to load {dialog_json_path}: {e}")
                    continue

            # Search for words in transcriptions
            for video_clip, video_clip_text in dialog_data.items():
                if video_clip_text != "NO AUDIO":
                    video_clip_text = video_clip_text.lower()
                    for word in words_in_string(video_clip_text, word_list):
                        try:
                            w1, w2 = video_clip.split("-")
                            start_time = int(w2) * self.clip_duration
                            second_sets[f"{w1}-{start_time}"] = f"{word}-word"
                            logging.info(f"Found '{word}' in {video_clip} at {start_time} seconds.")
                        except ValueError as e:
                            logging.error(f"Error parsing video_clip '{video_clip}': {e}")
            return second_sets
        except Exception as e:
            logging.error(f"Error during UI search: {e}")
            return second_sets

class MultithreadRun(object):

    def __init__(self, stream_instance):
        self.stream_instance = stream_instance

    def processSpeech(self, video_name):
        rs = RequestSpeech()
        rs.processSpeech(video_name, stream_instance=self.stream_instance)
