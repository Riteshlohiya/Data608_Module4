import pandas as pd
import numpy as np
import string as s
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

url = ('https://data.cityofnewyork.us/resource/nwxe-4ae8.json?$limit=5&$offset=' + str(0) + '&$select=count(tree_id)').replace(' ', '%20')
trees = pd.read_json(url)
cnt = pd.read_json(url)
print(cnt)


#The tree has 683,788 rows.


boro = 'Bronx'
soql_url = ('https://data.cityofnewyork.us/resource/nwxe-4ae8.json?' +\
        '$select=spc_common,count(tree_id)' +\
        '&$where=boroname=\'Bronx\'' +\
        '&$group=spc_common').replace(' ', '%20')
soql_trees = pd.read_json(soql_url)

print(soql_trees)

url2 = ('https://data.cityofnewyork.us/resource/nwxe-4ae8.json?' +\
        '$select=count(tree_id),boroname,spc_common, health,status' +\
         '&$where=health!=\'NaN\'' +\
        '&$group=boroname,health,status,spc_common,steward'+\
        '&$order=boroname').replace(' ', '%20')

a2 = pd.read_json(url2)

print(a2)

# get the data

df = pd.read_json('https://data.cityofnewyork.us/resource/nwxe-4ae8.json?$limit=50000')

# drop the rows with missing data
df1 = df.filter(['boroname','spc_common','health', 'tree_id', 'steward'], axis=1)

#Question1: What proportion of trees are in good, fair, or poor health according to the ‘health’ variable?

df1['count_tree_id'] = df1.groupby(['spc_common'])['tree_id'].transform('count')

df1 = df1.dropna(axis=0, how='any')
print(df1)

tot = df1.groupby(['boroname', 'spc_common'])['count_tree_id'].sum()
tot = tot.reset_index(drop=False)

hlt = df1.groupby(['boroname', 'spc_common', 'health'])['count_tree_id'].sum()
hlt = hlt.reset_index(drop=False)

print(tot)
print(hlt)

tot.columns = ['boroname', 'spc_common', 'species_tot']
hlt.columns = ['boroname', 'spc_common', 'health', 'total']

print(tot)
print(hlt)

tp = pd.merge(hlt, tot, on=['boroname', 'spc_common'])

tp['ratio'] = tp['total']/ tp['species_tot']

print(tp)

tp['spc_common'] = tp['spc_common'].apply(lambda x: x.title())
species = np.sort(tp.spc_common.unique())


#Question2: Are stewards (steward activity measured by the ‘steward’ variable) having an impact on the health of trees?

steward = df1.groupby(['boroname', 'spc_common', 'steward'])['count_tree_id'].sum()
steward = steward.reset_index(drop=False)
steward.columns = ['boroname', 'spc_common', 'steward', 'steward_total']
print(steward)

steward_f = pd.merge(df1, steward, on=['boroname', 'spc_common', 'steward'])
print(steward_f)

rank = {'Poor':1, 'Fair':2, 'Good':3}
steward_f['health_level'] = steward_f['health'].map(rank)
steward_f.sort_values(by=['boroname', 'spc_common', 'steward']).head(10)
steward_f['health_index'] = (steward_f['count_tree_id']/steward_f['steward_total']) * steward_f['health_level']
steward_f.sort_values(by=['boroname', 'spc_common', 'steward']).head(10)
hlt_index = steward_f.groupby(['boroname', 'spc_common', 'steward'])['health_index'].sum()
hlt_index = hlt_index.reset_index(drop=False)
hlt_index.columns = ['boroname', 'spc_common', 'steward', 'health_index']
rank2 = {'3or4':3, '4orMore':4, 'None':1, '1or2':2}
hlt_index['steward_level'] = hlt_index['steward'].map(rank2)
rank3 = { 'Manhattan':'Manhattan', 'Bronx':'Bronx', 'Brooklyn':'Brooklyn', 'Queens':'Queens', 'Staten Island':'Staten Island'}
hlt_index['borough'] = hlt_index['boroname'].map(rank3)
hlt_index['spc_common'] = hlt_index['spc_common'].apply(lambda x: x.title())

print(hlt_index)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.H4('Species'),
    dcc.Dropdown(
        id='species',
        options=[{'label': i, 'value': i} for i in species],
        value="'Schubert' Chokecherry",
        style={'height': 'auto', 'width': '300px'}
    ),
    dcc.Graph(id='graph-ratio'),
    dcc.Graph(id='graph-health')
], style={'columnCount': 1})

@app.callback(
    Output('graph-ratio', 'figure'),
    [Input('species', 'value')])
def dash(Species):
    new = tp[tp.spc_common == Species]
    manhattan = new[new.boroname == 'Manhattan']
    bronx = new[new.boroname == 'Bronx']
    brooklyn = new[new.boroname == 'Brooklyn']
    queens = new[new.boroname == 'Queens']
    staten_island = new[new.boroname == 'Staten Island']
    facts = []

    facts.append(go.Bar(
        x=queens['health'],
        y=queens['ratio'],
        name='Queens',
        opacity=0.9
    ))

    facts.append(go.Bar(
        x=manhattan['health'],
        y=manhattan['ratio'],
        name='Manhattan',
        opacity=0.9
    ))

    facts.append(go.Bar(
        x=bronx['health'],
        y=bronx['ratio'],
        name='Bronx',
        opacity=0.9
    ))

    facts.append(go.Bar(
        x=brooklyn['health'],
        y=brooklyn['ratio'],
        name='Brooklyn',
        opacity=0.9
    ))

    facts.append(go.Bar(
        x=staten_island['health'],
        y=staten_island['ratio'],
        name='Staten Island',
        opacity=0.9
    ))

    return {
        'data': facts,
        'layout': go.Layout(
            xaxis={'title': 'Health'},
            yaxis={'title': 'Proportion'},
            legend=dict(x=-.15, y=1.5)
        )
    }


@app.callback(
    Output('graph-health', 'figure'),
    [Input('species', 'value')])

def dash2(Species):
   new1 = hlt_index[hlt_index.spc_common == Species]
   facts2 = []
   for i in new1.borough.unique():
        df_by_borough = new1[new1['borough'] == i]
        facts2.append(go.Scatter(
            x=df_by_borough['steward_level'],
            y=df_by_borough['health_index'],
            mode='markers',
            opacity=0.9,
            marker={
                'size': 10,
                'line': {'width': 0.75, 'color': 'white'}
            },
            name=i
            ))

        return {

        'data': facts2,
        'layout': go.Layout(
            yaxis={'title': 'Health Index'},
            xaxis=dict(tickvals=[1, 2, 3, 4], ticktext=['None', '1or2', '3or4', '4orMore'], title='Steward'),
            margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            legend=dict(x=-.1, y=1.2)
        )
    }


if __name__ == '__main__':
    app.run_server(debug=True)





