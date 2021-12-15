from google.cloud import datastore
from flask import Flask, request, jsonify

app = Flask(__name__)
client = datastore.Client()

@app.route('/')
def index():
    return "Please navigate to API to use this."\

@app.route('/boats', methods=['POST'])
def boats_get_post():
    if request.method == 'POST':
        content = request.get_json()

        if len(content) != 3:
            return (jsonify({'Error': 'The request object is missing at least one of the required attributes'}), 400)

        new_boat = datastore.entity.Entity(key=client.key("boats"))
        new_boat.update({"name": content["name"], "type": content["type"],
          "length": content["length"]})
        client.put(new_boat)

        return (jsonify({"id": new_boat.key.id, "name": content["name"], "type": content["type"], 
          "length": content["length"], "self": str(request.url) + "/" + str(new_boat.key.id)}), 201)

    else:
        return 'Method not recognized'



@app.route('/boats/<id>', methods=['GET'])
def boats_put_delete(id):
    if request.method == 'GET':
        content = request.get_json()
        boat_key = client.key("boats", int(id))
        boat = client.get(key = boat_key)

        if boat == None:
            return (jsonify({'Error': 'No boat with this boat_id exists'}), 404)

        boat["id"] = id
        boat["self"] = str(request.url)

        return (jsonify(boat), 200)

    else:
        return 'Method not recognized'



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)