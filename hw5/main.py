from google.cloud import datastore
from flask import Flask, request, jsonify
import json
import constants
from json2html import *

app = Flask(__name__)
client = datastore.Client()

@app.route('/')
def index():
    return "Please navigate to API to use this."\

@app.route('/boats', methods=['POST','GET'])
def boats_get_post():
    if request.method == 'POST':

        if "application/json" in request.accept_mimetypes:

            if "application/json" not in request.content_type:
                result = (jsonify({'error': 'sent MIME type not supported'}))
                result.mimetype = 'application/json'
                result.status_code = 415
                return result

            content = request.get_json()

            if len(content) < 3:
                result = (jsonify({'error': 'missing one or more required attributes'}))
                result.mimetype = 'application/json'
                result.status_code = 400
                return result

            if len(content) > 3:
                result = (jsonify({'error': 'added unnecessary additional attributes'}))
                result.mimetype = 'application/json'
                result.status_code = 400
                return result

            validatename = content["name"]
            validatetype = content["type"]

            if len(validatename) > 20:
                result = (jsonify({'error': 'the name is too long'}))
                result.mimetype = 'application/json'
                result.status_code = 400
                return result

            for character in validatename:
                if character.isdigit():
                    result = (jsonify({'error': 'the name contains numbers'}))
                    result.mimetype = 'application/json'
                    result.status_code = 400
                    return result

            for character in validatetype:
                if character.isdigit():
                    result = (jsonify({'error': 'the type contains numbers'}))
                    result.mimetype = 'application/json'
                    result.status_code = 400
                    return result

            if len(validatetype) > 20:
                result = (jsonify({'error': 'the type is too long'}))
                result.mimetype = 'application/json'
                result.status_code = 400
                return result

            new_boat = datastore.entity.Entity(key=client.key(constants.boats))
            new_boat.update({"name": content["name"], "type": content["type"],
            "length": content["length"]})
            client.put(new_boat)

            finished_boat = ({"id": str(new_boat.key.id), "name": new_boat["name"], "type": new_boat["type"],
            "length": new_boat["length"], "self": request.base_url + "/" + str(new_boat.key.id)})
            
            if "application/json" in request.accept_mimetypes:
                result = jsonify(finished_boat)
                result.mimetype = 'application/json'
                result.status_code = 201

            return result
        
        else:
            result = (jsonify({'error': 'requested MIME type not supported'}))
            result.mimetype = 'application/json'
            result.status_code = 406
            return result
    
    elif request.method == 'GET':

        if "application/json" in request.accept_mimetypes:
            query = client.query(kind=constants.boats)
            q_limit = int(request.args.get('limit', '3'))
            q_offset = int(request.args.get('offset', '0'))
            l_iterator = query.fetch(limit= q_limit, offset=q_offset)
            pages = l_iterator.pages
            results = list(next(pages))
        
            if l_iterator.next_page_token:
                next_offset = q_offset + q_limit
                next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
            else:
                next_url = None

            for e in results:
                e["id"] = e.key.id
                e["self"] = request.url + "/" + str(e["id"])

            output = {constants.boats: results}

            if next_url:
                output["next"] = next_url

            
            result = (jsonify(output))
            result.mimetype = "applicaton/json"
            result.status_code = 200
            return result

        else:
            result = (jsonify({'error': 'requested MIME type not supported'}))
            result.mimetype = 'application/json'
            result.status_code = 406
            return result

    else:
        result = (jsonify({'error': 'this method is not allowed'}))
        result.mimetype = 'application/json'
        result.status_code = 405
        return result


@app.route('/boats/<id>', methods=['PUT','PATCH','GET','DELETE', 'POST'])
def boats_put_patch_get_delete(id):
    if request.method == 'PUT':
        if 'application/json' in request.accept_mimetypes:
            if "application/json" not in request.content_type:
                result = (jsonify({'error': 'sent MIME type not supported'}))
                result.mimetype = 'application/json'
                result.status_code = 415
                return result

            content = request.get_json()
            content_key = content.keys()

            if "id" in content_key:
                result = (jsonify({'error': 'cannot change the id of the boat'}))
                result.mimetype = 'application/json'
                result.status_code = 403
                return result

            if len(content) != 3:
                result = (jsonify({'error': 'missing one or more required attributes'}))
                result.mimetype = 'application/json'
                result.status_code = 400
                return result

            boat_key = client.key(constants.boats, int(id))
            boat = client.get(key=boat_key)

            if boat == None:
                result = (jsonify({'error': 'no boat with this id exists'}))
                result.mimetype = 'application/json'
                result.status_code = 404
                return result

            boat.update({"name": content["name"], "type": content["type"],
            "length": content["length"]})
            client.put(boat)

            finished_boat = ({"id": str(boat.key.id), "name": boat["name"], "type": boat["type"],
            "length": boat["length"], "self": request.base_url})

        
            result = (jsonify(finished_boat))
            result.mimetype = 'application/json'
            result.headers.set('Location', request.base_url)
            result.status_code = 303
            return result

        else:
            result = (jsonify({'error': 'requested MIME type not supported'}))
            result.mimetype = 'application/json'
            result.status_code = 406
            return result

    elif request.method == 'PATCH':
        if 'application/json' in request.accept_mimetypes:
            if "application/json" not in request.content_type:
                result = (jsonify({'error': 'sent MIME type not supported'}))
                result.mimetype = 'application/json'
                result.status_code = 415
                return result

            content = request.get_json()

            boat_key = client.key(constants.boats, int(id))
            boat = client.get(key=boat_key)
            content_key = content.keys()

            if boat == None:
                result = (jsonify({'error': 'no boat with this id exists'}))
                result.mimetype = 'application/json'
                result.status_code = 404
                return result

            if "name" in content_key:
                boat.update({"name": content["name"]})

            if "type" in content_key:
                boat.update({"type": content["type"]})

            if "length" in content_key:
                boat.update({"length": content["length"]})

            if "id" in content_key:
                result = (jsonify({'error': 'cannot change the id of the boat'}))
                result.mimetype = 'application/json'
                result.status_code = 403
                return result

            client.put(boat)

            finished_boat = ({"id": str(boat.key.id), "name": boat["name"], "type": boat["type"],
            "length": boat["length"], "self": request.base_url})

            result = (jsonify(finished_boat))
            result.mimetype = 'application/json'
            result.status_code = 200
            return result

        else:
            result = (jsonify({'error': 'requested MIME type not supported'}))
            result.mimetype = 'application/json'
            result.status_code = 406
            return result


    elif request.method == 'GET':
        if 'application/json' or 'text/html' in request.accept_mimetypes:
            content = request.get_json()
            boat_key = client.key(constants.boats, int(id))
            boat = client.get(key=boat_key)

            if boat == None:
                result = (jsonify({'error': 'no boat with this id exists'}))
                result.mimetype = 'application/json'
                result.status_code = 404
                return result

            finished_boat = ({"id": str(boat.key.id), "name": boat["name"], "type": boat["type"],
            "length": boat["length"], "self": request.base_url})

            if 'application/json' in request.accept_mimetypes:
                result = (jsonify(finished_boat))
                result.mimetype = 'application/json'
                result.status_code = 200
                return result

            if 'text/html' in request.accept_mimetypes:
                result = (jsonify(json2html.convert(json = json.dumps(finished_boat))))
                result.headers.set('Content-Type', 'text/html')
                result.status_code = 200
                return result

        else:
            result = (jsonify({'error': 'requested MIME type not supported'}))
            result.mimetype = 'application/json'
            result.status_code = 406
            return result

    elif request.method == 'DELETE':
        if 'application/json' in request.accept_mimetypes:
            boat_key = client.key(constants.boats, int(id))
            boat = client.get(key=boat_key)

            if boat == None:
                result = (jsonify({'error': 'no boat with this id exists'}))
                result.mimetype = 'application/json'
                result.status_code = 404
                return result

            client.delete(boat_key)

            result = (jsonify(''))
            result.mimetype = 'application/json'
            result.status_code = 204
            return result
    
        else:
            result = (jsonify({'error': 'requested MIME type not supported'}))
            result.mimetype = 'application/json'
            result.status_code = 406
            return result

    elif request.method == 'POST':
        if 'application/json' in request.accept_mimetypes:
            if "application/json" not in request.content_type:
                result = (jsonify({'error': 'sent MIME type not supported'}))
                result.mimetype = 'application/json'
                result.status_code = 415
                return result

            result = (jsonify({'error': 'cannot create boat with this used id'}))
            result.mimetype = 'application/json'
            result.status_code = 403
            return result

        else:
            result = (jsonify({'error': 'requested MIME type not supported'}))
            result.mimetype = 'application/json'
            result.status_code = 406
            return result

    else:
        result = (jsonify({'error': 'this method is not allowed'}))
        result.mimetype = 'application/json'
        result.status_code = 405
        return result


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)