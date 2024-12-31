import flask
import flask.scaffold
import json
import webbrowser
from flask_restful import reqparse, Api, Resource
from crux_processor import video_per_second as vps
import os

flask.helpers._endpoint_from_view_func = flask.scaffold._endpoint_from_view_func

# Instantiate Stream
vps_request_stream = vps.Stream()

# Instantiate MultithreadRun with the Stream instance
vps_multi = vps.MultithreadRun(stream_instance=vps_request_stream)

# Instantiate RequestUiSearch
vps_request_search = vps.RequestUiSearch()

port = 4000
static_folder = 'public'
url = f"http://localhost:{port}/{static_folder}"
app = flask.Flask(__name__, static_folder=static_folder)
api = Api(app)


@app.route('/stream')
def stream():
    return flask.Response(vps_request_stream.event_stream(),
                          mimetype="text/event-stream")


# Allow CORS for all domains (for demo purposes)
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response


# Define request arguments
parser = reqparse.RequestParser()
parser.add_argument('seconds1', type=int, location='form')
parser.add_argument('seconds2', type=int, location='form')
parser.add_argument('seconds3', type=int, location='form')
parser.add_argument('videoName', type=str, location='form')
parser.add_argument('v1', type=str, location='form')
parser.add_argument('v2', type=str, location='form')
parser.add_argument('v3', type=str, location='form')
parser.add_argument('word1', type=str, location='form')


class Process(Resource):

    def post(self):
        # Parse arguments
        args123 = parser.parse_args()
        video_name = args123.get('videoName')
        print(f"Processing video: {video_name}")

        if not video_name:
            return {"error": "No video name provided."}, 400

        # Start processing in a separate thread
        vps_multi.processSpeech(video_name)

        return {
            "status": "completed",
            "message": f"{video_name} speech processing completed.",
            "video_name": video_name
        }, 201


class SearchList(Resource):

    def post(self):
        args = parser.parse_args()
        ui_search_input = args.get('word1')
        video_set = {
            'video1': args.get('v1'),
            'video2': args.get('v2'),
            'video3': args.get('v3')
        }

        if not ui_search_input or not all(video_set.values()):
            return {"error": "Invalid search input or video set."}, 400

        video_clean_words = vps_request_search.uiSearch(ui_search_input, video_set)
        return video_clean_words, 201


class Root(Resource):

    def get(self):
        return app.send_static_file('index.html')


class SearchUI(Resource):

    def get(self):
        return app.send_static_file('searchui.html')


class VideosStarter(Resource):

    def get(self, video):
        print(f"Serving video: {video}")
        video_path = os.path.join(app.static_folder, 'videos', video)
        if os.path.isfile(video_path):
            return app.send_static_file(os.path.join('videos', video))
        else:
            return {"error": "Video not found."}, 404


# Set up the API resource routing
api.add_resource(Process, '/api/Process')
api.add_resource(SearchList, '/api/Words')

# Static Pages/files
api.add_resource(VideosStarter, '/api/Video/starter/<string:video>')
api.add_resource(Root, '/public/')
api.add_resource(SearchUI, '/public/search')

if __name__ == '__main__':
    # Open the URL in the default web browser
    webbrowser.open_new(url)
    app.run(port=port, debug=False, threaded=True)
