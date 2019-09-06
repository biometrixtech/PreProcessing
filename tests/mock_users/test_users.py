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
    # "tread_a_2",  # 441a296a-6d37-4de3-ba04-bd725da05613
    # "tread_b_2",  # e72bfb85-9c66-4cbe-8a77-20e5eda0a793
    # "tread_run_2",  # 4c8792b2-d5e2-475b-b55d-c16e70dc47aa
    # "long_3s_2",  # 06a112b3-b07f-4da7-a6bb-16558c5345ea
    # "half_sym_2",  # d81af04a-385e-4a43-ad95-63222549ecc4
    # "run_a_mazen", #110e14e6-8630-48e8-b75d-0caad447d661
    # "tread_run_2_mazen", #23e93c04-c7cc-40b3-8e34-e43a9cab286a
    #"tread_b_mazen",  # 1569f9bb-6de3-49a9-913c-f69d7d763d25
    #("nc_long@200.com",  '7bb3e792-41ff-43cb-861e-87cf2bdeeadf'),
    ("nc_sore_tread@200.com",  '917e94bc-3f56-4519-8d25-ae54878748f2'),
    # ("ts_tread@200.com", '18ad5cde-92a8-4cd4-8295-71a91c7d3aac'),
    # ("ts_pain_long@200.com", 'e602620d-2040-4ecc-87cc-f392d9db5eab'),
    # ("two_pain_tread@200.com",  '25c38e39-357a-456d-84b7-61547364a2ba'),
    # ("full_fte_long@200.com", '024a6807-eef6-4556-b3b8-1c8639dd1758'),
    # ("full_fte_tread@200.com", '33293741-bf30-479e-83e9-bc6b3a1cb7c2'),
    # ("nc_long_2@200.com",  '8f6ff382-9314-43d2-9bb5-54bd8416a682'),
    # ("nc_sore_tread_2@200.com",  '3f4bd8a2-c76b-4296-8c75-7302c31468c2'),
    # ("ts_pain_long_2@200.com",  '5dd7a148-1c0e-4ddf-a1b1-020a99347069'),
    # ("ts_tread_2@200.com",  '93b7a075-8168-4fad-961f-cfebdee392fc'),
    # ("two_pain_tread_2@200.com",  '84a5e6fd-19f2-44ed-8bbd-ed2c03769ecf'),
    # ("full_fte_long_2@200.com",  '24882bdf-69df-4043-b832-74d6c1f7052c'),
    # ("full_fte_tread_2@200.com",  '703b5309-78cd-46b1-82ec-45e86b6d71de'),
]

def get_test_users():

    user_list = []

    for u in users:
        #u[0] = u[0] + domain
        user_list.append(u)

    return user_list