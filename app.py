from dash import Dash, dcc, html, callback, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime

app = Dash(__name__)
server = app.server
app.title = 'NYC Transit'

services = {
    'subways': 'Subways',
    'buses': 'Buses',
    'lirr': 'LIRR',
    'metro_north': 'Metro-North',
    'access_a_ride': 'Access-a-Ride',
    'bridges_and_tunnels': 'Bridges and Tunnels',
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
            style={'padding': 5, 'color': '#0039A5'}
        ),
        html.Div(
            children=[
                html.H5(
                    children='Select a service:',
                    style={'margin-right': 20, 'margin-top': 12, 'display': 'inline-block'}
                ),
                dcc.Dropdown(
                    options=['All services'] + list(services.values()),
                    value='All services',
                    clearable=False,
                    id='service',
                    style={'width': '50%', 'height': '30px', 'display': 'inline-block'}
                )
            ],
            style={'padding': 5, 'display': 'flex'}
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.H4(
                            id='description-line1',
                            style={'padding-left': 52, 'padding-top': 5}
                        ),
                        html.H4(
                            id='description-line2',
                            style={'padding-left': 52, 'padding-top': 0}
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

data = data.drop([column for column in data.columns if 'staten_island_railway' in column], axis=1)

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

df_weekday['is_weekend'] = df_weekday['is_weekend'].replace({0: 'Weekday', 1: 'Weekend'})

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
        color_discrete_map = {
            'Subways': '#C60C30',
            'Buses': '#0039A5',
            'LIRR': '#00A1DE',
            'Metro-North': '#009B3A',
            'Access-a-Ride': '#FBB720',
            'Bridges and Tunnels': '#6E267B',
        }

        fig = px.line(
            df_weekly,
            x='week',
            y='percent_change',
            color='service',
            color_discrete_map=color_discrete_map,
            title='Percentage change from pre-pandemic',
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
    
    else:
        fig = px.line(
            df_weekday[df_weekday['service'] == service],
            x='week',
            y='percent_change',
            color='is_weekend',
            title='Percentage change from pre-pandemic'
        )
                
        fig.update_xaxes(
            title=None,
            range=[
                datetime.strptime(df_weekday['week'].min(), '%Y-%m-%d').timestamp() * 1000,
                (datetime.strptime(df_weekday['week'].max(), '%Y-%m-%d').timestamp() + 5256000) * 1000
            ],
            ticks='outside'
        )

        fig.update_layout(
            showlegend=True,
            legend=dict(
                title=None,
                orientation='h',
                yanchor='bottom',
                y=0,
                xanchor='center',
                x=0.5
            ),
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

    annotations = {
        '2020-03-03': [' First COVID-19 case' , 'red', 'top', 'On <b>March 3, 2020</b>, Governor Andrew Cuomo confirmed the first case of COVID-19 person-to-person spread.<br>This was quickly followed by closures of in-office functions for non-essential business,<br>and non-essential gatherings via the "New York State on PAUSE" executive order signed on March 20, 2020.'],
        '2020-06-08': [' <br><br> City reopens in 4 phases', 'gray', 'bottom', 'Starting <b>June 8, 2020</b>, the city reopened in four biweekly phases, with incremental easing of restrictions<br>on office work, dining, education, amenities, and other services.'],
        '2020-12-21': [' Vaccinations begin', 'gray', 'top', 'The city began administering COVID-19 vaccines on <b>December 21, 2020</b>,<br>starting with healthcare workers and nursing home residents.'],
        '2021-09-13': [' City workers return to office', 'gray', 'top', 'Mayor Bill de Blasio announced plans for city employees to return to office starting <b>September 13, 2021</b>,<br>amidst strong vaccination rates.'],
        '2021-12-02': [' <br><br> First Omicron case', 'red', 'bottom', 'The highly-infectious Omicron variant quickly saw a surge in cases in New York City, starting from <b>December 2, 2021</b>,<br>when a Minnesota resident tested positive for the variant after returning from a visit.<br>This was followed by stricter safety protocols, and strengthening of mask and vaccination mandates.'],
        '2022-09-07': [' MTA lifts mask mandate', 'gray', 'top', 'Governor Kathy Hochul announced the end of mask requirements on public transport on <b>Septermber 7, 2022</b>,<br>accompanied by an MTA announcement that masks would be "encouraged, but optional"'],
        '2023-10-23': [' Remote work policy expanded', 'gray', 'top', "On <b>October 23, 2023</b>, Mayor Eric Adams announced an expansion of its hybrid work pilot program to non-unionized city employees,<br>citing success in the initial program and reflecting the city's stronger support towards remote work."]
    }

    fig.update_yaxes(
        title=None,
        range=[-100, 40],
        ticks='outside',
        tickformat='+d',
        zeroline=True,
        zerolinecolor='gray'
    )
    
    fig.update_traces(hovertemplate='Week of %{x}<br><b>%{y:+d}%</b> from pre-pandemic')
    
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
                y=[35 if value[2] == 'top' else 19],
                mode='lines',
                line_dash='dot',
                line_color='red',
                showlegend=False,
                hovertemplate=f'{value[3]}<extra></extra>'
            )
        )

    return fig

@callback(
    Output('description-line1', 'children'),
    Output('description-line2', 'children'),
    Input('service', 'value'),
)
def update_description(service):
    services_descriptions = {
        'All services': ['Vehicular traffic (Bridges and Tunnels) and Access-a-Ride trips are back to pre-pandemic levels.', 'However, other forms of public transport (Subways, Buses, Metro-North, LIRR) still lag behind.'],
        'Subways': ['Overall subway ridership has not recovered to pre-pandemic levels.', 'Weekend ridership shows slightly stronger recovery, driven by leisure and tourism.'],
        'Buses': ['Overall bus ridership remains significantly below pre-pandemic levels.', ' '],
        'LIRR': ['LIRR weekend ridership has surpassed pre-pandemic levels, driven by leisure travel and improved service reliability.', 'However, weekday ridership remains slightly below.'],
        'Metro-North': ['Metro-North weekend ridership recently surpassed pre-pandemic levels, driven by leisure travel. ', 'However, weekday ridership remains slightly below.'],
        'Access-a-Ride': ['Access-A-Ride scheduled trips have surpassed pre-pandemic levels, driven by city reopening and essential trips for seniors and individuals with disabilities.', ' '],
        'Bridges and Tunnels': ['Vehicle traffic across Bridges and Tunnels recovered quickly', 'due to increased car dependency during the pandemic.'],
    }
    description_line1 = services_descriptions[service][0]
    description_line2 = services_descriptions[service][1]
    return description_line1, description_line2

if __name__ == '__main__':
    app.run_server(debug=True)