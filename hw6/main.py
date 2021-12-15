from google.cloud import datastore
from flask import Flask, request, render_template, redirect, session
import flask
import logging 
import requests
import json
import uuid
import string
import urllib
import random
import constants

app = Flask(__name__)
make_key = str(uuid.uuid4())
app.secret_key = make_key

client = datastore.Client()


SCOPE_URI = "https://www.googleapis.com/auth/userinfo.profile"
TOKEN_URI = "https://oauth2.googleapis.com/token"
BASE_URI = "https://accounts.google.com/"
ME_URI = "https://people.googleapis.com/v1/names"
API_URI = "https://www.googleapis.com/oauth2/v1/"
REDIRECT_URI = "https://hw6-rajamong-331402.wl.r.appspot.com/oauth"
CLIENT_ID = "456833472426-n1rosnokseo9ek1vgfqq52mdj3egr11r.apps.googleusercontent.com"
CLIENT_SECRET = "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"
GRANT_TYPE = "authorization_code"
RANDOM_KEY = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(8))


@app.route('/')
def MainPage():
    return render_template('index.html')


@app.route('/gauth')
def GAuthHandler():
	flask.session[constants.state] = RANDOM_KEY
	return redirect(f'{BASE_URI}o/oauth2/v2/auth?scope={SCOPE_URI}&access_type=offline&response_type=code&redirect_uri={REDIRECT_URI}&client_id={CLIENT_ID}&state={RANDOM_KEY}')


@app.route('/oauth')
def OAuthHandler():
        information = {"code": request.args.get(constants.code), "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "redirect_uri": REDIRECT_URI, "grant_type": GRANT_TYPE}
        result = requests.post(TOKEN_URI, data=information).json()

        user = requests.get(API_URI + "userinfo?alt=json&" + constants.access + "=" + result[constants.access]).json()
        
        newstate = request.args.get(constants.state)
        
        if newstate != flask.session[constants.state]:
            return ("the state is incorrect", 404)

        else:

            fullname = user[constants.name]
            names = fullname.split(" ")
            firstname = names[0]
            lastname = names[2]

            return ('<h1>Welcome to the User Page !!</h1>\n <h2>Here I will be displaying your information !!</h2>\n\n <h3>First Name: </h3>' + firstname + '<h3>Last Name: </h3>' + lastname + '<h3>Current State: </h3>'+ newstate)


if __name__ == '__main__':
    	app.run(host='127.0.0.1', port=8080, debug=True)

