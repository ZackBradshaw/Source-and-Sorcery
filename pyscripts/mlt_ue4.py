import unreal
import os
import re
import platform

passedItem = "./multiverse.mtl"

def returnValidUnrealMaterialName(passedItem):
    s = re.sub("[^0-9a-zA-Z\.]+", "_", passedItem)
    s = s.replace(".", "_")
    unreal.log_debug(f"Valid Unreal Material Name: {s}")
    return s

def importListOfImageMaps(passedList, passedTargetFolder):
    lst_texture2D = []
    data = unreal.AutomatedAssetImportData()
    data.set_editor_property('destination_path', passedTargetFolder)
    data.set_editor_property('filenames', passedList)
    lst_texture2D = unreal.AssetToolsHelpers.get_asset_tools().import_assets_automated(data)
    unreal.log_debug(f"Imported {len(lst_texture2D)} textures to {passedTargetFolder}")
    return lst_texture2D

def returnImageListByToken(passedLines, passedToken, passedTexturePath=""):
    lst_images = []
    for line in passedLines:
        s = line.lstrip()
        ary = s.split(' ')
        if ary[0] == passedToken:
            s = os.path.join(passedTexturePath, ary[1])
            lst_images.append(s)
    unreal.log_debug(f"Found {len(lst_images)} images for token {passedToken}")
    return lst_images

def createNewImageMapOpaqueMaterial(passedAssetPath, passedMaterialName, passedDiffuseTexture, passedNormalTexture, passedDiffuseColor, passedSpec, passedRough):
    assetTools = unreal.AssetToolsHelpers.get_asset_tools()
    mf = unreal.MaterialFactoryNew()
    mat_closure = assetTools.create_asset("M_%s" % passedMaterialName, passedAssetPath, unreal.Material, mf)

    if passedDiffuseTexture is not None:
        ts_node_diffuse = unreal.MaterialEditingLibrary.create_material_expression(mat_closure, unreal.MaterialExpressionTextureSample, -384, -200)
        ts_node_diffuse.texture = passedDiffuseTexture
        unreal.MaterialEditingLibrary.connect_material_property(ts_node_diffuse, "RGBA", unreal.MaterialProperty.MP_BASE_COLOR)
    else:
        ts_node_diffuse = unreal.MaterialEditingLibrary.create_material_expression(mat_closure, unreal.MaterialExpressionConstant3Vector, -384, -200)
        value = unreal.LinearColor(float(passedDiffuseColor[0]), float(passedDiffuseColor[1]), float(passedDiffuseColor[2]), 1.0)
        ts_node_diffuse.set_editor_property("constant", value)
        unreal.MaterialEditingLibrary.connect_material_property(ts_node_diffuse, "", unreal.MaterialProperty.MP_BASE_COLOR)

    ts_node_roughness = unreal.MaterialEditingLibrary.create_material_expression(mat_closure, unreal.MaterialExpressionConstant, -125, 150)
    ts_node_roughness.set_editor_property('R', passedRough)
    unreal.MaterialEditingLibrary.connect_material_property(ts_node_roughness, "", unreal.MaterialProperty.MP_ROUGHNESS)

    ts_node_specular = unreal.MaterialEditingLibrary.create_material_expression(mat_closure, unreal.MaterialExpressionConstant, -125, 50)
    ts_node_specular.set_editor_property('R', passedSpec)
    unreal.MaterialEditingLibrary.connect_material_property(ts_node_specular, "", unreal.MaterialProperty.MP_SPECULAR)

    unreal.MaterialEditingLibrary.recompile_material(mat_closure)
    unreal.log_debug(f"Created new image map opaque material: {passedMaterialName}")

def process_material_file(file_name, asset_path, material_path, texture_path):
    with open(file_name, 'r') as f:
        lines = f.read().splitlines()

    lst_diffuse_maps = list(dict.fromkeys(returnImageListByToken(lines, "map_Kd", file_path)))
    lst_textures_diffuse = importListOfImageMaps(lst_diffuse_maps, texture_path)
    lst_normal_maps = list(dict.fromkeys(returnImageListByToken(lines, "map_Kn", file_path)))
    lst_textures_normal = importListOfImageMaps(lst_normal_maps, texture_path)

    mat_name = ""
    material_pending = False
    diffuse_color = [0, 0, 0]
    specular_color = [0, 0, 0]
    map_diffuse = ""
    map_normal = ""

    for line in lines:
        s = line.lstrip()
        ary = s.split(' ')
        
        if ary[0] == 'newmtl':
            if material_pending:
                generate_material(material_path, mat_name, map_diffuse, diffuse_color, lst_diffuse_maps, lst_textures_diffuse)
            mat_name = ary[1]
            material_pending = True
        
        if ary[0] == 'Ks':
            specular_color = [float(ary[1]), float(ary[2]), float(ary[3])]
        elif ary[0] == 'Kd':
            diffuse_color = [float(ary[1]), float(ary[2]), float(ary[3])]
        elif ary[0] == 'map_Kd':
            map_diffuse = ary[1]
        elif ary[0] == 'map_Kn':
            map_normal = ary[1]

    if material_pending:
        generate_material(material_path, mat_name, map_diffuse, diffuse_color, lst_diffuse_maps, lst_textures_diffuse)
        unreal.log_debug("MTL file processed successfully.")

def generate_material(material_path, mat_name, map_diffuse, diffuse_color, lst_diffuse_maps, lst_textures_diffuse):
    shader_name = returnValidUnrealMaterialName("M_%s" % mat_name)
    unreal.log_debug(f"Generating material: {shader_name}")

    texture_diffuse = None
    if map_diffuse:
        for i, entry in enumerate(lst_diffuse_maps):
            if entry.endswith(map_diffuse):
                texture_diffuse = lst_textures_diffuse[i]
                break

    createNewImageMapOpaqueMaterial(material_path, shader_name, texture_diffuse, None, diffuse_color, 0.92, 0.26)
    unreal.log_debug(f"Material {shader_name} generated successfully.")
