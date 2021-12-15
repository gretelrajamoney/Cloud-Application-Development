from flask import Blueprint, request, jsonify
from google.cloud import datastore
import json
import constants

client = datastore.Client()

bp = Blueprint('boat', __name__, url_prefix='/boats')

@bp.route('', methods=['POST','GET'])
def boats_get_post():
    if request.method == 'POST':
        content = request.get_json()
        attributes = 3
    
        if len(content) != attributes:
            return (jsonify({"error": "object is missing one or more of the required attributes"}), 400)

        new_boat = datastore.entity.Entity(key=client.key(constants.boats))
        new_boat.update({"name": content["name"], "type": content["type"],
          "length": content["length"], constants.loads: []})

        client.put(new_boat)
        new_boat["id"] = new_boat.key.id
        new_boat["self"] = request.url + '/' + str(new_boat["id"])

        return (jsonify(new_boat), 201)
    
    elif request.method == 'GET':
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

            if (len(e[constants.loads])  > 0):
                for one_load in e[constants.loads]:
                    one_load_id = str(one_load["id"])
                    one_load["self"] = request.url_root + constants.loads + "/" + one_load_id

        output = {constants.boats: results}

        if next_url:
            output["next"] = next_url

        return (jsonify(output), 200)

    else:
        return 'Method not recogonized'


@bp.route('/<id>', methods=['GET','DELETE'])
def boats_get_delete(id):
    if request.method == 'GET':
        boat_key = client.key(constants.boats, int(id))
        boat = client.get(key=boat_key)

        if boat == None:
            return (jsonify({"error": "no boat with this id exists"}), 404)

        for one_load in boat[constants.loads]:
            one_load_id = str(one_load["id"])
            one_load["self"] = request.url_root + constants.loads + "/" + one_load_id

        boat["id"] = id
        boat["self"] = request.url

        return (jsonify(boat), 200)

    elif request.method == 'DELETE':
        key = client.key(constants.boats, int(id))
        boat = client.get(key=key)

        if boat == None:
            return (jsonify({"error": "no boat with this id exists"}), 404)

        boat_length = len(boat[constants.loads])

        if (boat_length != 0):
            for one_load in boat[constants.loads]:
                load_id = one_load["id"]
                load_key = client.key(constants.loads, load_id)
                take_load = client.get(key=load_key)
                take_load[constants.carrier] = None
                client.put(take_load)

        client.delete(key)
        return (jsonify(''), 204)

    else:
        return 'Method not recogonized'


@bp.route('/<bid>/loads/<lid>', methods=['PUT','DELETE'])
def add_delete_boatloads(bid, lid):
    if request.method == 'PUT':
        boat_key = client.key(constants.boats, int(bid))
        boat = client.get(key=boat_key)
        load_key = client.key(constants.loads, int(lid))
        load = client.get(key=load_key)

        if boat == None and load == None:
            return (jsonify({"error": "there is no boat or load with this id"}), 404)

        elif boat == None:
            return (jsonify({"error": "there is no boat with this id"}), 404)
        
        elif load == None:
            return (jsonify({"error": "there is no load with this id"}), 404)
            
        elif load[constants.carrier] != None:
            return (jsonify({"error": "this load was already assigned to boat"}), 403)

        if constants.loads in boat.keys():
            for loads in boat[constants.loads]:
                load_id = load.key.id
                boat_id = boat.key.id

                if loads["id"] == load_id:
                    return (jsonify({"error": "this load was already assigned to boat"}), 403)

            load_id = load.key.id
            boat_id = boat.key.id
            boat[constants.loads].append({"id": load_id})   
            load[constants.carrier] = {"id": boat_id, "name": boat["name"]}
            
        else:
            load_id = load.key.id
            boat_id = boat.key.id
            boat[constants.loads] = {"id": load_id}  
            load[constants.carrier] = {"id": boat_id, "name": boat["name"]}

        client.put(boat)
        client.put(load)
        return(jsonify(""), 204)

    if request.method == 'DELETE':
        boat_key = client.key(constants.boats, int(bid))
        boat = client.get(key=boat_key)
        load_key = client.key(constants.loads, int(lid))
        load = client.get(key=load_key)

        if boat == None and load == None:
            return (jsonify({"error": "there is no boat with this id"}), 404)

        elif boat == None:
            return (jsonify({"error": "there is no boat with this id"}), 404)
   
        elif load == None:
            return (jsonify({"error": "there is no load with this id"}), 404)

        elif load[constants.carrier] == None:
            return (jsonify({"error": "this load is not on the boat"}), 404)

        elif load[constants.carrier]["id"] != boat.key.id:
            return (jsonify({"error": "this load is not on the boat"}), 404)

        if constants.loads in boat.keys():
            load_id = load.key.id
            boat[constants.loads].remove({"id": load_id})
            load[constants.carrier] = None
            client.put(boat)
            client.put(load)
        
        return (jsonify(""), 204)


@bp.route('/<id>/loads', methods=['GET'])
def get_boatloads(id):
    boat_key = client.key(constants.boats, int(id))
    boat = client.get(key=boat_key)

    if boat == None:
        return (jsonify({"error": "there is no boat with this id"}), 404)

    load_list  = []

    if len(boat[constants.loads]) != 0:
        for load in boat[constants.loads]:
            load_id = int(load["id"])
            load_key = client.key(constants.loads, load_id)
            find_load = client.get(key=load_key)
            find_load["id"] = find_load.key.id
            find_load["self"] = request.url_root + constants.loads + "/" + str(find_load["id"])
            find_load[constants.carrier]["self"] = request.url_root + constants.boats + "/" + str(find_load[constants.carrier]["id"])
            load_list.append(find_load)

        return (jsonify(load_list), 200)

    else:
        return (jsonify(""), 204)
