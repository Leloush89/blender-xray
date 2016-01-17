import bpy
import os.path


def get_preferences():
    return bpy.context.user_preferences.addons['io_scene_xray'].preferences


class PluginPreferences(bpy.types.AddonPreferences):
    bl_idname = 'io_scene_xray'

    def xr_set(self, prop_name):
        value = getattr(self, prop_name)
        print(0, prop_name, value)
        if not value:
            if prop_name == 'textures_folder':
                self.gamedata_folder
            return
        path = os.path.abspath(os.path.join(value, os.pardir))
        for pn, ps in {
            'textures_folder': 'textures',
            'gamemtl_file': 'gamemtl.xr',
            'cshader_file': 'shaders.xr',
            'eshader_file': 'shaders_xrlc.xr'
        }.items():
            print(1, pn, ps)
            if pn == prop_name:
                continue
            pv = getattr(self, pn)
            print(2, pv)
            if pv:
                continue
            pv = os.path.join(path, ps)
            print(3, pv)
            if os.path.exists(pv):
                setattr(self, pn, pv)

    gamedata_folder = bpy.props.StringProperty(name='gamedata', description='The path to the \'gamedata\' directory', subtype='DIR_PATH')
    textures_folder = bpy.props.StringProperty(
            name='Textures Folder',
            description='The path to the \'gamedata/textures\' directory',
            update=lambda self, context: self.xr_set('textures_folder'),
            subtype='DIR_PATH')
    gamemtl_file = bpy.props.StringProperty(
            name='GameMtl File',
            description='The path to the \'gamemtl.xr\' file',
            update=lambda self, context: self.xr_set('gamemtl_file'),
            subtype='FILE_PATH')
    eshader_file = bpy.props.StringProperty(name='EShader File', description='The path to the \'shaders.xr\' file', subtype='FILE_PATH')
    cshader_file = bpy.props.StringProperty(name='CShader File', description='The path to the \'shaders_xrlc.xr\' file', subtype='FILE_PATH')
    expert_mode = bpy.props.BoolProperty(name='Expert Mode', description='Show additional properties/controls')

    def get_textures_folder(self):
        result = self.textures_folder;
        if not result and self.gamedata_folder:
            import os.path
            result = os.path.join(self.gamedata_folder, 'textures')
        return result

    def draw(self, context):
        layout = self.layout
        if not self.textures_folder and self.gamedata_folder:
            tf = self.get_textures_folder()
            print('x', tf)
            self.textures_folder = tf
        layout.prop(self, 'textures_folder', expand=True)
        layout.prop(self, 'gamemtl_file', emboss=True)
        layout.prop(self, 'eshader_file')
        layout.prop(self, 'cshader_file')
        lr = layout.row()
        lr.label(text='Expert Mode:')
        lr.prop(self, 'expert_mode', text='')
