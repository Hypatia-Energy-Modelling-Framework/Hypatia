# -*- coding: utf-8 -*-
"""
Created on Tue Sep 13 15:30:23 2022

@author: NAMAZIFN
"""

import pandas as pd
from plotly import graph_objects as go



tech_group = "hydrogen supply"
techs = [
"H2_import",
"Electrolyzer",
"SMR_CCS", 
    ]

regions = ["reg1"]




def read_data(i):
    return pd.read_csv(
            fr"test/final_case/all_results/results_{i}/total_capacity/reg8/Conversion.csv",
            index_col=0,
            header=0
        )


data = list(map(read_data,list(range(12))))
#%%

data = pd.concat({f"result {i}":data[i] for i in list(range(12))},axis=1)
#%%

number_of_techs = len(data.columns.unique(1))
number_of_sens = len(data.columns.unique(0))
years = data.index.tolist()
techs = data.columns.unique(1)

x = sorted(years*number_of_sens)
#%%

fig = go.Figure()

for tech in techs:
    df = data.loc[:,(slice(None),tech)]
    df=df.unstack()
    idx = df.index.sortlevel(-1)[0]
    
    vals = df.loc[idx].values
    
    fig.add_trace(
        go.Box(
            x = x,
            y = vals,
            name = tech
            )
        )
    

    
fig.update_layout(
    yaxis_title='normalized moisture',
    boxmode='group' # group together boxes of the different traces for each value of x
)   
   
fig.write_html("gooz.html")
    #%%
data = {'name':["Akash", "Geeku", "Pankaj", "Sumitra", "Ramlal"],
       'Branch':["B.Tech", "MBA", "BCA", "B.Tech", "BCA"],
       'Score':["80", "90", "60", "30", "50"],
       'Result': ["Pass", "Pass", "Pass", "Fail", "Fail"]}
 
df = pd.DataFrame(data)
#%%
# pivoting the dataframe
df = df.pivot(columns = )
    
    