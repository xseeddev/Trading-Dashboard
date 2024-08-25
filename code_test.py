import json
from login import angel_login
from login import login

#Angel Login Test
def Login_test():
    with open("user_data.json", "r") as f:
        user_data = json.load(f)

    for user in user_data:
        #logincount, client, user_id, password, api_key, secret_key
        # status, obj = login(3,user['user_id'],user['user_id'],user['password'],user['api_key'],user['secret_key'])
        status, obj = angel_login(user)
        print("DEB:",status)
        break

if __name__ == "__main__":
    Login_test()