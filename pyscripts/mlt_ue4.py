"""
MTL File Reader
(c) 2020 Atom
Reads the entries of an .MTL file and generates a material linked to the image maps.
Date: 10/01/20

This module is designed to work within the Unreal Engine Python environment to automate the process of reading .MTL files,
extracting material properties, and creating corresponding materials in Unreal Engine with linked image maps.
"""

import unreal
import os
import re
import platform

def returnValidUnrealMaterialName(passedItem):
    """
    Replaces any illegal characters in names for Unreal Engine compatibility.
    
    Args:
        passedItem (str): The original material name from the .MTL file.
        
    Returns:
        str: A valid Unreal Engine material name.
    """
    # Replace any characters not allowed in Unreal names with "_"
    s = re.sub("[^0-9a-zA-Z\.]+", "_", passedItem)
    s = s.replace(".", "_")
    return s

def importListOfImageMaps(passedList, passedTargetFolder):
    """
    Imports a list of image maps into Unreal Engine.
    
    Args:
        passedList (list): A list of file paths to the image maps.
        passedTargetFolder (str): The target folder in Unreal Engine to import the images into.
        
    Returns:
        list: A list of imported Texture2D objects.
    """
    lst_texture2D = []
    data = unreal.AutomatedAssetImportData()
    data.set_editor_property('destination_path', passedTargetFolder)  # Unreal game folder.
    data.set_editor_property('filenames', passedList)
    lst_texture2D = unreal.AssetToolsHelpers.get_asset_tools().import_assets_automated(data)
    return lst_texture2D

def returnImageListByToken(passedLines, passedToken, passedTexturePath=""):
    """
    Collects a list of image files associated with a specific token in the .MTL file.
    
    Args:
        passedLines (list): The lines of the .MTL file.
        passedToken (str): The token to search for (e.g., "map_Kd" for diffuse maps).
        passedTexturePath (str, optional): The path to prepend to the image filenames. Defaults to "".
        
    Returns:
        list: A list of image file paths.
    """
    lst_images = []
    for line in passedLines:
        s = line.lstrip()  # Remove leading TAB or spacing if present.
        ary = s.split(' ')  # Split by spaces.
        if ary[0] == passedToken:
            s = os.path.join(passedTexturePath, ary[1])
            lst_images.append(s)
    return lst_images

def createNewImageMapOpaqueMaterial(passedAssetPath, passedMaterialName, passedDiffuseTexture, passedNormalTexture, passedDiffuseColor, passedSpec, passedRough):
    """
    Creates a new opaque material in Unreal Engine with the specified properties.
    
    Args:
        passedAssetPath (str): The path in Unreal Engine to create the material.
        passedMaterialName (str): The name of the material.
        passedDiffuseTexture (Texture2D): The diffuse texture.
        passedNormalTexture (Texture2D): The normal texture.
        passedDiffuseColor (list): The diffuse color as [R, G, B].
        passedSpec (float): The specular value.
        passedRough (float): The roughness value.
    """
    assetTools = unreal.AssetToolsHelpers.get_asset_tools()
    mf = unreal.MaterialFactoryNew()
    mat_closure = assetTools.create_asset("M_%s" % passedMaterialName, passedAssetPath, unreal.Material, mf)

    # Make a texture diffuse node.
    if passedDiffuseTexture is not None:
        # Add an image node.
        ts_node_diffuse = unreal.MaterialEditingLibrary.create_material_expression(mat_closure, unreal.MaterialExpressionTextureSample, -384, -200)
        ts_node_diffuse.texture = passedDiffuseTexture
        unreal.MaterialEditingLibrary.connect_material_property(ts_node_diffuse, "RGBA", unreal.MaterialProperty.MP_BASE_COLOR)
    else:
        # Add a color constant node.
        ts_node_diffuse = unreal.MaterialEditingLibrary.create_material_expression(mat_closure, unreal.MaterialExpressionConstant3Vector, -384, -200)
        value = unreal.LinearColor(float(passedDiffuseColor[0]), float(passedDiffuseColor[1]), float(passedDiffuseColor[2]), 1.0)
        ts_node_diffuse.set_editor_property("constant", value)
        unreal.MaterialEditingLibrary.connect_material_property(ts_node_diffuse, "", unreal.MaterialProperty.MP_BASE_COLOR)

    # Make a constant float node for roughness.
    ts_node_roughness = unreal.MaterialEditingLibrary.create_material_expression(mat_closure, unreal.MaterialExpressionConstant, -125, 150)
    ts_node_roughness.set_editor_property('R', passedRough)
    unreal.MaterialEditingLibrary.connect_material_property(ts_node_roughness, "", unreal.MaterialProperty.MP_ROUGHNESS)

    # Make a constant float node for specular.
    ts_node_specular = unreal.MaterialEditingLibrary.create_material_expression(mat_closure, unreal.MaterialExpressionConstant, -125, 50)
    ts_node_specular.set_editor_property('R', passedSpec)
    unreal.MaterialEditingLibrary.connect_material_property(ts_node_specular, "", unreal.MaterialProperty.MP_SPECULAR)

    unreal.MaterialEditingLibrary.recompile_material(mat_closure)
import unreal

def process_material_file(file_name, asset_path, material_path, texture_path):
    """
    Processes a .MTL file to generate materials in Unreal Engine 5 based on the file's specifications.
    
    Args:
        file_name (str): The path to the .MTL file.
        asset_path (str): The base path in Unreal Engine where assets will be stored.
        material_path (str): The path in Unreal Engine where materials will be created.
        texture_path (str): The path in Unreal Engine where textures will be stored.
    """
    # Open the .MTL file and read its lines
    with open(file_name, 'r') as f:
        lines = f.read().splitlines()  # Remove newline characters at the end of each line.

    # Collect list of image files associated with this MTL file for diffuse and normal maps
    lst_diffuse_maps = list(dict.fromkeys(returnImageListByToken(lines, "map_Kd", file_path)))  # Remove duplicates.
    lst_textures_diffuse = importListOfImageMaps(lst_diffuse_maps, texture_path)
    lst_normal_maps = list(dict.fromkeys(returnImageListByToken(lines, "map_Kn", file_path)))  # Remove duplicates.
    lst_textures_normal = importListOfImageMaps(lst_normal_maps, texture_path)

    # Initialize default material properties
    mat_name = ""
    material_pending = False
    diffuse_color = [0, 0, 0]
    specular_color = [0, 0, 0]
    map_diffuse = ""
    map_normal = ""

    # Process each line in the .MTL file
    for line in lines:
        s = line.lstrip()  # Remove leading TAB or spacing if present.
        ary = s.split(' ')  # Split by spaces.
        
        # Handle new material definition
        if ary[0] == 'newmtl':
            if material_pending:
                # Generate the pending material before starting a new one
                generate_material(material_path, mat_name, map_diffuse, diffuse_color, lst_diffuse_maps, lst_textures_diffuse)
            mat_name = ary[1]  # Update material name
            material_pending = True  # Mark that there's a material pending generation
        
        # Update material properties based on the line's token
        if ary[0] == 'Ks':
            specular_color = [float(ary[1]), float(ary[2]), float(ary[3])]
        elif ary[0] == 'Kd':
            diffuse_color = [float(ary[1]), float(ary[2]), float(ary[3])]
        elif ary[0] == 'map_Kd':
            map_diffuse = ary[1]
        elif ary[0] == 'map_Kn':
            map_normal = ary[1]

    # Generate the last material if it is still pending
    if material_pending:
        generate_material(material_path, mat_name, map_diffuse, diffuse_color, lst_diffuse_maps, lst_textures_diffuse)
        unreal.log("MTL file processed successfully.")

def generate_material(material_path, mat_name, map_diffuse, diffuse_color, lst_diffuse_maps, lst_textures_diffuse):
    """
    Generates a material in Unreal Engine based on the provided specifications.
    
    Args:
        material_path (str): The path in Unreal Engine where the material will be created.
        mat_name (str): The name of the material.
        map_diffuse (str): The name of the diffuse map file.
        diffuse_color (list): The diffuse color as [R, G, B].
        lst_diffuse_maps (list): A list of diffuse map file paths.
        lst_textures_diffuse (list): A list of imported Texture2D objects for diffuse maps.
    """
    shader_name = returnValidUnrealMaterialName("M_%s" % mat_name)
    unreal.log(f"Generating material: {shader_name}")
    unreal.log(f"Diffuse color: {diffuse_color}.")
    unreal.log(f"Diffuse map: {map_diffuse}.")

    texture_diffuse = None  # Default to None if no map is specified
    if map_diffuse:
        # Search for the diffuse texture in the list of imported textures
        for i, entry in enumerate(lst_diffuse_maps):
            if entry.endswith(map_diffuse):
                texture_diffuse = lst_textures_diffuse[i]
                break

    # Call the function to create a new material with the specified properties
    createNewImageMapOpaqueMaterial(material_path, shader_name, texture_diffuse, None, diffuse_color, 0.92, 0.26)
    unreal.log(f"Material {shader_name} generated successfully.")
