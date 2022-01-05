import os
#os.chdir(r"C:\Users\user\Epi Threshold Board")

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


external_stylesheets = [dbc.themes.LUX]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'Dengue Epidemic Threshold'
server = app.server

app.layout = html.Div([
    dbc.Container([
        
        # section to upload dengue data
            html.Div( [
                html.H1('Upload Dengue Data', style={'textAlign': 'center'}),
           dcc.Upload(
            id="upload-dengue-data",
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
        html.Div(id='output-div')],className="wrapper"),
            html.H1('Epidemic Threshold', style={'textAlign': 'center'}),
         html.Button(id='threshold-clicks', n_clicks=0, children='Press for Graph'),   
         html.Div(
            children=dcc.Graph(
                id="line-chart", config={"displayModeBar": False},
            ),
            className="card",
        ),

            ])
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
        
        dcc.Store(id='stored-data', data=df.to_dict('records')),
        
        dbc.Row(
            [     dbc.Col(
                 html.Div(
                     children=[
                         html.Div(children="Select Year Column", className="menu-title"),
                         dcc.Dropdown(
                             id="select-column",
                             options=[{'label':x, 'value':x} for x in df.columns],
                             clearable=False,
                             multi=False,
                     
                         ),
                     ]
                 )),
                
                
                dbc.Col(
                     html.Div(
                         children=[
                             html.Div(children="Select EWeek Column", className="menu-title"),
                             dcc.Dropdown(
                                 id="select-eweek",
                                 options=[{'label':x, 'value':x} for x in df.columns],
                                 clearable=False,
                                 multi=False,
                         
                             ),
                         ]
                     )),
                
                dbc.Col(
                     html.Div(
                         children=[
                             html.Div(children="Select Dengue Column", className="menu-title"),
                             dcc.Dropdown(
                                 id="select-dengue",
                                 options=[{'label':x, 'value':x} for x in df.columns],
                                 clearable=False,
                                 multi=False,
                         
                             ),
                         ]
                     )),
                
                dbc.Col(
                     html.Div(
                         children=[
                             html.Div(children="Select Dengue Threshold Column", className="menu-title"),
                             dcc.Dropdown(
                                 id="select-threshold",
                                 options=[{'label':x, 'value':x} for x in df.columns],
                                 clearable=False,
                                 multi=False,
                         
                             ),
                         ]
                     )),
                
                ]),
        
        dbc.Row([ 
                dbc.Col(
                html.Div(
                        children=[
                            html.Div(children="Select Year Output", className="menu-title"),
                         dcc.Dropdown(
                                id="select-output",
                                multi=False,
                  
                            ),
                        ]
                    )),
                dbc.Col(
                html.Div(
                    children=[
                        html.Div(children="Select Year Input", className="menu-title"),
                     dcc.Dropdown(
                            id="select-input",
                            multi=True,
              
                        ),
                    ]
                )),
                
                dbc.Col(
                html.Div(
                    children=[
                        html.Div(children="Select Moving Average", className="menu-title"),
                     dcc.Dropdown(
                            id="select-ma",
                            options=[{'label':x, 'value':x} for x in [9,13]],
                            multi=False,
              
                        ),
                    ]
                )),
                
                
         ]),
            
        


    ])

@app.callback([Output('output-div', 'children')],
              [Input('upload-dengue-data', 'contents')],
              [State('upload-dengue-data', 'filename'),
              State('upload-dengue-data', 'last_modified')])
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children
  
@app.callback(
    Output('select-output', 'options'),
    [Input('select-column', 'value')],
   [ State('stored-data', 'data')]
)
def update_year_dropdown(column,data):
    data =pd.DataFrame(data)
    return [{'label': i, 'value': i} for i in data[column].unique()]

@app.callback(
    Output('select-input', 'options'),
   [ Input('select-column', 'value'),
    Input('select-output', 'value')],
   [ State('stored-data', 'data')]
)
def update_year_input_dropdown(column,output,data):
    data =pd.DataFrame(data)
    selections = data[column].unique()
    selections = [int(x) for x in selections]
    dropdown = [int(x) for x in selections if int(x)<int(output)]
    return [{'label': i, 'value': i} for i in dropdown]




@app.callback(
    Output('line-chart', 'figure'),
    [Input('threshold-clicks','n_clicks'),
    Input('select-column', 'value'),
    Input('select-eweek', 'value'),
    Input('select-dengue', 'value'),
    Input('select-threshold', 'value'),
    Input('select-output', 'value'),
    Input('select-input', 'value'),
    Input('select-ma', 'value')],
    [State('stored-data', 'data')]
)
def compute_threshold(n,year_column,week_column,case_column,threshold_column, year_output,year_input,ma_window,data):
    if n is None:
        return dash.no_update
    else:
        data = pd.DataFrame(data)
        years_needed = year_input
        ma_window = ma_window//2
      #  print(data.info())
        print(ma_window)
        
       # print(year_input)
        #print(week_column)
        result = {}
        for eweek in range(1,54):   
         #   print(data[data[year_column]==year_output][week_column].unique())
            if eweek!=53 :
                #look at historical data
                other_years = data[(data[year_column].isin(years_needed)) & (data[week_column]==eweek)]
                index_list = [[*range(x-ma_window,x+ma_window+1)] for x in other_years.index]
                index_list = [item for sublist in index_list for item in sublist ]
                other_years = data.iloc[index_list]
                
                #compute mean and sd from historical data
                mean_dengue = other_years[threshold_column].mean()
                std_dengue = other_years[threshold_column].std()
                thr_dengue = mean_dengue + 2*std_dengue
                result[eweek]=round(thr_dengue)
        #rename the new column to "Threshold"
        tmp_results = pd.DataFrame(result.items(),columns=["E-week","Threshold"])
       # print(tmp_results.tail())
        plot_results = pd.merge(data[data[year_column]==year_output],tmp_results,how="right")
        print(plot_results.tail())
        
        #produce plots - plots the dengue case column and the Threshold column (newly created column)
        fig = px.line(plot_results, x=week_column, y=[case_column,"Threshold"],template="simple_white",\
                      labels={"variable":"Type","value":"Cases"}) #plots two y lines
        fig.update_xaxes(tickvals=np.arange(1,53,2),ticktext = np.arange(1,53,2),
                                             title_text="EWeeks")
        fig.update_yaxes(title_text="Dengue Cases")
        return fig



# =============================================================================
# @app.callback(
#     Output("map-chart","figure"),
#     Input('select-input', 'value'),
#     Input('select-column', 'value'),
#     Input('select-output', 'value'),
#     State('stored-data', 'data')
# )
# def update_threshold(column,year_output,year_input, data):
#     data =pd.DataFrame(data)
#     data.reset_index(inplace=True)
#     print(data.info())
# 
# =============================================================================




if __name__ == '__main__':
    app.run_server(debug=False)