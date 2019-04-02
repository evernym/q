"""
Some hard-coded identities that we can use for testing scenarios.
Using these values is NOT secure, and is not supposed to be; they
just make it easy to set up a wallet with known state before
running an experiment.
"""

ALICE = {
    'signing_key': 'HKAT8Q11mAD9UdYebqGoMGRTv8qHGU4WaDNVb1aVM6pb',
    'seed': 'f262218dd9357077cf545aa583b892a480f041f197cbf7e3fc5b0b2b8ca6b9fc',
    'did': 'Khu4PoQZ2W9rs4uNGYfb7Z',
    'ver_key': 'BCJkY967hNJLnMRuPie2wsDWBBbrxKc1C7PKjWasPUty'
}

BOB = {
    'signing_key': 'FyuPgaSkAsYiPJcY1YC9MDwU1SNG9eqo51dVQYrzJo2d',
    'seed': 'de97618ccb5af7f59436cdbfbd9c8ff07d42c913862f4d09e438822836393cee',
    'did': '8hmMCToGUEYodxDXm3ScLv',
    'ver_key': '5CW7QqU5MpCg7GXUQTtisknK2ZBcbc1uWJw3duwZrjyf'
}

ALICE_MEDIATOR = {
    'signing_key': 'BpDcXg6SgzH1yRkqkbSPcB5LP1UkinhiAG27b6dKZ3Hk',
    'seed': 'a0ad6da94cdd1c875f7108858d30c92315c6fff2441e9ca7f5917fbfddef10f3',
    'did': 'DsJaFSG2VVRbSjrigHiW9k',
    'ver_key': '81m7Jb7DauJ2LSHEUjosxGBRwoSNzu95EzGwYt4WvnoW'
}

BOB_MEDIATOR = {
    'signing_key': 'F1JRVv6E6co3S9U1dhFzfJsmEPNvMbjKqjTGsH7yiKTu',
    'seed': 'd0175107e272722e801a2e18b67bb60254511bf1d9f52d9c80e23a390050ec48',
    'did': 'Ds4Dv65kUEZMAqzFnH6WME',
    'ver_key': '81dHetC6P89VAYcXXvSFpnUnaYPxdLmoXBUtGJEdVWTz'
}

ALICE_EXTRA_EDGE = {
    'signing_key': '2yH9PvssRJVyyjnC1QeqLNHcwLvZ6qhkaTueWUcc1HH7',
    'seed': '1d467797add159a35c737e4cc2c7634ae226b3cffd249aca4611a161d3663a36',
    'did': None,
    'ver_key': 'HcQaPWxe3Jy8xGeX4z9FoHSRh1MbMbr7ogfhLXKouhUP'
}

BOB_EXTRA_EDGE = {
    'signing_key': 'GejE7zLtd5XmfQHgXFpKpVgHHQyMFeTqEvXPiuVMSfTE',
    'seed': 'e8898a06b887d1859bae7569039b31a4d5574c32e91645d3b3494966311c7b71',
    'did': None,
    'ver_key': '5vdAM3s9R4XoavZ91TdmWgE7FqoryoFPiv8kuUSbq2Fs'
}

ALL = {
    'ALICE': ALICE,
    'BOB': BOB,
    'ALICE_MEDIATOR': ALICE_MEDIATOR,
    'BOB_MEDIATOR': BOB_MEDIATOR,
    'ALICE_EXTRA_EDGE': ALICE_EXTRA_EDGE,
    'BOB_EXTRA_EDGE': BOB_EXTRA_EDGE
}

ALL_NAMES = sorted(ALL.keys())