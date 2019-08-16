domain = "@200.com"

#test env

users = [
    # "tread_a",  # 6fc48b46-23c8-4490-9885-e109ff63c20e
    # "tread_b",  # 4673998d-5206-4275-a048-da5dda6a7342
    # "tread_run",  # bdb8b194-e748-4197-819b-b356f1fb0629
    # "run_a",  # 2b4a1792-42c7-460e-9e4c-98627e72cc6f
    # "sym",  # 7fd0c1d4-61ac-4ce5-9621-16d69501b211
    # "half_sym",  # 7cf2f832-a043-468c-8f61-13d07765d2a2
    # "run_a_2", #5c695e58-0aba-4eec-9af1-fa93970d3132
    # "sym_2" #aa1534d0-4abd-41c0-9b84-4e414b3d86d4
    # "long_3s",  # 928f64b5-a761-4278-8724-95a908499fae
    # "run_a_3",  # 9e90e3ef-c6e0-4e2d-a430-a52f1e61a962
    # "sym_3",  # 34b47309-7ad5-4222-b865-0f825680541e
    "tread_a_2",  # 441a296a-6d37-4de3-ba04-bd725da05613
    # "tread_b_2",  # e72bfb85-9c66-4cbe-8a77-20e5eda0a793
    # "tread_run_2",  # 4c8792b2-d5e2-475b-b55d-c16e70dc47aa
    # "long_3s_2",  # 06a112b3-b07f-4da7-a6bb-16558c5345ea
    # "half_sym_2",  # d81af04a-385e-4a43-ad95-63222549ecc4
    #"run_a_mazen", #110e14e6-8630-48e8-b75d-0caad447d661
    #"tread_run_2_mazen", #23e93c04-c7cc-40b3-8e34-e43a9cab286a
]

def get_test_users():

    user_list = []

    for u in users:
        email = u + domain
        user_list.append(email)

    return user_list