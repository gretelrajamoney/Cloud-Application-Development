from google.cloud import datastore
from flask import Flask, request, jsonify
from requests_oauthlib import OAuth2Session
from google.auth.transport import requests
from google.oauth2 import id_token
import constants


app = Flask(__name__)
client = datastore.Client()

CLIENTID = "116542577120-33o72gknjeet441h6h21h4shvr099nt3.apps.googleusercontent.com"
CLIENTSECRET = "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"
REDIRECTURI = "https://finalproject-rajamong.wl.r.appspot.com/profile"
SCOPE = ['https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile', 'openid']
OAUTH = OAuth2Session(client_id=CLIENTID, redirect_uri=REDIRECTURI, scope=SCOPE)
AUTHORIZATIONURI = "https://accounts.google.com/o/oauth2/auth"
TOKENURI = "https://accounts.google.com/o/oauth2/token"
ACCESSTYPE = "offline"
MESSAGESENT = "select_account"
MAKEREQUEST = requests.Request()



def verifyJWT():
	jwt_token = request.headers.get('Authorization')
	
	if jwt_token:	
		jwt_token = jwt_token.split(" ")[1]
		
		try:
			jwt_sub = id_token.verify_oauth2_token(jwt_token, MAKEREQUEST, CLIENTID)[constants.sub]
		
		except:
			jwt_sub = "not valid"
			return jwt_sub
	else:    		
		jwt_sub = "not found"
		return jwt_sub
	
	return jwt_sub


@app.route('/')
def mainpage():
	authorization_url, state = OAUTH.authorization_url(AUTHORIZATIONURI, access_type = ACCESSTYPE, prompt = MESSAGESENT)
	return '<h1>welcome</h1>\n <p>click <a href=%s>here</a> to sign in or create a new account !!</p>' % authorization_url


@app.route('/profile')
def profilepage():
	token = OAUTH.fetch_token(TOKENURI, authorization_response = request.url, client_secret = CLIENTSECRET)
	id_info = id_token.verify_oauth2_token(token[constants.token], MAKEREQUEST, CLIENTID)

	query = client.query(kind = constants.students)
	query.add_filter(constants.sub, constants.equal, id_info[constants.sub])
	result = list(query.fetch())

	if len(result) == 1:
		return (("<h1>welcome back !!</h1>\n	<p>your jwt is: %s</p>\n	<p>your sub unique id is: %s</p>\n" % (token[constants.token], id_info[constants.sub])), 200)

	if len(result) == 0:
		new_profile = datastore.entity.Entity(key=client.key(constants.students))
		new_profile.update({"email": id_info[constants.email], "sub": id_info[constants.sub]})
		client.put(new_profile)
		return (("<h1>your account has been created</h1>\n	<p>your generated jwt is: %s</p>\n	<p>your generated sub unique id is: %s</p>\n" % (token[constants.token], id_info[constants.sub])), 201)
	

@app.route('/students', methods=["GET"])
def get_students():
	if request.method == "GET":
		if "application/json" in request.accept_mimetypes:
			query = client.query(kind=constants.students)
			all_students = list(query.fetch())

			for e in all_students:
				e[constants.id] = e.key.id
				e[constants.self] = request.url + "/" + str(e[constants.id])

			return (jsonify(all_students), 200)
		
		else:
			result = (jsonify("requested MIME type not supported"))
			result.mimetype = "application/json"
			result.status_code = 406
			return result

	else:
		result = (jsonify("this method is not recognized"))
		result.mimetype = "application/json"
		result.status_code = 405
		return result


@app.route('/students/<student_id>', methods=["GET"])
def get_studentid(student_id):
	if request.method == "GET":
		jwt_sub = verifyJWT()

		if jwt_sub == "not valid":
			return(jsonify("the jwt is wrong"), 401)
		
		if jwt_sub == "not found":
			return (jsonify("there is no jwt"), 401)

		if jwt_sub != student_id:
			return(jsonify("you do not have access to this student"), 404)

		if "application/json" in request.accept_mimetypes:
			query = client.query(kind = constants.students)
			query.add_filter(constants.sub, constants.equal, student_id)
			all_students = list(query.fetch())

			if len(all_students) == 0:
				return(jsonify("this student does not exist"), 404)

			for e in all_students:
				e[constants.id] = e.key.id
				e[constants.self] = request.url

			return (jsonify(all_students), 200)

		else:
			result = (jsonify("requested MIME type not supported"))
			result.mimetype = "application/json"
			result.status_code = 406
			return result
    		
	else:
		result = (jsonify("this method is not recognized"))
		result.mimetype = "application/json"
		result.status_code = 405
		return result


@app.route('/courses', methods=["POST", "GET"])
def post_get_courses():
	if request.method == "POST":
		jwt_sub = verifyJWT()
		
		if jwt_sub == "not valid":
			return (jsonify("the jwt is wrong"), 401)
		
		if jwt_sub == "not found":
			return (jsonify("there is no jwt"), 401)

		if "application/json" in request.accept_mimetypes:
			if "application/json" not in request.content_type:
				result = (jsonify("sent MIME type not supported"))
				result.mimetype = "application/json"
				result.status_code = 406
				return result

			content = request.get_json()

			if len(content) != 6:
				return (jsonify("the course is missing one or more of the required attributes"), 400)
			
			new_course = datastore.entity.Entity(key=client.key("courses"))
			new_course.update({"title": content["title"], "subject": content["subject"], "level": content["level"], "professor": content["professor"], "owner": jwt_sub, "assignments": []})
			client.put(new_course)
			new_course.update({"id": new_course.key.id, "self": request.url + "/" + str(new_course.key.id)})
			
			if "application/json" in request.accept_mimetypes:
				result = jsonify(new_course)
				result.mimetype = "application/json"
				result.status_code = 201

			return result

		else:	
			result = (jsonify("requested MIME type not supported"))
			result.mimetype = "application/json"
			result.status_code = 406
			return result
	
	elif request.method == "GET":
		jwt_sub = verifyJWT()

		if jwt_sub == "not valid":
			return(jsonify("the jwt is wrong"), 401)

		elif jwt_sub == "not found":
			return (jsonify("there is no jwt"), 401)

		if "application/json" in request.accept_mimetypes:
			query = client.query(kind = "courses")
			query.add_filter(constants.owner, constants.equal, jwt_sub)
			q_limit = int(request.args.get("limit", "5"))
			q_offset = int(request.args.get("offset", "0"))
			l_iterator = query.fetch(limit = q_limit, offset = q_offset)
			pages = l_iterator.pages
			all_courses = list(next(pages))
			
			if l_iterator.next_page_token:
				next_offset = q_offset + q_limit
				next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
			
			else:
				next_url = None
			
			for e in all_courses:
				e[constants.id] = e.key.id
				e[constants.self] = request.url_root + "courses/" + str(e[constants.id])

			list_courses = {"courses": all_courses}

			if next_url:
				list_courses["next"] = next_url

			list_courses["collection"] = len(list(query.fetch()))
			
			result = (jsonify(list_courses))
			result.mimetype = "application/json"
			result.status_code = 200
			return result
		
		else:	
			result = (jsonify("requested MIME type not supported"))
			result.mimetype = "application/json"
			result.status_code = 406
			return result
	
	else:
		result = (jsonify("this method is not recognized"))
		result.mimetype = "application/json"
		result.status_code = 405
		return result


@app.route('/courses/<course_id>', methods=["GET", "DELETE", "PUT", "PATCH"])
def get_delete_courses(course_id):
	if request.method == "PUT":
		jwt_sub = verifyJWT()

		if jwt_sub == "not valid":
			return(jsonify("the jwt is wrong"), 401)

		if jwt_sub == "not found":
			return (jsonify("there is no jwt"), 401)

		if "application/json" in request.accept_mimetypes:
			if "application/json" not in request.content_type:
				result = (jsonify("sent MIME type not supported"))
				result.mimetype = "application/json"
				result.status_code = 406
				return result

			course_key = client.key("courses", int(course_id))
			course = client.get(key = course_key)

			if course == None:
				return (jsonify("this course can not be found"), 401)
			
			if course[constants.owner] != jwt_sub:
				return (jsonify("you can not change this course"), 401)
			
			content = request.get_json()

			if len(content) == 0:
				return (jsonify("invalid information"), 400)

			client.put(course)
			course[constants.id] = course.key.id
			course[constants.self] = request.url

			result = (jsonify(course))
			result.mimetype = "application/json"
			result.headers.set('Location', request.base_url)
			result.status_code = 303
			return result
		
		else:	
			result = (jsonify("requested MIME type not supported"))
			result.mimetype = "application/json"
			result.status_code = 406
			return result

	elif request.method == "PATCH":	
		jwt_sub = verifyJWT()
		
		if jwt_sub == "not valid":
			return(jsonify("the jwt is wrong"), 401)

		if jwt_sub == "not found":
			return (jsonify("there is no jwt"), 401)

		if "application/json" in request.accept_mimetypes:	
			if "application/json" not in request.content_type:
				result = (jsonify("sent MIME type not supported"))
				result.mimetype = "application/json"
				result.status_code = 406
				return result

			course_key = client.key("courses", int(course_id))
			course = client.get(key = course_key)

			if course == None:
				return (jsonify("this course can not be found"), 401)
			
			if course[constants.owner] != jwt_sub:
				return (jsonify("you can not access this course"), 401)
			
			content = request.get_json()

			if len(content) == 0:
				return (jsonify("the content is invalid"), 400)

			client.put(course)
			course[constants.id] = course.key.id
			course[constants.self] = request.url
			
			result = (jsonify(course))
			result.mimetype = "application/json"
			result.status_code = 201
			return result
		
		else:	
			result = (jsonify("requested MIME type not supported"))
			result.mimetype = "application/json"
			result.status_code = 406
			return result

	elif request.method == "GET":
		jwt_sub = verifyJWT()

		if jwt_sub == "not valid":
			return(jsonify("the jwt is wrong"), 401)

		if jwt_sub == "not found":
			return (jsonify("there is no jwt"), 401)

		if "application/json" in request.accept_mimetypes:
			course_key = client.key("courses", int(course_id))
			course = client.get(key = course_key)

			if course == None:
				return (jsonify("this course can not be found"), 404)

			if course[constants.owner] != jwt_sub:
				return (jsonify("you can not access this course"), 401)

			course[constants.id] = course.key.id
			course[constants.self] = request.url

			if course[constants.assignments]:
				for homework in course[constants.assignments]:
					hw_key = client.key("assignments", homework[constants.id])
					this_hw = client.get(key = hw_key)
					homework["title"] = this_hw["title"]
					homework["due_date"] = this_hw["due_date"]
					homework["points"] = this_hw["points"]
					homework["finished"] = this_hw["finished"]
					homework["self"] = request.url_root + "assignments/" + str(homework[constants.id])

			result = (jsonify(course))
			result.mimetype = "application/json"
			result.status_code = 200
			return result

		else:	
			result = (jsonify("requested MIME type not supported"))
			result.mimetype = "application/json"
			result.status_code = 406
			return result
	
	elif request.method == "DELETE":
		jwt_sub = verifyJWT()

		if jwt_sub == "not valid":
			return(jsonify("the jwt is wrong"), 401)

		if jwt_sub == "not found":
			return (jsonify("there is no jwt"), 401)

		if "application/json" in request.accept_mimetypes:
			course_key = client.key("courses", int(course_id))
			course = client.get(key = course_key)

			if course == None:
				return (jsonify("this course can not be found"), 401)
			
			if course[constants.owner] != jwt_sub:
				return (jsonify("you are not in this course"), 401)
			
			if course[constants.assignments]:
				for homework in course[constants.assignments]:
					hw_key = client.key("assignments", homework[constants.id])
					this_hw = client.get(key = hw_key)
					this_hw["course_id"] = None
					client.put(this_hw)
			
			client.delete(course)
			result = (jsonify(""))
			result.mimetype = "application/json"
			result.status_code = 204
			return result

		else:	
			result = (jsonify("requested MIME type not supported"))
			result.mimetype = "application/json"
			result.status_code = 406
			return result

	else:	
		result = (jsonify("this method is not recognized"))
		result.mimetype = "application/json"
		result.status_code = 405
		return result


@app.route('/assignments', methods=["POST", "GET"])
def post_get_assignments():
	if request.method == "POST":
		jwt_sub = verifyJWT()

		if jwt_sub == "not valid":
			return(jsonify("the jwt is wrong"), 401)

		if jwt_sub == "not found":
			return (jsonify("there is no jwt"), 401)

		if "application/json" in request.accept_mimetypes:
			if "application/json" not in request.content_type:
				result = (jsonify("sent MIME type not supported"))
				result.mimetype = "application/json"
				result.status_code = 406
				return result

			content = request.get_json()

			if len(content) != 4:
				return (jsonify("the assignment is missing one or more of the required attributes"), 400)
			
			new_assignment = datastore.entity.Entity(key = client.key("assignments"))
			new_assignment.update({"title": content["title"], "course_id": None, "finished": False, "due_date": content["due_date"], "points": content["points"], "owner": jwt_sub})
			client.put(new_assignment)
			new_assignment.update({"id": new_assignment.key.id, "self": request.url + "/" + str(new_assignment.key.id)})
			
			if "application/json" in request.accept_mimetypes:
				result = jsonify(new_assignment)
				result.mimetype = "application/json"
				result.status_code = 201

			return result
		
		else:	
			result = (jsonify("requested MIME type not supported"))
			result.mimetype = "application/json"
			result.status_code = 406
			return result
	
	elif request.method == "GET":
		jwt_sub = verifyJWT()

		if jwt_sub == "not valid":
			return(jsonify("the jwt is wrong"), 401)

		if jwt_sub == "not found":
			return (jsonify("there is no jwt"), 401)

		if "application/json" in request.accept_mimetypes:
			query = client.query(kind = "assignments")
			query.add_filter(constants.owner, constants.equal, jwt_sub)
			q_limit = int(request.args.get("limit", "5"))
			q_offset = int(request.args.get("offset", "0"))
			l_iterator = query.fetch(limit= q_limit, offset= q_offset)
			pages = l_iterator.pages
			all_assignments = list(next(pages))

			if l_iterator.next_page_token:
				next_offset = q_offset + q_limit
				next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
			
			else:
				next_url = None

			for e in all_assignments:	
				e[constants.id] = e.key.id
				e[constants.self] = request.url_root + "assignments/" + str(e.key.id)
			
			total_list = {"assignments": all_assignments}
			
			if next_url:
				total_list["next"] = next_url
			
			total_list["collection"] = len(list(query.fetch()))
			result = (jsonify(total_list))
			result.mimetype = "application/json"
			result.status_code = 200
			return result

		else:	
			result = (jsonify("requested MIME type not supported"))
			result.mimetype = "application/json"
			result.status_code = 406
			return result

	else:
		result = (jsonify("this method is not recognized"))
		result.mimetype = "application/json"
		result.status_code = 405
		return result


@app.route('/assignments/<assignment_id>', methods=["GET", "PATCH", "DELETE", "PUT"])
def get_delete_put_patch_assignments(assignment_id):
	if request.method == "PUT":
		jwt_sub = verifyJWT()

		if jwt_sub == "not valid":
			return(jsonify("the jwt is wrong"), 401)

		if jwt_sub == "not found":
			return (jsonify("there is no jwt"), 401)

		if "application/json" in request.accept_mimetypes:
			if "application/json" not in request.content_type:
				result = (jsonify("sent MIME type not supported"))
				result.mimetype = "application/json"
				result.status_code = 406
				return result

			assignment_key = client.key("assignments", int(assignment_id))
			assignment = client.get(key = assignment_key)

			if assignment == None:
				return (jsonify("this assignment can not be found"), 404)
			
			if assignment[constants.owner] != jwt_sub:
				return (jsonify("you do not have this assignment"), 401)
			
			content = request.get_json()

			if len(content) != 4:
				return (jsonify("the content is invalid"), 400)

			for temp in content:
				if type(content.get(temp)) == bool and temp == "finished":
					if assignment["course_id"]:
						course_key = client.key("courses", int(assignment["course_id"]))
						course = client.get(key = course_key)
						
						if assignment["finished"] == False and content.get(temp) == True:
								course["assignments"].remove({'id': assignment.key.id, 'owner': jwt_sub, 'course_id': str(course.key.id)})
						
						elif assignment["finished"] == True and content.get(temp) == False:
								course["assignments"].append({'id': assignment.key.id, 'owner': jwt_sub, 'course_id': str(course.key.id)})

						client.put(course)

					assignment["finished"] = content.get(temp)

				elif type(content.get(temp)) == str and temp == "title":
					assignment["title"] = content.get(temp)

				elif type(content.get(temp)) == str and temp == "due_date":
					assignment["due_date"] = content.get(temp)

				elif type(content.get(temp)) == int and temp == "points":
					assignment["points"] = content.get(temp)

				else:
					return (jsonify("this content is invalid"), 400)

			client.put(assignment)
			assignment[constants.id] = assignment.key.id
			assignment[constants.self] = request.url

			result = (jsonify(assignment))
			result.mimetype = "application/json"
			result.status_code = 201
			return result

		else:	
			result = (jsonify("requested MIME type not supported"))
			result.mimetype = "application/json"
			result.status_code = 406
			return result

	elif request.method == "GET":
		jwt_sub = verifyJWT()

		if jwt_sub == "not valid":
			return(jsonify("the jwt is wrong"), 401)

		if jwt_sub == "not found":
			return (jsonify("there is no jwt"), 401)

		if "application/json" in request.accept_mimetypes:
			assignment_key = client.key("assignments", int(assignment_id))
			assignment = client.get(key = assignment_key)

			if assignment == None:
				return (jsonify("this assignment can not be found"), 404)

			if assignment[constants.owner] != jwt_sub:
				return (jsonify("you do not have this assignment"), 401)

			assignment[constants.id] = assignment.key.id
			assignment[constants.self] = request.url

			result = (jsonify(assignment))
			result.mimetype = "application/json"
			result.status_code = 200
			return result
		
		else:	
			result = (jsonify("requested MIME type not supported"))
			result.mimetype = "application/json"
			result.status_code = 406
			return result

	elif request.method == "PATCH":
		jwt_sub = verifyJWT()

		if jwt_sub == "not valid":
			return(jsonify("the jwt is wrong"), 401)

		if jwt_sub == "not found":
			return (jsonify("there is no jwt"), 401)

		if "application/json" in request.accept_mimetypes:	
			if "application/json" not in request.content_type:
				result = (jsonify("sent MIME type not supported"))
				result.mimetype = "application/json"
				result.status_code = 406
				return result

			assignment_key = client.key("assignments", int(assignment_id))
			assignment = client.get(key = assignment_key)

			if assignment == None:
				return (jsonify("this assignment can not be found"), 404)
			
			if assignment[constants.owner] != jwt_sub:
				return (jsonify("you do not have this assignment"), 401)
			
			content = request.get_json()

			if len(content) == 0:
				return (jsonify("the content is invalid"), 400)

			for temp in content:
				if type(content.get(temp)) == bool and temp == "finished":
					if assignment["course_id"]:
						course_key = client.key("courses", int(assignment["course_id"]))
						course = client.get(key = course_key)
						
						if assignment["finished"] == False and content.get(temp) == True:
								course["assignments"].remove({'id': assignment.key.id, 'owner': jwt_sub, 'course_id': str(assignment.key.id)})
						
						elif assignment["finished"] == True and content.get(temp) == False:
								course["assignments"].append({'id': assignment.key.id, 'owner': jwt_sub, 'course_id': str(assignment.key.id)})

						client.put(course)

					assignment["finished"] = content.get(temp)

				elif type(content.get(temp)) == str and temp == "title":
					assignment["title"] = content.get(temp)

				elif type(content.get(temp)) == str and temp == "due_date":
					assignment["due_date"] = content.get(temp)

				elif type(content.get(temp)) == int and temp == "points":
					assignment["points"] = content.get(temp)

				else:
					return (jsonify("this content is invalid"), 400)

			client.put(assignment)
			assignment[constants.id] = assignment.key.id
			assignment[constants.self] = request.url

			result = (jsonify(assignment))
			result.mimetype = "application/json"
			result.status_code = 201
			return result
		
		else:	
			result = (jsonify("requested MIME type not supported"))
			result.mimetype = "application/json"
			result.status_code = 406
			return result

	elif request.method == "DELETE":
		jwt_sub = verifyJWT()

		if jwt_sub == "not valid":
			return(jsonify("the jwt is wrong"), 401)

		if jwt_sub == "not found":
			return (jsonify("there is no jwt"), 401)

		if "application/json" in request.accept_mimetypes:		
			assignment_key = client.key("assignments", int(assignment_id))
			assignment = client.get(key = assignment_key)

			if assignment == None:
				return (jsonify("this assignment can not be found"), 404)
			
			if assignment[constants.owner] != jwt_sub:
				return (jsonify("you do not have this assignment"), 401)
			
			if assignment["course_id"]:
				course_key = client.key("courses", int(assignment["course_id"]))
				course = client.get(key = course_key)
				client.put(course)
			
			client.delete(assignment)
			result = (jsonify(""))
			result.mimetype = "application/json"
			result.status_code = 204
			return result

		else:	
			result = (jsonify("requested MIME type not supported"))
			result.mimetype = "application/json"
			result.status_code = 406
			return result

	else:
		result = (jsonify("this method is not recognized"))
		result.mimetype = "application/json"
		result.status_code = 405
		return result


@app.route('/courses/<course_id>/assignments', methods=["GET", "POST"])
def post_get_courses_assignments(course_id):
	if request.method == "GET":
		jwt_sub = verifyJWT()

		if jwt_sub == "not valid":
			return(jsonify("the jwt is wrong"), 401)

		if jwt_sub == "not found":
			return (jsonify("there is no jwt"), 401)

		if "application/json" in request.accept_mimetypes:
			course_key = client.key("courses", int(course_id))
			selected_course = client.get(key = course_key)

			if selected_course == None:
				return (jsonify("this course can not be found"), 401)

			if selected_course[constants.owner] != jwt_sub:
				return (jsonify("you are not in this course"), 401)

			query = client.query(kind = constants.assignments)
			query.add_filter("course_id", constants.equal, course_id)
			query.add_filter("finished", constants.equal, False)
			assignments = list(query.fetch())

			for e in assignments:
				e[constants.id] = e.key.id
				e[constants.self] = request.url_root + "assignments/" + str(e[constants.id])

			all_courses = {"assignments": assignments}
			result = (jsonify(all_courses))
			result.mimetype = "application/json"
			result.status_code = 200
			return result

		else:	
			result = (jsonify("requested MIME type not supported"))
			result.mimetype = "application/json"
			result.status_code = 406
			return result
		
	elif request.method == "POST":
		jwt_sub = verifyJWT()

		if jwt_sub == "not valid":
			return(jsonify("the jwt is wrong"), 401)

		if jwt_sub == "not found":
			return (jsonify("there is no jwt"), 401)

		if "application/json" in request.accept_mimetypes:
			if "application/json" not in request.content_type:
				result = (jsonify("sent MIME type not supported"))
				result.mimetype = "application/json"
				result.status_code = 406
				return result

			course_key = client.key("courses", int(course_id))
			course = client.get(key = course_key)

			if course == None:
				return (jsonify("this course can not be found"), 401)

			if course[constants.owner] != jwt_sub:
				return (jsonify("you are not in this course"), 401)

			content = request.get_json()

			if len(content) != 5:
				return (jsonify("one or more of the required attributes is missing"), 400)
			
			new_assignment = datastore.entity.Entity(key = client.key(constants.assignments))
			new_assignment.update({"title": content["title"], "course_id": course_id, "finished": False, "due_date": content["due_date"], "points": content["points"], "owner": jwt_sub})
			client.put(new_assignment)
			course[constants.assignments].append({"id": new_assignment.key.id, "owner": jwt_sub, "course_id": course_id})
			client.put(course)

			course.update({"id": course.key.id, "self": request.url_root + "courses/" + str(course.key.id)})
			
			for assignment in course[constants.assignments]:
				assignment[constants.self] = request.url_root + "assignments/" + str(assignment[constants.id])
			
			if "application/json" in request.accept_mimetypes:
				result = jsonify(course)
				result.mimetype = "application/json"
				result.status_code = 201

			return result

		else:	
			result = (jsonify("requested MIME type not supported"))
			result.mimetype = "application/json"
			result.status_code = 406
			return result

	else:	
		result = (jsonify("this method is not recognized"))
		result.mimetype = "application/json"
		result.status_code = 405
		return result


@app.route('/courses/<course_id>/assignments/<assignment_id>', methods=["PUT", "DELETE"])
def put_course_assignment(course_id, assignment_id):
	if request.method == "PUT":
		jwt_sub = verifyJWT()

		if jwt_sub == "not valid":
			return(jsonify("the jwt is wrong"), 401)

		if jwt_sub == "not found":
			return (jsonify("there is no jwt"), 401)

		course_key = client.key("courses", int(course_id))
		course = client.get(key = course_key)

		assignment_key = client.key("assignments", int(assignment_id))
		assignment = client.get(key = assignment_key)

		if course == None and assignment == None:
			return (jsonify("neither the course nor the assignment can be found"), 404)
			
		if course == None:
			return (jsonify("this course can not be found"), 404)

		if assignment == None:
			return (jsonify("this assignment can not be found"), 404)

		if course[constants.owner] != jwt_sub:
			return (jsonify("you are not in this course"), 401)
			
		if assignment[constants.owner] != jwt_sub:
			return (jsonify("you do not have this assignment"), 401)

		for this_hw in course[constants.assignments]:
			if this_hw[constants.id] == int(assignment_id):
				return (jsonify("this assignment is already in the course"), 403)
			
		course["assignments"].append({"id": assignment.key.id, "owner": assignment["owner"], "course_id": course_id})
		client.put(course)

		assignment["course_id"] = course_id
		client.put(assignment)

		result = (jsonify(""))
		result.mimetype = 'application/json'
		result.status_code = 204
		return result

	elif request.method == "DELETE":
		jwt_sub = verifyJWT()

		if jwt_sub == "not valid":
				return(jsonify("the jwt is wrong"), 401)
		
		if jwt_sub == "not found":
			return (jsonify("there is no jwt"), 401)

		if "application/json" in request.accept_mimetypes:	
			course_key = client.key("courses", int(course_id))
			course = client.get(key = course_key)
			
			assignment_key = client.key("assignments", int(assignment_id))
			assignment = client.get(key = assignment_key)

			if course == None and assignment == None:		
				return (jsonify("neither the course nor the assignment can be found"), 404)
			
			if course == None:
				return (jsonify("this course can not be found"), 404)
			
			if assignment == None:
				return (jsonify("this assignment can not be found"), 404)
			
			if course[constants.owner] != jwt_sub:			
				return (jsonify("you are not in this course"), 401)

			elif assignment[constants.owner] != jwt_sub:
				return (jsonify("you do not have this assignment"), 401)
			
			if assignment["course_id"]:
				course_key = client.key("courses", int(assignment["course_id"]))
				course = client.get(key = course_key)
				
				if assignment["finished"] == False:
						course["assignments"].remove({"id": assignment.key.id, "owner": jwt_sub, "course_id": str(course.key.id)})

				client.put(course)
			
			client.delete(assignment)
			result = (jsonify(""))
			result.mimetype = "application/json"
			result.status_code = 204
			return result

		else:	
			result = (jsonify("requested MIME type not supported"))
			result.mimetype = "application/json"
			result.status_code = 406
			return result

	else:
		result = (jsonify("this method is not recognized"))
		result.mimetype = "application/json"
		result.status_code = 405
		return result


if __name__ == '__main__':
    	app.run(host='127.0.0.1', port=8080, debug=True)