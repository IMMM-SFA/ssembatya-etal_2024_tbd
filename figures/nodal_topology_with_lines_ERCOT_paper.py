# -*- coding: utf-8 -*-
"""
Created on Mon Aug 15 11:48:51 2022

@author: kakdemi
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# import descartes
import geopandas as gpd
from shapely.geometry import Point, Polygon
import networkx as nx
from matplotlib.lines import Line2D
import matplotlib.patches as mpatches

#Plotting the figure

plt.rcParams['font.sans-serif'] = "Arial"



#Reading and specifying the number of nodes
all_selected_nodes = pd.read_csv('selected_nodes_150.csv',header=0)
all_selected_nodes = [*all_selected_nodes['SelectedNodes']]




#Set the lat/lon bounds for the plot:
lat_min = 25
lat_max = 38
lon_min = -108
lon_max = -92

#Setting the rojection
projection= 4269


#Reading all necessary files for plotting the map
df = pd.read_csv('ERCOT_Bus.csv',header=0)


#Specifying the projection and geometry
crs = {'init':'epsg:4269'}

geometry = [Point(xy) for xy in zip(df['Substation Longitude'],df['Substation Latitude'])]
nodes_df = gpd.GeoDataFrame(df,crs=crs,geometry=geometry)
nodes_df = nodes_df.to_crs("EPSG:2163")

#States shape file
states_gdf = gpd.read_file('geo_export_9ef76f60-e019-451c-be6b-5a879a5e7c07.shp')
nodes_df = nodes_df.to_crs(epsg= projection)

#importing the lines
lines_df = pd.read_csv('line_params.csv',header=0)

all_line_nodes = []

for a in range(len(lines_df)):
    line_name = lines_df.loc[a,'line']
    splitted_name = line_name.split('_')
    line_list = [int(splitted_name[1]),int(splitted_name[2])]
    all_line_nodes.append(line_list)

#subsetting to the nodes we want to display
Selected_topology_nodes = nodes_df[nodes_df['Number'].isin(all_selected_nodes)].copy()
Selected_topology_nodes.reset_index(drop=True,inplace=True)
Selected_topology_nodes["Loc"]=0

allnodes= list(Selected_topology_nodes['Number'])            
            
#Plotting the figure
fig,ax = plt.subplots(1, 1, figsize=(25, 10))
states_gdf.plot(ax=ax,color='white',edgecolor='black',linewidth=0.5)

#Plotting the lines
G_all_lines = nx.Graph(ax=ax)
for i in all_selected_nodes:
    
    my_pos_1 = nodes_df.loc[nodes_df['Number']==i].geometry.x.values[0]
    my_pos_2 = nodes_df.loc[nodes_df['Number']==i].geometry.y.values[0]
    
    G_all_lines.add_node(i,pos=(my_pos_1,my_pos_2))     
 
for i in range(len(all_line_nodes)):
  
    G_all_lines.add_edge(all_line_nodes[i][0],all_line_nodes[i][1]) 

pos_lines=nx.get_node_attributes(G_all_lines,'pos')
nx.draw_networkx_edges(G_all_lines,pos_lines, edge_color='royalblue',alpha=0.6,width=0.8)

#Plotting the nodes
Selected_topology_nodes.plot(ax=ax,
                             edgecolor='black',
                             linewidth=0.8, 
                             markersize=150, 
                             color='peru',
                             alpha=1, 
                             marker='o',
                                          
                             #legend=True,
                             #legend_kwds ={'label': ('Total Daily Outages (MWh)'), 'orientation': 'vertical'})
                             legend_kwds ={ 'orientation': 'vertical'})
                                          

ax.set_box_aspect(1)
ax.set_xlim(lon_min, lon_max)
ax.set_ylim(lat_min, lat_max)
plt.axis('off')


#CUSTOMIZED LEGEND        
# I created 6 proxy members to generate the legend
nodes, = plt.plot( np.NaN, np.NaN, color='peru', marker="o", linestyle = 'none',  markersize=12, markeredgecolor='black', label=' Nodes'  )
lines, = plt.plot( np.NaN, np.NaN, color='royalblue', linewidth=1, linestyle = 'solid', label=' Transmission lines')

# You can adjust the parameters below according to your needs <3
plt.legend(handles=[nodes, lines],
            loc='lower left',
            columnspacing=2, handletextpad=.2, handlelength=2, frameon=True, fontsize=25, bbox_to_anchor=(0.01, 0.1))    

plt.tight_layout()

#plt.show() 

plt.savefig('allnodes_with_lines.png',dpi=400, bbox_inches='tight')

