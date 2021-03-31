#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  4 17:14:46 2020

@author: Disco
"""

import scipy.optimize as optimize
import numpy as np
import pandas as pd
import pickle
import sir_ode
import sir_cost
from scipy.integrate import odeint as ode
#import matplotlib.pyplot as plt

#Analiza las serie de datos

#path = "SinEscuela/"
path=""


R0list = []
lLugares = []
bins=[0,18,28,60,110]
labels = [0,1,2,3]
ledad = []
lcontagios = []
ltiempo = []
lmaxcont = []
for simu in range(0,9):
    #if simu == 2:
    #    continue
    archivo =  path + "datos{0}.pickle".format(simu)
    #archivo = "datos{0}.pickle".format(simu)
    with open(archivo, 'rb') as handle:
        u_data = pickle.load(handle)   
    personas = u_data.get('DF')
    dC = u_data.get('Estados') 
    datos = pd.DataFrame()
    for item in dC:
        nroIndices = len(item.index)
    #Estados :  suceptible = 1,no suceptible = 2, infectado = 3,
    #Contagioso con síntomas(infected en el paper) = 4, cuarentena = 5, hospitalizado = 6, uci = 7, muerto = 8
    #recuperado = 9, contagioso asiNtomatico = 10
        
        fila = pd.Series([0,0,0,0,0,0,0,0,0,0]) 
        for i in range(nroIndices):
    #        print('{0}-{1}'.format(item.index[i],item.iloc[i]))
            fila.iloc[(item.index[i]-1)] = item.iloc[i]
        datos = datos.append(fila, ignore_index=True)
    
    if (len(datos)<60) or (datos[7][69]<2):
        continue
    #Primero se calcula el R0
    times = list(range(len(datos)))   
    data = list(datos[3]+datos[4]+datos[5]+datos[6]+datos[9])

    largo = len(times)
    posicion = 0
    for numero in data:
        if numero >= 4:
            break
        posicion = posicion + 1
    times = times[posicion:largo]
    data = data[posicion:largo]

    params = [1, 1, 10000]
    #### Parameter estimation ####
    optimizer = optimize.minimize(sir_cost.NLL, params, args=(data, times), method='Nelder-Mead')
    param = np.abs(optimizer.x)
    R0list.append(param[0]/param[1])
    
    #Distribuciones de lugares de contagio
    lugares = personas.groupby('LugardeContagio').count()['Contagios']
    lLugares.append(lugares)
    
    #Grupos etareos
    personas['bins']=pd.cut(personas['P09'],bins=bins, labels=labels, include_lowest=True)
    grupo = personas.groupby(['bins','LugardeContagio']).count()['Contagios']
    ledad.append(grupo)
    
    #Cuantos contagios generaron
    grupo = personas.groupby('Contagios').count()['t0']
    lcontagios.append(grupo)
    
    #Momento de contagio
    grupo = personas.groupby('t0').count()['Contagios']
    ltiempo.append(grupo)
    
    #Donde se alcanzó el maximo numero de contagios
    lmaxcont.append(datos[2][datos[2]==max(datos[2])])

# pdf = pd.DataFrame(lLugares)
# pdf.to_csv('Lugares.csv',index=False) #Lugares de contagios
# pdf = pd.DataFrame(ledad)    
# pdf.to_csv('LugaresporEdad.csv',index=False) #Lugares de contagios
# pdf = pd.DataFrame(lcontagios)
# pdf.to_csv('Contagios.csv',index=False) #Lugares de contagios
# pdf = pd.DataFrame(ltiempo)
# pdf.to_csv('Tiempos.csv',index=False)
# pdf = pd.DataFrame(lmaxcont)
# pdf.to_csv('Maximos.csv',index=False)




