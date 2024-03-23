import os
import re

def return_valid_unreal_material_name(passed_item):
    """
    Replace any illegal characters for names here.
    """
    s = re.sub("[^0-9a-zA-Z\.]+", "_", passed_item)
    s = s.replace(".", "_")
    return s

def import_list_of_image_maps(passed_list, passed_target_folder):
    """
    Import a list of image maps into Unreal Engine, returning the list of imported texture assets.
    """
    lst_texture2D = []
    data = unreal.AutomatedAssetImportData()
    data.set_editor_property('destination_path', passed_target_folder)
    data.set_editor_property('filenames', passed_list)
    lst_texture2D = unreal.AssetToolsHelpers.get_asset_tools().import_assets_automated(data)
    return lst_texture2D

def return_image_list_by_token(passed_lines, passed_token, passed_texture_path=""):
    """
    Collect list of image files associated with this MTL file.
    """
    lst_images = []
    for line in passed_lines:
        s = line.lstrip()
        ary = s.split(' ')
        if ary[0] == passed_token:
            s = os.path.join(passed_texture_path, ary[1])
            lst_images.append(s)
    return lst_images

def create_new_image_map_opaque_material(passed_asset_path, passed_material_name, passed_diffuse_texture, passed_normal_texture, passed_diffuse_color, passed_spec, passed_rough):
    """
    Create a material and configure its properties.
    """
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    mf = unreal.MaterialFactoryNew()
    mat_closure = asset_tools.create_asset("M_{}".format(passed_material_name), passed_asset_path, unreal.Material, mf)

    # Make a texture diffuse node.
    if passed_diffuse_texture is not None:
        ts_node_diffuse = unreal.MaterialEditingLibrary.create_material_expression(mat_closure, unreal.MaterialExpressionTextureSample, -384, -200)
        ts_node_diffuse.texture = passed_diffuse_texture
        unreal.MaterialEditingLibrary.connect_material_property(ts_node_diffuse, "RGBA", unreal.MaterialProperty.MP_BASE_COLOR)
    else:
        ts_node_diffuse = unreal.MaterialEditingLibrary.create_material_expression(mat_closure, unreal.MaterialExpressionConstant3Vector, -384, -200)
        value = unreal.LinearColor(float(passed_diffuse_color[0]), float(passed_diffuse_color[1]), float(passed_diffuse_color[2]), 1.0)
        ts_node_diffuse.set_editor_property("constant", value)
        unreal.MaterialEditingLibrary.connect_material_property(ts_node_diffuse, "", unreal.MaterialProperty.MP_BASE_COLOR)

    # Roughness and Specular setup omitted for brevity.

    unreal.MaterialEditingLibrary.recompile_material(mat_closure)


