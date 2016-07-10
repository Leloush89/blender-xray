from utils import defs
from . import skl

__all__ = [
    'SCHEMA',
]

SCHEMA = defs.Simple({
    0: ('header', (
        ('version', 'I'),
        ('guid', '16B'),
        ('graphguid', '16B'),
        ('spawncount', 'I'),
        ('levelcount', 'I'),
    )),
    1: ('spawns', {
        0: ('header', (
            ('vertexcount', 'I'),
        )),
        1: ('chunks', {
            None: (None, {
                0: ('id', 'H'),
                1: ('netpacket', {
                    0: ('spawn', (
                        ('length', 'H'),
                        ('type', 'H'),
                        ('name', 'S'),
                        ('name_replace', 'S'),
                        ('?zero', 'B'),
                        ('rp', 'B'),
                        ('position', 'fff'),
                        ('angle', 'fff'),
                        ('respawn_time', 'H'),
                        ('id', 'H'),
                        ('id_parent', 'H'),
                        ('id_phantom', 'H'),
                        ('flags', 'H'),
                        ('version', 'H'),
                        ('game_type', 'H'),
                        ('script_version', 'H'),
                        ('client_data', ['H', 'B']),
                        ('tspawn_id', 'H'),
                        ('state', (
                            ('graph_id', 'H'),
                            ('?zero', 'H'),
                            ('distance', 'f'),
                            ('direct_control', 'I'),
                            ('tnode_id', 'I'),
                            ('flags', 'I'),
                            ('ini_string', 'S'),
                            ('story_id', 'I'),
                            ('spawn_story_id', 'I'),

                            # ('visual_name', 'S'),
                            # ('flags', 'B'),
                            #
                            # ('team', 'B'),
                            # ('squad', 'B'),
                            # ('group', 'B'),
                            # ('health', 'f'),
                            # ('x', 'I'),
                        )),
                    ))
                })
            }),
        }),
    }),
    2: ('level', ['I', (
        ('point', 'fff'),
        ('node_id', 'I'),
        ('distance', 'f'),
    )]),
    3: ('patrol', {
        0: ('size', 'I'),
        1: ('chunks', {
            None: (None, {
                0: ('key', 'S'),
                1: ('val', {}),
            })
        })
    }),
})
