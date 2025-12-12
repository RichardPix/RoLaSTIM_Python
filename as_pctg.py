# -*- coding: utf-8 -*-
"""
Created on Tue May  7 11:46:41 2024

@author: Copyright (c) 2025 Yongquan Zhao @ Nanjing Institute of Geography and Limnology, Chinese Academy of Sciences (NIGLAS).
         E-mail: yongquanzhao181@gmail.com
         
Version 1.0: December 12, 2025.

This code package is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0) license.
"""

from rasterio.mask import mask
import geopandas as gpd
import numpy as np
import thiessen
import os


def make_dir(path):
    isExists=os.path.exists(path) 
    if not isExists:
      os.mkdir(path)
      print(path+' created.')
      return True
    else:
        print (path+' existed')
        return False


# Create lake buffers.
def get_lakeshore_buf(polygons_gdf, crs, buffer_dist, level):    
    buffers = polygons_gdf['geometry'].buffer(buffer_dist)

    buffers_gdf = gpd.GeoDataFrame(geometry=buffers)
    buffers_gdf.crs = crs
    
    return buffers_gdf


# Convert lake polygons to lines.
def get_lake_line(polygon_gdf, crs):  
    # Convert polygons to lines
    lines = polygon_gdf['geometry'].boundary

    mlines = lines[0] # get the line from the Series. MultiLineString or LineString.
    if mlines.geom_type == 'MultiLineString':
        mls_list = list(mlines.geoms) # geoms method for multipart geometries.
        boundary_linestring = mls_list[0] # Get the 1st LineString, i.e., lake boundary.
    else:
        boundary_linestring = mlines # geom_type: LineString
    
    boundary_linestring_gdf = gpd.GeoDataFrame(geometry=[boundary_linestring])
    boundary_linestring_gdf.crs = crs
        
    return boundary_linestring, boundary_linestring_gdf


# Create thiessen polygons based on a lake boundary.
def get_lakeshore_thi(boundary_linestring, dist_interval, level, crs):
    equidistant_points = thiessen.equidistant_points_along_line(boundary_linestring, dist_interval)
    equidistant_points_gdf = gpd.GeoDataFrame(geometry=equidistant_points)
    
    vor_gdf = thiessen.create_thiessen_scipy(equidistant_points_gdf)
    vor_gdf.crs = crs 
    
    return vor_gdf


# Calculate artificial surface percentages in a lakeshore classification unit.
def get_as_pctg(thi_units, src_img):
    # Get the number of classification units.
    num_units = len(thi_units)
    # print("\n Polygons info:", thi_units.info())
    
    as_pctg_list = []
    
    for i in range(0, num_units):
        # Select the ith polygon from the shapefile.
        cur_plg = thi_units.iloc[i]
        # print("\n Prcessing unit %s" %(i+1), "of %s." %num_units)
        
        # Extract the geometry of the ith polygon and clip the raster image using the ith polygon geometry.
        clipped_lc_unit, _ = mask(src_img, [cur_plg.geometry], crop=True, nodata=src_img.nodata)
        clipped_lc_unit = np.squeeze(clipped_lc_unit, axis=0)

        # Find the indices of pixels with the specified value
        idx_as = np.argwhere(clipped_lc_unit == 30) # get impervious surface pixels.
        idx_unit = np.argwhere((clipped_lc_unit != 0) & (clipped_lc_unit != 255)) # get all valid pixels. 0 is the fill value in GLC, 255 is the background in the classificaiton units.
        pixnum_as = len(idx_as)        
        pixnum_unit = len(idx_unit)
        
        # Get the percentage of impervious surfaces in the classification unit.
        if (pixnum_unit != 0): # deal with division by zero
            as_pctg = pixnum_as / pixnum_unit
        else:
            as_pstg = 0
        as_pctg_list.append(as_pctg) 
    
    return as_pctg_list