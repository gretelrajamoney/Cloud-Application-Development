from google.cloud import datastore
from flask import Flask, request, jsonify
from requests_oauthlib import OAuth2Session
from google.auth.transport import requests
from google.oauth2 import id_token
import constants


app = Flask(__name__)
client = datastore.Client()


CLIENT_ID = "282765905850-8sfpdir30aoblprho7lboua2bllcs4n7.apps.googleusercontent.com"
CLIENT_SECRET = "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"
SCOPE_URI = ['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']
REDIRECT_URI = "https://hw7-rajamong.wl.r.appspot.com/oauth"
AUTHORIZATION_URI = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URI = "https://accounts.google.com/o/oauth2/token"
OAUTH = OAuth2Session(CLIENT_ID, redirect_uri = REDIRECT_URI, scope = SCOPE_URI)
REQUEST_GET = requests.Request()
ACCESS_TYPE = "offline"
MESSAGE_SENT = "select_account"



def verify():
    jwt_token = request.headers.get("Authorization")

    if jwt_token:
            jwt_token = jwt_token.split(" ")[1]

            try:
                jwt_sub = id_token.verify_oauth2_token(jwt_token, REQUEST_GET, CLIENT_ID)[constants.sub]
                return jwt_sub
            
            except:
                jwt_sub = "not valid"
                return jwt_sub
        
    else:    
        jwt_sub = "not valid"
        return jwt_sub



@app.route('/')
def MainPage():
    authorization_url, state = OAUTH.authorization_url(AUTHORIZATION_URI, access_type = ACCESS_TYPE, prompt = MESSAGE_SENT)
    return '<h1>welcome to the main page !!</h1>\n <p>click <a href=%s>here</a> to generate your JWT !!</p>' % authorization_url



@app.route('/oauth')
def OAuthHandler():
    token = OAUTH.fetch_token(TOKEN_URI, authorization_response = request.url, client_secret = CLIENT_SECRET)
    idinfo = id_token.verify_oauth2_token(token["id_token"], REQUEST_GET, CLIENT_ID)
    return '<h1>your generated JWT is: </h1>' + token["id_token"] 



@app.route('/verify-jwt')
def VerifyHandler():
    idinfo = id_token.verify_oauth2_token(request.args[constants.jwt], REQUEST_GET, CLIENT_ID)
    return (repr(idinfo) + "<br><br> the user is: " + idinfo[constants.email])



@app.route('/boats', methods = ["POST", "GET"])
def get_post_boats():
    if request.method == "POST":

        jwt_sub = str(verify())

        if jwt_sub == "not valid":
            return (jsonify(""), 401)

        else:
            content = request.get_json()
            new_boat = datastore.entity.Entity(key = client.key(constants.boats))
            new_boat.update({"name": content["name"], "type": content["type"], "length": content["length"], "public": content["public"], "owner": jwt_sub})
            client.put(new_boat) 
            send_boat = ({"id": new_boat.key.id, "name": content["name"], "type": content["type"], "length": content["length"], "public": content["public"], "owner": jwt_sub})
            return (jsonify(send_boat), 201)


    elif request.method == "GET":
        jwt_sub = str(verify())
        query = client.query(kind = constants.boats)

        if jwt_sub == "not valid":
            query.add_filter(constants.public, "=", True)
            all_boats = list(query.fetch())

            for e in all_boats:
                e[constants.id] = e.key.id

            return (jsonify(all_boats), 200)
        
        else:
            query.add_filter(constants.owner, "=", jwt_sub)
            all_boats = list(query.fetch())

            for e in all_boats:
                e[constants.id] = e.key.id

            return (jsonify(all_boats), 200)



@app.route('/owners/<owner_id>/boats', methods = ["GET"])
def get_boats(owner_id):
    if request.method == "GET":
        query = client.query(kind = constants.boats)
        query.add_filter(constants.owner, "=", owner_id)
        query.add_filter(constants.public, "=", True)
        owners_boats = list(query.fetch())

        for e in owners_boats:
            e[constants.id] = e.key.id

        return (jsonify(owners_boats), 200)



@app.route('/boats/<boat_id>', methods = ["DELETE"])
def delete_boats(boat_id):
    if request.method == "DELETE":

        jwt_sub = str(verify())

        if jwt_sub == "not valid":
            return (jsonify(""), 401)

        else:
            boat_key = client.key(constants.boats, int(boat_id))
            boat = client.get(key = boat_key)

            if boat == None or boat[constants.owner] != jwt_sub:
                return (jsonify(""), 403)

            client.delete(boat_key)
            return (jsonify(""), 204)



if __name__ == '__main__':
    	app.run(host='127.0.0.1', port=8080, debug=True)
