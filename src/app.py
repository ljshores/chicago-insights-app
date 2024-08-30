#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 29 08:09:06 2024

@author: laurenshores
"""


import pandas as pd
import plotly.express as px  # (version 4.7.0 or higher)
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, dash_table  # pip install dash (version 2.0.0 or higher)
import dash_bootstrap_components as dbc

import geopandas as gpd
#import matplotlib.pyplot as plt



app = Dash(external_stylesheets=[dbc.themes.FLATLY])
server = app.server

# -- Import and clean data (importing csv into pandas)
# df = pd.read_csv("intro_bees.csv")
df = pd.read_csv("assets/Chi_Map_Data_2.csv")
race_df = pd.read_csv("assets/Race_Cnts_Dataset.csv")
rental_df1 = pd.read_csv("assets/Chi_Rentals_Formatted_Data1.csv")
#rental_df2 = pd.read_csv("assets/Chi_Rentals_Formatted_Data2.csv")
#rental_df = pd.concat([rental_df1, rental_df2], axis=0)
rental_df = rental_df1 # workaround to import less data in case memory is causing prod app not to render

df["geometry"] = df["cmntyGeom"].astype(str)

chi3_byCmnty_sub = df.groupby(["community", "geometry"]).agg({'restaurant_bar_cafe' : lambda x: x.sum(skipna=True), 
                                            'beauty' : lambda x: x.sum(skipna=True),
                                            'income_medhh' : lambda x: x.mean(skipna=True),
                                            'perc_white' : lambda x: x.mean(skipna=True),
                                            'perc_black' : lambda x: x.mean(skipna=True),
                                            'perc_hispanic' : lambda x: x.mean(skipna=True),
                                            'perc_asian' : lambda x: x.mean(skipna=True),
                                            'Theft' : lambda x: x.sum(skipna=True),
                                            "Violent Crime" : lambda x: x.sum(skipna=True),
                                            "Homicide" : lambda x: x.sum(skipna=True),
                                            "T_ArrstRate" : lambda x: x.mean(skipna=True),
                                            "VC_ArrstRate" : lambda x: x.mean(skipna=True),
                                            "H_ArrstRate": lambda x: x.mean(skipna=True),
                                            "avg_rental_price": lambda x: x.mean(skipna=True),
                                            "pop_density": lambda x: x.sum(skipna=True)}).reset_index() 

chi3_byCmnty_sub['geometry'] = gpd.GeoSeries.from_wkt(chi3_byCmnty_sub['geometry'])
chi3_byCmnty_sub = gpd.GeoDataFrame(chi3_byCmnty_sub, geometry='geometry', crs="EPSG:4326")

# -----formatting race for charts ---

race = pd.melt(race_df[['community','blkGrpGeom','pop_white', 'pop_black',
       'pop_asian', 'pop_native', 'pop_other', 'pop_mixed']], id_vars=["community", "blkGrpGeom"])

ethnicity = pd.melt(race_df[['community','blkGrpGeom','is_hispanic', 'not_hispanic']], id_vars=["community", "blkGrpGeom"])

ethnicity_byGrp = pd.DataFrame(ethnicity.groupby(["community", "variable"])["value"].sum()).reset_index()
race_byGrp = pd.DataFrame(race.groupby(["community", "variable"])["value"].sum()).reset_index()
#-----

# to geopandas dataframe at blockGrp level

df["geometry"] = df["blkGrpGeom"]

df['geometry'] = gpd.GeoSeries.from_wkt(df['geometry'])
df = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:4326")

cmnties = df['community'].drop_duplicates() 

max_theft = round(df['Theft'].max())
max_vc = round(df['Violent Crime'].max())
max_rental_avg = round(df['avg_rental_price'].max())
#----- formatting rentals for table

rentals = rental_df[["blkGrpGeom","address","price","beds","link"]] \
    .merge(df[["blkGrpGeom", "community", "Theft", 
               "Violent Crime", "Homicide", "avg_rental_price", "restaurant_bar_cafe"]], how="left",
           on="blkGrpGeom")

del rental_df
del rental_df1
del race_df
# ------------------------------------------------------------------------------
# App layout


sidebar = html.Div(
    [
        dbc.Row(
            [
                html.H3('WindyCity Insights',
                        style={'margin-top': '12px', 'margin-left': '24px'})
                ],
            style={"height": "9vh"},
            className='bg-primary text-white font-italic'
            ),
        
        dbc.Row(
            [
                html.Div([
                    html.P(['This tool brings together Chicago rent prices, population demographics, crime, \
                           and business data so that users can understand areas of the city. \
                               The bottom half explores variables at the block group level; \
                                   the top by community level data.',
                           html.Br(),
                           'Click on the map to see race proportions in the sidebar by community area.'
                           ],
                           style={'margin-top': '8px', 'margin-bottom': '4px'},
                           className='font-weight-bold'),
                    # select community html.Pand dcb.Dropdown for select attribute used to be here,
                    html.Hr(),
                    #html.H4('Race and Ethniciy: Click Community Map to Change'),
                    #html.P('Race and Ethniciy: Click Community Map to Change',
                     #      style={'margin-top': '16px', 'margin-bottom': '1px'},
                      #     className='font-weight-bold'),
                    dcc.Graph(id='race_pie', figure={}, style={'width': '320px'}
                              ),
                    
                    ]
                    )
                ],
            style={'height': '57vh', 'margin': '8px'}),
        dbc.Row(html.P()),
        
        dbc.Row(
            html.Div([
                html.Hr(),
            html.H5('Census Block Group Filter Inputs'),
                html.P('Max Number of Thefts',
                           style={'margin-top': '16px', 'margin-bottom': '4px'},
                           className='font-weight-bold'),
            dcc.Input(id="theft_map_filter", type="number", value=max_theft+2,  placeholder="Max Value {}".format(max_theft)), #placeholder="Max Value",
            
            
            html.P('Max Number of Violent Crimes',
                       style={'margin-top': '16px', 'margin-bottom': '4px'},
                       className='font-weight-bold'),
            dcc.Input(id="vc_map_filter", type="number",  value=max_vc+2),
        
            html.P('Max Average Rental Price',
                       style={'margin-top': '16px', 'margin-bottom': '4px'},
                       className='font-weight-bold'),
            dcc.Input(id="rental_map_filter", type="number",  value=max_rental_avg+2),
            
            html.P('Min Number of Restaurants/Bars/Cafes',
                       style={'margin-top': '16px', 'margin-bottom': '4px'},
                       className='font-weight-bold'),
            dcc.Input(id='rstrnt_map_filter', type="number", value=-1)
            
            
        
                ],
            #style={"height": "45vh"}, #className='bg-dark text-white',
            
            ))
        ]
)

content = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div([
                            html.P(id='my_map_title',
                                   children='Community (Neighborhood) Level Map',
                                   className='font-weight-bold'),
                            dcc.Graph(id='my_chi_map',
                                      #figure={},
                                      className='bg-light')])
                        ]),
                dbc.Col(
                    [
                        html.Div([
                            html.P(id='bar-title',
                                   children='Variable Rank by Community',
                                   className='font-weight-bold'),
                            dcc.Graph(id="cmnty_bar",
                                      figure={},
                                      className='bg-light')])
                        ])
                ],
            style={'height': '50vh',
                   'margin-top': '16px', 'margin-left': '8px',
                   'margin-bottom': '8px', 'margin-right': '8px'}),
        
        #new
        dbc.Row( [html.P('Select Community Level Variable',
               style={'margin-top': '8px', 'margin-bottom': '4px'},
               className='font-weight-bold'),
        
        dcc.Dropdown(id="slct_attribute",
                     options=[
                         {"label": "Restaurants/Bars/Cafes", "value": "restaurant_bar_cafe"},
                         {"label": "Median HH Income", "value": "income_medhh"},
                         {"label": "Average Rental Price", "value": "avg_rental_price"},
                         {"label": "White Population %", "value": "perc_white"},
                         {"label": "Black Population %", "value": "perc_black"},
                         {"label": "Hispanic Population %", "value": "perc_hispanic"},
                         {"label": "Population Density", "value": "pop_density"},
                         {"label": "Asian Population %", "value": "perc_asian"},
                         {"label": "Homicide", "value": "Homicide"},
                         {"label": "Violent Crime", "value": "Violent Crime"},
                         {"label": "Theft", "value": "Theft"}],
                     multi=False,
                     value="restaurant_bar_cafe",
                     style={'width': '320px'}
                     )]
            ),#end new
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div([
                            html.P('Census Block Group Level Map',
                                   className='font-weight-bold'),
                            dcc.Graph(id='my_blkGrp_map',
                                      #figure={},
                                      className='bg-light')])
                        ]),
                dbc.Col(
                    [
                        html.Div([
                            html.P('Rental Properties',
                                   className='font-weight-bold'),
                            dash_table.DataTable(id='rental_tbl',
                                                 columns = [{"name": i, "id": i,'type': 'text', "presentation":"markdown"} for i in rentals[["community","address", "price", "beds"]].columns ],
                                                 style_table={
                #'overflowX': 'auto',
                #'width':'100%',
                #'margin':'auto'
                },
                row_deletable=False,
                virtualization=True,
                #row_selectable="single",
                page_current= 0,
                page_size= 10,
                fill_width=False,
                style_data={
                    'whiteSpace': 'normal',
                    'height': 'auto',
                },
                style_cell = {
                #'font-family': 'cursive',
                'font-size': '14px',
                #'text-align': 'center'
            },
                )])
                        ])
                ],
            style={"height": "50vh", 
                   'margin-top': '16px', 'margin-left': '8px',
                   'margin-bottom': '8px', 'margin-right': '8px'})
        ]
    )

app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(sidebar, width=3, className='bg-light'),
                dbc.Col(content, width=9)
                ],
            style={"height": "100vh"}
            ),
        ],
    fluid=True
    )












        

        
# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components
@app.callback(
    [#Output(component_id='output_container', component_property='children'),
     Output(component_id='my_chi_map', component_property='figure'),
     
    Output(component_id='cmnty_bar', component_property='figure')],
   # Output(component_id='race_pie', component_property='figure')],
    [Input(component_id='slct_attribute', component_property='value')]#,
     #Input(component_id='slct_cmnty', component_property='value')]
)
def update_graph(option_slctd):
    #print(option_slctd)
    #print(type(option_slctd))

    #container = "The param chosen by user was: {}".format(option_slctd)

    dff = chi3_byCmnty_sub#.copy()
    
    dff = dff[['geometry', 'community', option_slctd]]
    #-----
    fig = px.choropleth(dff, 
                        geojson=dff.geometry, 
                        locations=dff.index, 
                        color=option_slctd,
                        hover_name='community',
                        hover_data={'community': True, option_slctd : True}, #'points': [{'customdata': dff['community'].drop_duplicates()}]}
                        #color_continuous_scale="magma",
                        #height=700,
                        #template='plotly_dark'
                        )
    fig.update_layout(#title_text='Chicago Community Areas',
                      #autosize=False,
                      width=490,
                      height=340,
                      margin=dict(l=40, r=20, t=20, b=30),
                      #autoexpand=True),
                      clickmode='event+select',  
                      )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update(layout_coloraxis_showscale = False) # to get rid of legend
    
    #---
    fig_bar = px.bar(dff.sort_values(option_slctd), x=option_slctd, y='community', orientation='h')
    fig_bar.update_layout(width=490,
                       height=340,
                       margin=dict(t=20, b=20, l=40, r=20),
                       #paper_bgcolor='rgba(0,0,0,0)',
                       #plot_bgcolor='rgba(0,0,0,0)',
                       #legend=dict(
                        #   orientation="h",
                         #  yanchor="bottom",
                          # y=1.02,
                           #xanchor="right",
                           #x=1) 
                       )
    #---

    return fig, fig_bar#, fig_pie, container,

@app.callback([Output(component_id='my_blkGrp_map', component_property='figure'),
               Output(component_id='rental_tbl', component_property='data')],
              [Input(component_id='theft_map_filter', component_property='value'),
               Input(component_id='vc_map_filter', component_property='value'),
               Input(component_id='rental_map_filter', component_property='value'),
               Input(component_id='rstrnt_map_filter', component_property='value'),
               Input(component_id='my_chi_map', component_property='selectedData')
               ])

def create_blkGrpMap(value1, value2, value3, value4, selectedData): #theft_map_filter, vc_map_filter, rental_map_filter, rstrnt_map_filter, selectedData
    df["color_anchor"] = '1'
    dff1 =df
    
    dff1['restaurant_bar_cafe'] = dff1['restaurant_bar_cafe'].astype(int)
    
    if value4 is not None:
        value4 = int(value4)

    mask = (dff1['Theft'] < value1 ) & \
        (dff1["Violent Crime"] < value2) & \
            (dff1['restaurant_bar_cafe'] > value4) & \
                ((dff1['avg_rental_price'] <= value3) | (dff1['avg_rental_price'].isna()))
       
    
    dff2 = dff1[mask]    
    
    
    fig = px.choropleth(data_frame=dff2, 
                            geojson=dff2.geometry, 
                            locations=dff2.index,
                        
                            color="color_anchor",
                            color_discrete_map={'1':  '#2b7bba'},
                        locationmode="geojson-id",
                        hover_name="community",
                        hover_data={'avg_rental_price': True, 'Theft' : True, 'Violent Crime': True, 'restaurant_bar_cafe':True, 'color_anchor':False},
                        #color_continuous_scale="magma",
                        featureidkey="id",
                            #template='plotly_dark'
                            )
    # Specify a default color for regions without data
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(showlegend=False)
    
    
    # ----- fig2 is a base map so can alwasy see blk outlines even when there is no data
    
    """fig2 = px.choropleth(data_frame=dff1, 
                        geojson=dff1.geometry,
                        color="color_anchor",
                        color_discrete_map={'1': '#bad6eb'},
                        hover_data={"community":True,'color_anchor':False},
                     
                    locations=dff1.index) 
    fig2.update_geos(fitbounds="locations", visible=False)
    fig2.update_traces(marker_line_color='black', marker_line_width=0.5)
    

    
    # ----- put the maps together using trace
    #trace0 = fig # the second map...the map that will lay on top
    fig2.add_trace(fig.data[0])
    fig.layout.update(showlegend=False)
    
    fig2.update_layout(#title_text='Chicago Community Areas',
                      #autosize=False,
                      showlegend=False,
                      width=500,
                      height=300,
                      margin=dict(l=40, r=20, t=20, b=20),
                      paper_bgcolor='rgba(0,0,0,0)'
                      )
    """
    #-----rentals
    
    dff3 = rentals
    
    try:
        cmnty_name = selectedData['points'][0]['customdata']#[0]
        cmnty_name=list(cmnty_name)
    except:
        cmnty_name = dff3["community"].drop_duplicates()
    
    
    mask2 = (dff3['Theft'] < value1 ) & \
        (dff3["Violent Crime"] < value2) & \
            (dff3['price'] <= value3) & \
                (dff3['restaurant_bar_cafe'] >= value4) & \
                    (dff3["community"].isin(cmnty_name)) 
            
    
    temp_tbl = dff3[mask2]
    
    #[Duck Duck Go](https://duckduckgo.com)
    
    temp_tbl['address'] = "[" + temp_tbl['address'] +"](" + temp_tbl['link'] +")"
    temp_tbl = temp_tbl[["community", "address", "price", "beds","link"]]
    
    #def make_clickable(val):
     #   return '<a href="{}">{}</a>'.format(val,val)
    #temp_tbl['link']=temp_tbl.style.format({'link': make_clickable})
    
    return fig, temp_tbl.to_dict('records')

"""
@app.callback([
               Output(component_id='rental_tbl', component_property='data')],
              [Input(component_id='my_chi_map', component_property='selectedData'),
               Input(component_id='theft_map_filter', component_property='value'),
               Input(component_id='vc_map_filter', component_property='value'),
               Input(component_id='rental_map_filter', component_property='value'),
               Input(component_id='rstrnt_map_filter', component_property='value'),
               
               ])


def get_rental_tbl(selectedData, theft_input_filter, vc_input_filter, rental_input_filter, rstrnt_input_filter):
    
    dff3 = rentals
    
    try:
        cmnty_name = selectedData['points'][0]['customdata']#[0]
        cmnty_name=list(cmnty_name)
    except:
        cmnty_name = dff3["community"].drop_duplicates()
    
    
    mask2 = (dff3['Theft'] < theft_input_filter )  & \
        (dff3["Violent Crime"] < vc_input_filter) & \
        (dff3['avg_rental_price'] <= rental_input_filter)# & \
     #       (dff3["community"].isin(cmnty_name)) 
    # #(dff3['restaurant_bar_cafe'] >= rstrnt_input_filter) & \
        
    try:
        temp_tbl = dff3[mask2]
    except:
        temp_tbl = dff3
    temp_tbl = temp_tbl[["community", "address", "price", "beds","link"]]
    
    

    #temp_tbl["link"] = temp_tbl["link"].apply(lambda x: make_clickable(x))
    
    #temp_tbl["link"] = make_clickable(temp_tbl["link"])
    
    return temp_tbl.to_dict('records')
"""

@app.callback(
    Output(component_id='race_pie', component_property='figure'),
    Input(component_id='my_chi_map', component_property='selectedData')

)

def create_pie(selectedData):
    inner_df = ethnicity_byGrp#.copy()
    outer_df= race_byGrp#.copy()
    
    try:
        cmnty_name = selectedData['points'][0]['customdata']#[0]
        cmnty_name=list(cmnty_name)
    except:
        cmnty_name = outer_df["community"].drop_duplicates()
    inner_df = inner_df[inner_df['community'].isin(cmnty_name)]
    outer_df = outer_df[outer_df['community'].isin(cmnty_name)]
    
    if len(cmnty_name) > 2:
        mytitle = "All Communities"
    else:
        mytitle = cmnty_name[0]
    title = '<b>{}</b>'.format(mytitle)


    trace1 = go.Pie(
    hole=0.5,
    sort=False,
    direction='clockwise',
    domain={'x': [0.15, 0.85], 'y': [0.15, 0.85]},
    labels = inner_df['variable'],
    values=inner_df['value'],
    #textinfo=ethnicity_byGrp['variable'],
    textposition='inside',
    marker={'line': {'color': 'white', 'width': 1}} )
    
    trace2 = go.Pie(
    hole=0.7,
    sort=False,
    direction='clockwise',
    values=outer_df["value"],
    labels=outer_df["variable"],
    
    #textinfo=race_byGrp["variable"],
    textposition='outside',
    marker={#'colors': ['green', 'red', 'blue'],
            'line': {'color': 'white', 'width': 1}}
    )
    
    fig_pie = go.FigureWidget(data=[trace1, trace2])
    fig_pie.add_annotation( text=title)
    fig_pie.update_layout(title_text= 'Race & Ethnicity Proportions',
                          width=320,
                      height=250,
                      margin=dict(l=30, r=10, t=70, b=10),
                      paper_bgcolor='rgba(0,0,0,0)',
                      )
    return fig_pie



# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=False)
    