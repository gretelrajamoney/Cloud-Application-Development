from flask import Blueprint, request, jsonify
from google.cloud import datastore
import json
import constants

client = datastore.Client()

bp = Blueprint('load', __name__, url_prefix='/loads')

@bp.route('', methods=['POST','GET'])
def loads_get_post():
    if request.method == 'POST':
        content = request.get_json()
        attributes = 3

        if len(content) != attributes:
            return (jsonify({'error': 'object is missing one or more of the required attributes'}), 400)

        new_load = datastore.entity.Entity(key=client.key(constants.loads))
        new_load.update({"weight": content["weight"], "carrier": None,
          "content": content["content"], "delivery_date": content["delivery_date"]})

        client.put(new_load)

        new_load['id'] = new_load.key.id
        new_load['self'] = request.url + '/' + str(new_load['id'])
        return (jsonify(new_load), 201)
    

    elif request.method == 'GET':
        query = client.query(kind=constants.loads)
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
            e["self"] = str(request.url) + "/" + str(e["id"])

            if e[constants.carrier] != None:
                carrier_id = e[constants.carrier]['id']
                e[constants.carrier]["self"] = request.url_root + constants.boats + "/" + str(carrier_id)

        output = {constants.loads: results}

        if next_url:
            output["next"] = next_url

        return (jsonify(output), 200)

    else:
        return 'Method not recogonized'


@bp.route('/<id>', methods=['GET','DELETE'])
def loads_put_delete(id):
    if request.method == 'GET':
        content = request.get_json()
        load_key = client.key(constants.loads, int(id))
        load = client.get(key=load_key)

        if load == None:
            return (jsonify({"error": "there is no load with this id"}), 404)

        if load[constants.carrier]:
            load_id = load[constants.carrier]["id"]
            load[constants.carrier]["self"] = request.url_root + constants.boats + "/" + str(load_id)

        load["id"] = id
        load["self"] = request.url

        return (jsonify(load), 200)

    elif request.method == 'DELETE':
        key = client.key(constants.loads, int(id))
        load = client.get(key=key)

        if load == None:
            return (jsonify({"error": "there is no load with this id"}), 404)

        if load[constants.carrier] != None:
            carrier_id = load[constants.carrier]["id"]
            boat = client.get(key=client.key(constants.boats, carrier_id))
            load_id = load.key.id
            boat[constants.loads].remove({"id": load_id})
            client.put(boat)

        client.delete(key)
        return (jsonify(''),204)
        
    else:
        return 'Method not recogonized'