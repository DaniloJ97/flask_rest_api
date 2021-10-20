def get_response_dict(user,message,status_code):
    user_dict_field = None
    if not user:
        user_dict_field = {}
    elif type(user) == list:
        user_dict_field = user
    else:
        user_dict_field = user.get_user_dict()

    response_dict = {
        "message":message,
        "status code": status_code,
        "user(s)": user_dict_field
    }

    return response_dict

def update_user_fields(user,json):
    for key in json:
        user.update_field(key,json.get(key, None))