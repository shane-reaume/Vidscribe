import flask
import flask.scaffold
import json
import webbrowser
from flask_restful import reqparse, Api, Resource
from crux_processor import video_per_second as vps
flask.helpers._endpoint_from_view_func = flask.scaffold._endpoint_from_view_func

vps_request_speech = vps.RequestSpeech()
vps_request_search = vps.RequestUiSearch()
vps_multi = vps.MultithreadRun()
vps_request_stream = vps.Stream()

port = 4000
static_folder = 'public'
url = "http://localhost:{0}".format(port) + "/" + static_folder
app = flask.Flask(__name__, static_folder=static_folder)
api = Api(app)


@app.route('/stream')
def stream():
    return flask.Response(vps_request_stream.event_stream(),
                          mimetype="text/event-stream")


# let's open up COR's so demos  are easy
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response


# we filter what args we accept with type and how submitted
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
        # verify and parse args
        args123 = parser.parse_args()
        video_name = args123['videoName']
        print("is it: " + video_name)

        vps_multi.processSpeech(video_name)
        vps_request_speech.processSpeech(video_name)

        return video_name + " speech processed", 201


class SearchList(Resource):

    def post(self):
        args = parser.parse_args(req=None, strict=False)
        ui_search_input = args['word1']
        video_set = {'video1': args['v1'], 'video2': args['v2'], 'video3': args['v3']}
        video_clean_words = vps_request_search.uiSearch(ui_search_input, video_set)
        json_data = json.dumps(video_clean_words)
        return json_data, 201


class Root(Resource):

    def get(self):
        return app.send_static_file('index.html')


class SearchUI(Resource):

    def get(self):
        return app.send_static_file('searchui.html')


class VideosStarter(Resource):

    def get(self, video):
        print(video)
        return app.send_static_file('videos/' + video)


# Actually set up the Api resource routing here
api.add_resource(Process, '/api/Process')
api.add_resource(SearchList, '/api/Words')

# Static Pages/files
api.add_resource(VideosStarter, '/api/Video/starter/<string:video>')
api.add_resource(Root, '/public/')
api.add_resource(SearchUI, '/public/search')

if __name__ == '__main__':
    webbrowser.open_new(url)
    app.run(port=port, debug=False, threaded=True)
