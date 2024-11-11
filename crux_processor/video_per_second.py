import moviepy.editor as mp
import json
import os
from pydub import AudioSegment
import speech_recognition as sr
import io

recognizer = sr.Recognizer()


class MultithreadRun(object):

    def processSpeech(self, video_name):
        rs = RequestSpeech()
        rs.processSpeech(video_name)


class RequestSpeech(object):
    clip_duration = 10  # google

    def processSpeech(self, arg1):
        try:
            movie_name = arg1
        except:
            movie_name = ""
            print("No Movie in arg1, exiting.")
            exit(0)

        clip_duration = self.clip_duration

        movie_path = "public/videos/%s.mp4" % movie_name
        if not os.path.exists("asc/%s/" % movie_name):
            os.makedirs("asc/%s/" % movie_name, 0o755)
        mini_clip_path = "asc/%s/" % movie_name
        dialog_json = "public/results-json/%s-dialog.json" % movie_name

        # ---- moviepy start_seconds ------------------
        full_movie = mp.VideoFileClip(movie_path)
        clip_length = int(full_movie.duration / clip_duration)
        clip_length_remainder = int(full_movie.duration % clip_duration)
        if clip_length_remainder >= 1:
            clip_length = clip_length + 1
        clip_wav_list = []

        '''
        Check to see if pre- Recognize Google activity complete
        We want to NOT show all this in the demo's, so lets break it out when ran once
        '''
        pre_google_processes = "asc/" + movie_name + "/" + movie_name + "-mini-000.wav"
        if not os.path.isfile(pre_google_processes):
            def pydub_to_audio():
                start_seconds = 0
                end_seconds = clip_duration
                print("\nconverting clips to mono audio...\n")
                Stream.data_pack['speech1'] = "\nconverting clips to mono audio...\n"
                for x in range(0, clip_length):
                    try:
                        sound = AudioSegment.from_wav("%s%s-%03d.wav" % (mini_clip_path, movie_name, x)).set_channels(1)
                        newsound = "%s%s-mini-%03d.wav" % (mini_clip_path, movie_name, x)
                        sound.export(newsound, format="wav")
                        clip_wav_list.append(str(newsound))
                        if os.path.exists("%s%s-%03d.wav" % (mini_clip_path, movie_name, x)):
                            os.remove("%s%s-%03d.wav" % (mini_clip_path, movie_name, x))
                    except:
                        print('continue...')
                    start_seconds = start_seconds + clip_duration
                    end_seconds = end_seconds + clip_duration
                return clip_wav_list

            # set .wav clip length
            start_seconds = 0
            end_seconds = clip_duration
            print("cutting video into %s second clips..." % end_seconds)
            Stream.data_pack['speech1'] = "cutting video into %s second clips..." % end_seconds
            for x in range(0, clip_length):
                try:
                    clip2 = full_movie.subclip(start_seconds, end_seconds)
                except:
                    clip2 = full_movie.subclip(start_seconds, int(full_movie.duration) - 2)
                clip2.audio.write_audiofile("%s%s-%03d.wav" % (mini_clip_path, movie_name, x), verbose=False)
                start_seconds = start_seconds + clip_duration
                end_seconds = end_seconds + clip_duration
                if end_seconds > full_movie.duration:
                    end_seconds = full_movie.duration
            # ---- Pydub start use to convert to mono -------------------
            pydub_to_audio()

        '''
        Let's rebuild clip_wav_list off of directory .wav content
        - previously it just carried over, but we break that off on second runs for demo
        '''
        if not clip_wav_list:
            clip_wav_list = []
            for file in os.listdir("asc/" + movie_name):
                if file.endswith(".wav"):
                    clip_wav_list.append("asc/" + movie_name + "/" + str(file))
                    print("your file: " + file)

        wav_dict = {}
        ct = 0
        for wa in clip_wav_list:
            with sr.WavFile(wa) as source:
                audio = recognizer.record(source)
            try:
                recog = str(recognizer.recognize_google(audio, show_all=False))
                wav_dict["%s-%03d" % (movie_name, ct)] = recog
                print("speech: " + recog)
                location_seconds = str(ct * clip_duration) + "-" + str((ct + 1) * clip_duration)
                Stream.data_pack['speech1'] = "[" + movie_name + " " + location_seconds + "] " + recog
            except sr.UnknownValueError:
                wav_dict["%s-%03d" % (movie_name, ct)] = "NO AUDIO"
                print("...no audio...")
            except sr.RequestError as e:
                print("Could not request results from Google Speech Recognition service; {0}".format(e))
            except IndexError:
                print("No internet connection")
            except KeyError:
                print("Invalid API key or quota maxed out")
            except LookupError:
                try:
                    list = recognizer.recognize_google(audio, True)
                    for prediction in list:
                        print("\n " + prediction["text"] + " (" + str(prediction["confidence"] * 100) + "%)")
                        wav_dict["%s-%03d" % (movie_name, ct)] = list[0][
                            "text"]  # first transcription if nothing exceptional for json
                except:
                    wav_dict["%s-%03d" % (movie_name, ct)] = "NO AUDIO"
            ct += 1
        with io.open(dialog_json, "w", encoding='utf-8') as the_dialog:
            the_dialog.seek(0)
            the_dialog.truncate()
            the_dialog.write('[')
            the_dialog.write(json.dumps(wav_dict, indent=4, sort_keys=True, ensure_ascii=False))
            the_dialog.write(']')


class RequestUiSearch(object):
    clip_duration = RequestSpeech.clip_duration

    def uiSearch(self, ui_search_input, video_set):
        second_sets = {}
        try:
            word_list = ui_search_input.split(",")

            # align active video set names to list of json sets
            dialog_json_list = []
            try:
                for key, video_name in video_set.items():
                    dialog_json_list.append("public/results-json/%s-dialog.json" % video_name)
            except:
                print("one of the dialog json does not yet exist")

            # Compare your word/phrases with dialog.json files
            def words_in_string(a_string, word_list):
                true_sets = []
                [true_sets.append(a_string.replace("-", " ")) for phrase in word_list if phrase in a_string]
                return sorted(true_sets, reverse=True)

            # ### START GOOGLE SEARCH ############################
            clip_duration = self.clip_duration
            dialog_data = {}
            try:
                for dialog_json_path in dialog_json_list:
                    try:
                        dialog_json_file = open(str(dialog_json_path))
                        dialog_json_string = dialog_json_file.read()
                        dialog_data.update(json.loads(dialog_json_string)[0])
                    except:
                        continue
                for video_clip, video_clip_text in dialog_data.items():
                    if video_clip_text != "NO AUDIO":
                        video_clip_text = video_clip_text.lower()
                        for word in words_in_string(video_clip_text, word_list):
                            w1, w2 = video_clip.split("-")
                            second_sets[w1 + "-" + str(int(w2) * clip_duration)] = word + "-word"
            except:
                print("snap, error at dialog block")
            return second_sets
        except:
            print("well that did not work")
        return second_sets


class Stream(object):
    data_pack = {'speech1': ''}

    def event_stream(self):
        yield 'data: %s\n\n' % json.dumps(self.data_pack)
