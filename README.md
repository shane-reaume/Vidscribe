# Flask-Video-API

`python api.py`

- This is all you need to know if you just want to fire up, your UI will open in default browser.

- `public` is your static UI folder
- `video_api` is your rest services that allows a lot of the services
    - This is bult on `Flask` so any controllers or modification of endpoints are based on Flask
    - `flask_restful` was used as base for video_api if you need to see docs
- TODO: lets create a list of API endpoints once we create otherwise they are in the `api.py` file for now

## Setup for Miniconda3 Python 3.11

- install and use Minconda3 3.11
- `pip install ez_setup`
- `pip install setuptools`

### install dependencies, this creates requirements.txt
- `pip install pipreqs`
- `pipreqs C:\Users\shane\PycharmProjects\videoAnalysisUI3 --force`

### Install libraries in new env
- `pip install -r requirements.txt`