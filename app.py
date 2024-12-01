from dash import Dash, dcc, html, callback, no_update, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime

app = Dash()
app.title = 'NYC Transit'

services = {
    'subways': 'Subways',
    'buses': 'Buses',
    'lirr': 'LIRR',
    'metro_north': 'Metro-North',
    'access_a_ride': 'Access-a-Ride',
    'bridges_and_tunnels': 'Bridges and Tunnels',
    'staten_island_railway': 'Staten Island Railway'
}

app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.H1(
                    children='Have MTA commutes recovered to pre-pandemic levels?',
                    className='page-title'
                )
            ],
            style={'padding': 5}
        ),
        html.Div(
            children=[
                html.Label(
                    children='Select a service:',
                    style={'width': '10%', 'display': 'inline-block'}
                ),
                dcc.Dropdown(
                    options=['All services'] + list(services.values()),
                    value='All services',
                    clearable=False,
                    id='service',
                    style={'width': '50%', 'display': 'inline-block'}
                )
            ],
            style={'padding': 5}
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.P(
                            id='description',
                            style={'padding-left': 10, 'padding-top': 10}
                        ),
                        dcc.Graph(
                            id='graph',
                            config={'displayModeBar': False},
                            style={'padding': 0}
                        ),
                        dcc.Tooltip(
                            id='graph-tooltip'
                        )
                    ],
                    style={'boxSizing': 'border-box', 'border': '1px solid #ccc'}
                ),
                # html.Div(
                #     children=[
                #         html.H5(
                #             children='About this service',
                #         ),
                #         html.P()
                #     ],
                #     style={'boxSizing': 'border-box', 'border': '1px solid #ccc'}
                # )
            ],
            style={'padding': 5}
        )
    ],
    style={'padding': 5, 'font-family': 'Montserrat'}
)

data = pd.read_csv("MTA_Daily_Ridership.csv")

text_replacement = {
    'Total Estimated Ridership': 'total',
    'Total Scheduled Trips': 'total',
    'Total Traffic': 'total',
    '% of Comparable Pre-Pandemic Day': 'percent',
    ': ': ':',
    ' ': '_',
    '-': '_'
}

def clean_column_name(column_name:str):
    for key, value in text_replacement.items():
        column_name = column_name.replace(key, value)
    column_name = column_name.lower()
    return column_name

data.columns = [clean_column_name(column) for column in data.columns]

for service in services.keys():
    data[f'{service}:pre_pandemic'] = np.where(
        data[f'{service}:percent'] > 0,
        (data[f'{service}:total'] / data[f'{service}:percent'] * 100).round(),
        (data[f'{service}:total'] / 0.1 * 100).round(),
    ).astype(int)

data['week'] = pd.to_datetime(data['date']).dt.to_period('W-SAT').astype(str).str.split('/').str[0]
data['is_weekend'] = pd.to_datetime(data['date']).dt.weekday.isin([5, 6]).astype(int)

df = data.copy(deep=True)
df = df.melt(
    id_vars=['date', 'week', 'is_weekend'],
    value_vars=[column for column in data.columns if 'total' in column or 'pre_pandemic' in column]
)
df[['service', 'variable']] = df['variable'].str.split(':', expand=True)
df['service'] = df['service'].replace(services)
df = df.pivot(index=['date', 'week', 'is_weekend', 'service'], columns='variable', values='value').reset_index()

df_weekday = df.groupby(['week', 'is_weekend', 'service'])[['pre_pandemic', 'total']].sum().reset_index()
df_weekday['percent_change'] = (df_weekday['total'] / df_weekday['pre_pandemic'] * 100 - 100).round(0)
df_weekday['percent_change'] = np.where(
    df_weekday['total'] == 0,
    -100,
    df_weekday['percent_change']
)
df_weekday['percent_change'] = df_weekday['percent_change'].astype(int)

df_weekday = df_weekday.reset_index(drop=True)
df_weekday.columns.name = None

df_weekly = df.groupby(['week', 'service'])[['pre_pandemic', 'total']].sum().reset_index()
df_weekly['percent_change'] = (df_weekly['total'] / df_weekly['pre_pandemic'] * 100 - 100).round(0)
df_weekly['percent_change'] = np.where(
    df_weekly['total'] == 0,
    -100,
    df_weekly['percent_change']
)
df_weekly['percent_change'] = df_weekly['percent_change'].astype(int)

df_weekly = df_weekly.reset_index(drop=True)
df_weekly.columns.name = None

@callback(
    Output('graph', 'figure'),
    Input('service', 'value'),
)
def update_figure(service):
    if service == 'All services':
        fig = px.line(
            df_weekly,
            x='week',
            y='percent_change',
            color='service',
            title='Percentage change from pre-pandemic'
        )
        
        for service in services.values():
            fig.add_annotation(
                x=df_weekly['week'].max(),
                y=df_weekly[df_weekly['service'] == service]['percent_change'].tail(1).item(),
                text=service,
                font=dict(color='black'),
                showarrow=False,
                xanchor='left'
            )

        fig.update_xaxes(
            title=None,
            range=[
                datetime.strptime(df_weekday['week'].min(), '%Y-%m-%d').timestamp() * 1000,
                (datetime.strptime(df_weekday['week'].max(), '%Y-%m-%d').timestamp() + 5256000) * 1000
            ],
            ticks='outside',
            minor_ticks='outside',
            minor_nticks=6
        )
    
    else:
        fig = px.line(
            df_weekday[df_weekday['service'] == service],
            x='week',
            y='percent_change',
            color='is_weekend',
            title='Percentage change from pre-pandemic'
        )
        
        fig.add_annotation(
            x=df_weekday['week'].max(),
            y=df_weekday[(df_weekday['service'] == service) & (df_weekday['is_weekend'] == 1)]['percent_change'].tail(1).item(),
            text='Weekends',
            font=dict(color='black'),
            showarrow=False,
            xanchor='left'
            )
        fig.add_annotation(
            x=df_weekday['week'].max(),
            y=df_weekday[(df_weekday['service'] == service) & (df_weekday['is_weekend'] == 0)]['percent_change'].tail(1).item(),
            text='Weekdays',
            font=dict(color='black'),
            showarrow=False,
            xanchor='left'
            )
        
        fig.update_xaxes(
            title=None,
            range=[
                datetime.strptime(df_weekday['week'].min(), '%Y-%m-%d').timestamp() * 1000,
                (datetime.strptime(df_weekday['week'].max(), '%Y-%m-%d').timestamp() + 5256000) * 1000
            ],
            ticks='outside'
        )

    annotations = {
        '2020-03-03': [' First COVID-19 case' , 'red'],
        '2020-06-08': [' <br><br> City reopens in 4 phases', 'gray'],
        '2020-12-21': [' Vaccinations begin', 'gray'],
        '2021-09-13': [' City workers return to office', 'gray'],
        '2021-12-02': [' <br><br> First Omicron case', 'red'],
        '2022-09-07': [' MTA lifts mask mandate', 'gray'],
        '2023-10-23': [' Remote work policy expanded', 'gray']
    }

    fig.update_layout(
        showlegend=False,
        plot_bgcolor='white',
        font=dict(
            family='Montserrat',
            size=12,
        ),
        hoverlabel=dict(
            bgcolor='white',
            font_size=10,
            font_family='Montserrat'
        )
    )

    fig.update_yaxes(
        title=None,
        range=[-100, 40],
        ticks='outside',
        zeroline=True,
        zerolinecolor='gray'
    )
    
    fig.update_traces(hovertemplate='Week of %{x}<br><b>%{y:+g.0}%</b> from pre-pandemic')
    
    for key, value in annotations.items():
        fig.add_vline(
            datetime.strptime(key, '%Y-%m-%d').timestamp() * 1000,
            line_width=1,
            line_dash='dash',
            line_color=value[1],
            annotation_text=value[0]
        )

        fig.add_traces(
            go.Scatter(
                x=[datetime.strptime(key, '%Y-%m-%d').timestamp() * 1000],
                y=[35],
                mode='lines',
                line_dash='dot',
                line_color='red',
                showlegend=False,
                hovertemplate=f'{key} <br> {value[0]}<extra></extra>'
            )
        )

    return fig

@callback(
    Output('description', 'children'),
    Input('service', 'value'),
)
def update_description(service):
    description = service
    return description

if __name__ == '__main__':
    app.run_server(debug=True)