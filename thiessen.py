# -*- coding: utf-8 -*-
"""
Created on Wed Apr 24 17:05:08 2024

@author: Copyright (c) 2025 Yongquan Zhao @ Nanjing Institute of Geography and Limnology, Chinese Academy of Sciences (NIGLAS).
         E-mail: yongquanzhao181@gmail.com
         
Version 1.0: December 12, 2025.

This code package is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0) license.
"""

import geopandas as gpd
import numpy as np 
from shapely.geometry import Polygon, box
from scipy.spatial import Voronoi


# Create equidistant segmentation points for lines.
def equidistant_points_along_line(line, distance):
    total_length = line.length
    num_points = int(total_length / distance)
    
    equidistant_points = []
    for i in range(num_points + 1):
        point = line.interpolate(i * distance)
        equidistant_points.append(point)
        
    return equidistant_points


# Create Thiessen polygons.
def create_thiessen_scipy(pts_gdf):
    # Extract geometry coordinates and convert them to numpy array
    pts_arr = np.array([geom.coords for geom in pts_gdf['geometry']])
    pts_arr = np.squeeze(pts_arr, axis=1)    

    ################## Force the number of Thiessen polygons to equal the number of points ######################
    # Calculate the bounding box of the points
    min_x, min_y = np.min(pts_arr, axis=0)
    max_x, max_y = np.max(pts_arr, axis=0) 
    # Create a bounding box geometry
    bounding_box = box(min_x - 0.05, min_y - 0.05, max_x + 0.05, max_y + 0.05) # unit: geographic degree
    # Add additional points around the boundary of the bounding box
    # These additional points will ensure that each original point has its own Voronoi cell, resulting in the same number of Thiessen polygons as the number of original points
    additional_points = np.array([
        [min_x - 0.25, min_y - 0.25],
        [max_x + 0.25, min_y - 0.25],
        [max_x + 0.25, max_y + 0.25],
        [min_x - 0.25, max_y + 0.25]
    ])    
    # Concatenate the original points with the additional points
    all_points = np.concatenate([pts_arr, additional_points])    
    
    
    # Compute the Voronoi diagram   
    vor = Voronoi(all_points) # Compute the Voronoi diagram by origial + additional points
    
    # Extract the Voronoi vertices and regions
    vertices = vor.vertices
    regions = vor.regions
    pt_rg = vor.point_region 
       
    # Create and plot the Thiessen polygons.
    thiessen_polygons = []
    for region_index in pt_rg:
        vertices_indices = regions[region_index]
        if -1 not in vertices_indices:
            polygon_vertices = vertices[vertices_indices]           
            plg = Polygon(polygon_vertices)
            
            # Clip the polygon by the bounding box (optional)
            plg = plg.intersection(bounding_box)
            
            thiessen_polygons.append(plg)
    
    vor_gdf = gpd.GeoDataFrame(geometry=thiessen_polygons)
    
    return vor_gdf