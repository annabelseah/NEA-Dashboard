import os
#os.chdir(r"C:\Users\user\Random Forest Board")

import base64
import datetime
import io
import numpy as np
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.express as px

import pandas as pd
import base64
import os
from urllib.parse import quote as urlquote
import dash_bootstrap_components as dbc
from flask import Flask, send_from_directory
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output


#load in latest geopandas file
import pandas as pd


import shapefile
shp_path = r"Grids_Update.shp"
with shapefile.Reader(shp_path) as shp:
    geojson_data = shp.__geo_interface__


import json
with open("grids.geojson") as f:
    geojson_data = json.load(f)

    
import pathlib
token = open("maptoken.txt").read()   
px.set_mapbox_access_token(token)

external_stylesheets = [dbc.themes.LUX]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'Dengue Risk Map'
server = app.server

app.layout = html.Div([
    dbc.Container([
        
        # section to upload dengue data
            html.Div( [
                html.H1('Upload Dengue Data', style={'textAlign': 'center'}),
           dcc.Upload(
            id="upload-rfdata",
            children=html.Div(
                ["Drag and drop or click to select a file to upload."]
            ),
            style={
                "width": "100%",
                "height": "60px",
                "lineHeight": "60px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px",
            },
            multiple=True,
        ),
        ],className="wrapper"),
        
        html.Div(id='output-rfdata-div'),]),
        
    html.Div( [
        html.H1('Get Risk Map Predictions', style={'textAlign': 'center'}),
        html.H5('This may take awhile, go get a coffee!', style={'textAlign': 'center'}),
        html.Button(id="rfpred-button", children="Run Random Forest Model"),
        html.Div(id='output-predictions'),
   ],className="wrapper"),
    
    html.Div(
        children=[
             html.Div(
                children=dcc.Graph(
                    id="map-rfchart", config={"displayModeBar": False},
                ),
                className="card",
            ),
            
        ],
        className="wrapper",
    ),
        
        

            ])


def parse_contents(contents, filename, date):

    
    content_type, content_string = contents.split(',')
    print("hello")
    decoded = base64.b64decode(content_string)
    print("bye")

    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))

    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    return html.Div([
        html.H5(filename),
        html.H6(datetime.datetime.fromtimestamp(date)),
        
        dcc.Store(id='stored-rfdata', data=df.to_dict('records')),
         
        dbc.Row([
            dbc.Col(html.Div(
                children=[
                    html.Div(children="Select Target"),
                    dcc.Dropdown(
                        id="select-rftarget",
                        options=[{'label':x, 'value':x} for x in df.columns],
                        clearable=False,
                
                    ),
                ],style={"width": "50%"}
            ),width=4),
            
            
            
            dbc.Col(html.Div(
                children=[
                    html.Div(children="Select Predictors"),
                    dcc.Dropdown(
                        id="select-rfpredictor",
                        clearable=False,
                        multi=True,
                
                    ),
                ],style={"width": "50%"}
            ),width=4),
            
            dbc.Col(html.Div(
                children=[
                    html.Div(children="Select SectorID"),
                    dcc.Dropdown(
                        id="select-rfsector",
                        options=[{'label':x, 'value':x} for x in df.columns],
                        clearable=False,
                
                    ),
                ],style={"width": "50%"}
            ),width=4),
            
            
            
            ]),
        
        dbc.Row([
            dbc.Col(html.Div(
                children=[
                    html.Div(children="Select Year Column"),
                    dcc.Dropdown(
                        id="select-rfyear",
                        options=[{'label':x, 'value':x} for x in df.columns],
                        clearable=False,
                
                    ),
                ],style={"width": "50%"}
            ),width=6),
            
            
            
            dbc.Col(html.Div(
                children=[
                    html.Div(children="Select Year for Prediction"),
                    dcc.Dropdown(
                        id="select-rfyearvalue",
                        clearable=False,
                    ),
                ],style={"width": "50%"}
            ),width=6),
            
            
            
            
            ])
        

    ])

#to store the file
@app.callback(Output('output-rfdata-div', 'children'),
              [Input('upload-rfdata', 'contents')],
             [ State('upload-rfdata', 'filename'),
              State('upload-rfdata', 'last_modified')])
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children
 
#to update the predictor list    
@app.callback(
    Output('select-rfpredictor', 'options'),
    [Input('select-rftarget', 'value')],
    [State('stored-rfdata', 'data')]
)
def update_predictors(column,data):
    data=pd.DataFrame(data)
    return [{'label': i, 'value': i} for i in data.columns if i!= column]


#to update which year you want to predict
@app.callback(
    Output('select-rfyearvalue', 'options'),
    [Input('select-rfyear', 'value')],
    [State('stored-rfdata', 'data')]
)
def select_year(year,data):
    data=pd.DataFrame(data)
    return [{'label': i, 'value': i} for i in data[year].unique()]




@app.callback(Output('map-rfchart', 'figure'),
              [Input('rfpred-button','n_clicks')],
              [State('select-rftarget','value'),
              State('select-rfpredictor','value'),
              State('select-rfyear','value'),
              State('select-rfyearvalue','value'),
              State('select-rfsector','value'),
              State('stored-rfdata','data')])
def make_predictions_table(n,target,predictors,yearcol,yearvalue,sector,data):
    if n is None:
        return dash.no_update
    else:
        
        #split the data set up for prediction
        data = pd.DataFrame(data)
        df_train,df_test = data[data[yearcol]<yearvalue],data[data[yearcol]==yearvalue]
        
        #sort according to sector id
        df_test.set_index(sector,inplace=True)
        
        #print(df_test.index)
        #split train/test
        X_train,y_train = df_train[predictors],df_train[target]
        X_test,y_test = df_test[predictors],df_test[target]
                
        #import random forest 
        from sklearn.ensemble import RandomForestRegressor
        rf_model = RandomForestRegressor(n_estimators = 1000,n_jobs=-1)
        rf_model.fit(X_train,y_train)
        
        #produce predictions table
        mapframe= pd.DataFrame({"OBJECTID":X_test.index,"Predictions":rf_model.predict(X_test)})
        
        print(mapframe.head())
        
        print(mapframe.info())
        
        mapfig = px.choropleth_mapbox(mapframe, geojson=geojson_data, locations='OBJECTID', color='Predictions',
                                      color_continuous_scale="ylorrd",
                                      range_color=[0,max(mapframe.Predictions)],
                                      mapbox_style="open-street-map",
                                      zoom=10, center = {"lat": 1.35255, "lon": 103.82580},
                                      opacity=0.8,
                                      labels={'Predictions':'Predictions'},featureidkey ="properties.ID"
                                     )
       
        mapfig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, mapbox_accesstoken=token)
           
           
    return mapfig
        
    


if __name__ == '__main__':
    app.run_server(debug=False)
