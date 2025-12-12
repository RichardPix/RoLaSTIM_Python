# -*- coding: utf-8 -*-
"""
Created on Tue May  7 01:22:40 2024

@author: Copyright (c) 2025 Yongquan Zhao @ Nanjing Institute of Geography and Limnology, Chinese Academy of Sciences (NIGLAS).
         E-mail: yongquanzhao181@gmail.com
         
Version 1.0: December 12, 2025.

This code package is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0) license.
"""

import rasterio
import geopandas as gpd
from shapely.geometry import Polygon
import numpy as np
import as_pctg


#=========== Data loading (revise the paths per your device and env) ==========
roi = "tai"
# roi = "baikal"
# roi = "ladoga"
# roi = "geneva"
# roi = "erie"
# roi = "greatbear"
# roi = "victoria"
# roi = "tanganyika"
# roi = "taupo"
# roi = "greatlake"
# roi = "titicaca"
# roi = "buenosaires"

# Path to the input lake exterior polygon.
input_shp_path = "../RoLaSTIM_data/inputs/lake_exterior_polygon/" + roi + ".shp"

# Path to the input land cover raster data.
input_img_path = "../RoLaSTIM_data/inputs/lakeshore_buffer_raster/GLC2022_" + roi +"_15kmBuf_reclass.tif"

# Read the shapefile
gdf = gpd.read_file(input_shp_path)
crs = gdf.crs # Get the coordinate reference system

# Read the raster image
src_img = rasterio.open(input_img_path)
#==============================================================================


# ========================= Set output path ===================================
ouput_path = "../RoLaSTIM_data/results/shore_type"
as_pctg.make_dir(ouput_path)
# =============================================================================


#============================= Parameter setting ==============================
# Specify the buffer distance, with a unit of geographic degree.
buffer_dist_L1 =  0.0021 # 210 meters
buffer_dist_L2 =  0.0039 # 390 meters, almost 2 times of buffer_dist_L1

# Specify the lake shoreline interval.
dist_interval = 0.00210 # 210 meters

# Thresholds for the percentages of human-altered surface.
Th_L1 = 0.3
Th_L2 = 0.5
#==============================================================================


#=================== Creat the exterior polygon for lakes =====================
print("Extracing the lake exterior polygon...\n")
# get the exterior boundry of polygons.
exterior_boundary = gdf.exterior

# Create a GeoDataFrame containing the exterior boundry.
exterior_line = exterior_boundary[0]
exterior_polygon = Polygon(exterior_line)
exterior_polygon_gdf = gpd.GeoDataFrame(geometry=[exterior_polygon])
exterior_polygon_gdf.crs = crs
#==============================================================================


#================ Create lake shoreline classification units ==================
print("Generating Thiessen polygons...\n")
boundary, _ = as_pctg.get_lake_line(exterior_polygon_gdf, crs)

thi = as_pctg.get_lakeshore_thi(boundary, dist_interval, 1, crs)

print("Creating lakeshore buffer zones...\n")
buf_L1 = as_pctg.get_lakeshore_buf(exterior_polygon_gdf, crs, buffer_dist_L1, 1)
buf_L2 = as_pctg.get_lakeshore_buf(exterior_polygon_gdf, crs, buffer_dist_L2, 2)

print("Removing lakes from buffers...\n")
# Remove lake areas.
buf_L1_annulus = gpd.overlay(buf_L1, exterior_polygon_gdf, how='difference')
buf_L1_annulus.crs = crs
buf_L2_annulus = gpd.overlay(buf_L2, exterior_polygon_gdf, how='difference')
buf_L2_annulus.crs = crs

print("Cutting lake buffer annuluses by Thiessen ploygons...\n")
thi_units_L1 = gpd.overlay(thi, buf_L1_annulus, how='intersection')
thi_units_L2 = gpd.overlay(thi, buf_L2_annulus, how='intersection')

num_units = len(thi_units_L1)
print("Number of lakeshore classification units: %s" % num_units, "for Lake %s. \n" %roi)
#==============================================================================


#===================== Lake shoreline classification rules ====================
as_pctg_L1 = as_pctg.get_as_pctg(thi_units_L1, src_img)
as_pctg_L2 = as_pctg.get_as_pctg(thi_units_L2, src_img)

arr_as_pctg_L1 = np.array(as_pctg_L1)
type_L1 = arr_as_pctg_L1 >= Th_L1

arr_as_pctg_L2 = np.array(as_pctg_L2)
type_L2 = arr_as_pctg_L2 >= Th_L2

type_final = type_L1 | type_L2 
#==============================================================================


#================ Cut the lake shoreline by thiessen polygons; and save the classified lake shorelines =================
print("Cutting lake shorelines...\n")
_, boundary_lake_gdf = as_pctg.get_lake_line(exterior_polygon_gdf, crs)
    
# Perform spatial overlay to cut lake shorelines by thiessen polygons.
cut_lines_gdf = gpd.overlay(boundary_lake_gdf, thi, how='intersection')


print("Adding shore type attributes...\n")
# Add a new field with the shoreline type values.
cut_lines_gdf['Type'] = type_final # 0 for natural, 1 for artificial.

# Save the new GeoDataFrame to a shapefile
cut_lines_gdf.to_file(ouput_path + '/shore_type_' + str(round(dist_interval * 100000)) + "interv_" 
                      + str(round(buffer_dist_L1 * 100000)) + '_'+ str(round(buffer_dist_L2 * 100000)) + 'buf_' + roi  + '.shp')

print("Done!")
#=======================================================================================================================

