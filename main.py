# Import packages
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
import json
import numpy as np
import plotly.graph_objects as go
import qrcode as qr
from jsonschema import validate
# Incorporate data from the proposed json export
with open("JsonExport.json", encoding="utf-8-sig") as jsonfile:
    data = json.load(jsonfile)
# Load the json schema
with open("json-schema.json", encoding="utf-8-sig") as jsonfile:
    schema = json.load(jsonfile)
# Validate the data against schema
validate(instance=data, schema=schema)
isSensor = False


# Get all the relevant data as dataframes
def get_relevant_tables(element_type,secondary_name):
    elements_df = pd.DataFrame.from_dict(data[element_type+'s'])
    elements_df.replace("", float("NaN"), inplace=True)
    elements_df.dropna(how='all', axis=1, inplace=True)
    element_types_df = pd.DataFrame.from_dict(data[element_type+"_Types"])
    element_types = element_types_df["Name"]
    element_types_with_id = element_types_df[["Name", "Identifier"]]
    elements_df_agg = elements_df.groupby(secondary_name+'typeIdentifier')[secondary_name + "typeIdentifier"].count().\
        reset_index(name="Count")
    element_df_by_type = elements_df_agg.merge(element_types_with_id, left_on=secondary_name + 'typeIdentifier',
                                               right_on='Identifier')[['Name', 'Count']]
    return elements_df, element_types, element_types_with_id, elements_df_agg, element_df_by_type


# Split the dataframe horizontally and vertically
def split_dataframes(df, no_columns, no_rows):
    vertical_split_dfs = np.split(df, np.arange(no_columns, len(df.columns), no_columns), axis=1)
    list_of_dfs = []
    for df in vertical_split_dfs:
        for i in range(0, len(df), no_rows):
            list_of_dfs.append(df.iloc[i:i+no_rows-1,:] )
    return list_of_dfs


# Given a dataframe of connections , generate the heatmap
def get_heatmap(df):
    heatmap_x = list(df.iloc[:0])
    heatmap_y = df.index
    heatmap_z = df
    hovertext = list()
    for yi, yy in enumerate(heatmap_y):
        hovertext.append(list())
        for xi, xx in enumerate(heatmap_x):
            hovertext[-1].append('Sensor: {}<br />Actuator: {}<br />Connection: {}'.format(xx, yy, "Connected" if heatmap_z.iloc[yi][xx]==1 else "Not Connected"))

    return go.Heatmap(z=heatmap_z, x=heatmap_x, y=heatmap_y, xgap=5, ygap=5,  colorscale='Viridis',  showscale=False, hoverinfo='text', hovertext=hovertext )


actuators_df, actuator_types, actuator_types_with_id, actuators_df_agg, actuators_df_by_type = get_relevant_tables("Actuator", "Actor")
sensors_df, sensor_types, sensor_types_with_id, sensors_df_agg, sensors_df_by_type = get_relevant_tables("Sensor", "Sensor")
sensors_df_with_rel = sensors_df.copy()
sensors_df.drop('RelatedElements', axis=1, inplace=True)
# Replace the Actuator dictionary with just its name
sensors_df_with_rel["Actuators"] = sensors_df_with_rel["RelatedElements"].apply(lambda x: [d['Name'] for d in x])
# Create separate row for each connected actuator
exploded_sensor_actuator_df = sensors_df_with_rel.explode('Actuators').reset_index(drop=True)[["Name", "Actuators"]]
exploded_sensor_actuator_df.rename(columns={'Name': 'Sensors'}, inplace=True)
# The existing rows are connected
exploded_sensor_actuator_df["Connected"] = 1
# Pivot the dataframe with Actuator Names
pivoted_connection_df = pd.pivot_table(exploded_sensor_actuator_df, values='Connected', index=['Actuators'], columns=['Sensors'], aggfunc=np.mean)
heatmap_dfs = split_dataframes(pivoted_connection_df, 10, 10)
mod_df = actuators_df.copy()
frames = [
    go.Frame(data=get_heatmap(df), name=i)
    for i, df in enumerate(heatmap_dfs)
]
heatmap = go.Figure(data=frames[0].data, frames=frames).update_layout(
    updatemenus=[
        {
            "buttons": [{"args": [None, {"frame": {"duration": 500, "redraw": True}}],
                         "label": "Play", "method": "animate",},
                        {"args": [[None],{"frame": {"duration": 0, "redraw": False},
                                          "mode": "immediate", "transition": {"duration": 0},},],
                         "label": "Pause", "method": "animate",},],
            "type": "buttons",
        }
    ],
    # iterate over frames to generate steps... NB frame name...
    sliders=[{"steps": [{"args": [[f.name],{"frame": {"duration": 0, "redraw": True},
                                            "mode": "immediate",},],
                         "label": f.name, "method": "animate",}
                        for f in frames],}],
    height=600,
    yaxis={"title": 'Actuators', "tickangle": 45},
    xaxis={"constrain":'domain',"title": 'Sensors', "tickangle": 45, 'side': 'top'},
    title_x=0.5,

)

# Initialize the app - incorporate a Dash Bootstrap theme
external_stylesheets = [dbc.themes.CERULEAN]
app = Dash(__name__, external_stylesheets=external_stylesheets)
# App layout
tab1_content = dbc.CardBody([
    dbc.Row([
            dbc.Col([
                html.Div('Select sensor or actuator :', className="text-secondary text-left fs-5")
                ]),
            dbc.Col([
                dbc.RadioItems(options=[{"label": x, "value": x} for x in ['Sensors', 'Actuators']],
                               value='Sensors',
                               inline=True,
                               id='radio-buttons-final')
                 ]),
            ]),
    dbc.Row([
        html.Hr()
    ]),

    dbc.Row([
        dbc.Col([

            html.Div('Select element type :', className="text-secondary text-left fs-5")
            ], width=4),
        dbc.Col([
            dcc.Dropdown(options=[x for x in actuator_types], value=actuator_types[0], id='dropdown'),
            ],width=4),
            ],  justify="start",),
    dbc.Row([
        html.Br()
    ]),
    dbc.Row([
        html.Br()
    ]),
    dbc.Row([
        dbc.Col([
            dash_table.DataTable(data=actuators_df.to_dict('records'), page_size=20, style_table={'overflowX': 'auto', 'overflowY':'auto'},
                                 id="data-table")
        ], width=8),

        dbc.Col([
            dbc.Row([
                dcc.Graph(figure={}, id="qr-image")]),


        ], width=4),
    ]),
    ])

tab2_content = dbc.Card(
    dbc.CardBody(
        [
            dbc.Col([

                dcc.Graph(figure=heatmap, id='my-first-graph-final-2')
            ], width=16),
        ]
    ),
    className="mt-3",
)
tab3_content = dbc.Card(
    dbc.CardBody(
        [
            dbc.Row([
            dbc.Col([
                dcc.Graph(figure=px.bar(actuators_df_by_type, x='Name', y='Count', title="Actuators per Actuator Type"), id='my-first-graph-final')
            ]),
            dbc.Col([
                dcc.Graph(figure=px.bar(sensors_df_by_type, x='Name', y='Count', title="Sensors per Sensor Type"), id='my-first-graph-final-3')
            ])
            ])
        ]
    ),
    className="mt-3",
)
app.layout = dbc.Container([
    dbc.Row([
        html.Div('Demo Application', className="text-primary text-center fs-3")
    ]),
    dbc.Tabs
        ([
            dbc.Tab(tab1_content, label="Element Type"),
            dbc.Tab(tab2_content, label="Connections"),
            dbc.Tab(tab3_content, label="Graphs"),
    ])

], fluid=True)


# Add controls to build the interaction
@callback(
    [Output(component_id='dropdown', component_property='options'),Output(component_id='dropdown', component_property='value')],
    Input('radio-buttons-final', 'value')
)
def update_type(plan_element):
    global isSensor
    if plan_element == 'Sensors':
        isSensor = True
        return [x for x in sensor_types], sensor_types[0]
    else:
        isSensor = False
        return [x for x in actuator_types], actuator_types[0]


@callback(
    Output(component_id='data-table', component_property='data'),
    Input('dropdown', 'value')
)
def update_table(col_chosen):
    global mod_df
    if isSensor :
        identifier = sensor_types_with_id[(sensor_types_with_id["Name"] == col_chosen)]["Identifier"]
        mod_df = sensors_df[(sensors_df["SensortypeIdentifier"] == identifier.values[0])]
        mod_df = mod_df.drop('SensortypeIdentifier', axis=1)
        return mod_df.to_dict('records')
    else:
        identifier = actuator_types_with_id[(actuator_types_with_id["Name"] == col_chosen)]["Identifier"]
        mod_df = actuators_df[(actuators_df["ActortypeIdentifier"] == identifier.values[0])]
        mod_df = mod_df.drop('ActortypeIdentifier', axis=1)
        return mod_df.to_dict('records')


@callback(
    Output(component_id="qr-image", component_property='figure'),
    Input(component_id='data-table', component_property='active_cell')
)
def get_qr_code(active_cell):
    if active_cell is not None:
        export_id = mod_df.iloc[active_cell["row"]]["ExportId"]
        name = mod_df.iloc[active_cell["row"]]["Name"]
    else:
        export_id = mod_df.iloc[0]["ExportId"]
        name = mod_df.iloc[0]["Name"]
    img = qr.make(export_id)
    fig = px.imshow(img, title="Qr Code for element " + name)
    return fig


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)