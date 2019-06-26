#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr  4 09:17:12 2019

Skript analyzuje epizody vysokych nameranych hodnot niecoho - napr. SO2. 
Zaroven vykresli aj vietor z blizkej specifikovanej stanice. 
Pre polutant s vysokymi hodnotami je moznost volby log. skaly
**** toto je len mala zmena na testovanie verzii - iba v komentari ***
@author: p2993
"""

import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt

import metpy.calc as mpc
from metpy.units import units

name = {
        'dtvalue':'date',
        'Bratislava, Jeséniova':'Jeséniova',
        'Bratislava, Mamateyova':'Mamateyova',
        'Bratislava, Trnavské Mýto':'Trnavské Mýto',
        'Bratislava, Kamenné nám.':'Kamenné nám.',
        'Bratislava Pod. Biskupice':'Biskupice',
        'Bratislava Vlcie Hrdlo':'VHrdlo',
        'Rovinka':'Rovinka'
}
colors = {
        'Jeséniova':'green',
        'Mamateyova':'orange',
        'Trnavské Mýto':'red',
        'Kamenné nám.':'blue',
        'Biskupice':'magenta',
        'VHrdlo':'brown',
        'Rovinka':'yellow'
        }

pth = "/data/oko/krajc/smog"
file2 = "{}/data/11816-2019-06-04.txt".format(pth)

spc = 'NO2'
logy = False

# Nacitam subor s time seriou polutantov:
file1 = "{}/data/{}.xlsx".format(pth, spc)

pol = pd.read_excel(file1, index_col='dtvalue',sheet_name='Hárok2')
clist = list(pol.columns)
for i in clist:
    pol = pol.rename(columns={i:name[i]})

# Zistenie maximalnej hodnoty polutantu:
sumar = pol.describe()
mxvals = sumar.max(axis=1)
mxmax = mxvals[-1]

# Priradenie farieb:
clrs = []
nms = pol.columns
for i in nms:
    clrs.append(colors[i])

# Pridam y poziciu na zobrazenie vetra:
if logy == True:
    pos = mxmax * 5
    ylim = (0, pos*10 )
else:
    pos = mxmax * 1.1
    ylim = (0, pos * 1.2)


# Funkcia premena ws, wd na u, v:
def components(ws, wd):
    (u, v) = mpc.wind_components(ws, wd * units.deg)
    au, av = float(abs(u)), float(abs(v))
    if au < 1e-10:
        u = 0.0
    if av < 1e-10:
        v = 0.0
    return (u, v)

# Vytvorim df s met. udajmi
met = pd.read_csv(file2,sep='\t')
met.date= pd.to_datetime(met.date)
met['ypos'] = pos
met.index = met.date
met = met.rename(columns={'ws_avg':'ws','wd_avg':'wd'})
met = met.drop(columns=['ta_2m', 'pr_sum', 'ii', 'date'])
# Vytvorim a zapisem subor pre analyzu v OpenAir:
big = pol.join(met)
big.to_csv('{}/data/{}_openair.csv'.format(pth,spc))

# Pridam k df zlozky vetra:
met['u'] = 0.0
met['v'] = 0.0
for i in range(met.shape[0]-1): 
    uv = components(met.ws[i], met.wd[i])
    met.u[i] = uv[0]
    met.v[i] = uv[1]

# Pridam normovane zlozky vetra (chcem mat rovnaku dlzku sipok)
met['su'] = met.u/met.ws
met['sv'] = met.v/met.ws    


# Colormap pre zobrazenie rychlosti vetra:
cmap = 'gray_r'

# vykreslenie obrazka:
figname = '{}/slovnaft_epizoda_{}'.format(pth, spc)

plt.rcParams.update({'font.size': 14})
plt.rcParams.update({'xtick.labelsize': 12})
plt.rcParams.update({'ytick.labelsize': 12})

fig, axes = plt.subplots(1,1, figsize = (18, 5))
pol.plot(ax = axes, kind='line', marker='o', logy=logy, color=clrs, legend=None, 
         grid=True, ylim=ylim)
axes.set_xlabel("")
a = plt.quiver(met.index, met.ypos, met.su, met.sv, met.ws, units='height', 
               width=0.01, cmap=cmap)
ca = plt.colorbar(a,label='Rýchlosť vetra - m / s')
plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=4)
#plt.legend(loc=(0.18, 0.25))
#plt.yscale('log')
axes.set_title('Koncentrácie {} na staniciach'.format(spc))
axes.set_ylabel('$\mu g /m^3$')

plt.savefig(figname, dpi=300, bbox_inches='tight')


