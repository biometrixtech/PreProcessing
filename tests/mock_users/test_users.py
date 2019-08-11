domain = "@200.com"

#test env

users = [
    # "tread_a",  # 6fc48b46-23c8-4490-9885-e109ff63c20e
    # "tread_b",  # 4673998d-5206-4275-a048-da5dda6a7342
    # "tread_run",  # bdb8b194-e748-4197-819b-b356f1fb0629
    "run_a"  # 2b4a1792-42c7-460e-9e4c-98627e72cc6f
]

def get_test_users():

    user_list = []

    for u in users:
        email = u + domain
        user_list.append(email)

    return user_list