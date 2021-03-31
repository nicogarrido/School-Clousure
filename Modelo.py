#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 15:02:50 2020

@author: Disco
"""

import random
import pandas as pd
import time
from scipy.stats import powerlaw
import numpy as np
import pickle
from networkx.generators.random_graphs import erdos_renyi_graph
import networkx as nx
import os.path
import multiprocessing
import pandas.core.internals

def Simulacion(MC, conSE):
    hogares = []
    personas = []
    trabajo =[]
    edu_sup = []
    edu_basica = []
    usuariosTP ={}
    regionSelected = 11
    Comunas = []
    l_hogares = []

    def infeccion(grupo, p, lugar, tipo = 'tipo2'):
        nonlocal personas
        if len(grupo)==0:
            return
        p = 1/len(grupo)
        g = erdos_renyi_graph(len(grupo), p)
        vertices = nx.to_pandas_edgelist(g)
        for par in vertices.iterrows():
            id1 = par[1][0]
            id2 = par[1][1]
            if (personas.at[grupo[id1],'Estado'] == 1) and (personas.at[grupo[id2],'Estado']==4 or 
                                                                  personas.at[grupo[id2],'Estado']==10):
                personas.at[grupo[id1],'Estado'] = 3
                personas.at[grupo[id1],'TiempoTransicion'] = round(np.random.exponential(ti))    #Periodo de incubacion
                personas.at[grupo[id1],'t0'] = dia
                personas.at[grupo[id1],'LugardeContagio'] = lugar
                personas.at[grupo[id2],'Contagios'] = personas.at[grupo[id2],'Contagios'] + 1 
            if (personas.at[grupo[id2],'Estado'] == 1) and (personas.at[grupo[id1],'Estado']==4 or
                                                                  personas.at[grupo[id1],'Estado']==10):    
                personas.at[grupo[id2],'Estado'] = 3
                personas.at[grupo[id2],'TiempoTransicion'] = round(np.random.exponential(ti)) #incubacion
                personas.at[grupo[id1],'Contagios'] = personas.at[grupo[id1],'Contagios'] + 1
                personas.at[grupo[id2],'t0'] = dia
                personas.at[grupo[id2],'LugardeContagio'] = lugar

    def infeccionTransporte(grupo, tamanoBuses, p, lugar, tipo = 'tipo2'):
        nonlocal personas
        if len(grupo)==0:
            return

        totPasajeros = len(grupo)

        listaAleatoria = random.sample(range(totPasajeros),totPasajeros)
        buses = int(totPasajeros / tamanoBuses) + 1
    
    #    personas.at[grupo[lista2[i]],'TiempoparaContagiar'] = round(np.random.exponential(2))               
        p = 1/tamanoBuses
        for b in range(buses):
            desde = b * tamanoBuses
            hasta = min(((b+1) * tamanoBuses - 1), (len(pasajeros)))
            
            g = erdos_renyi_graph((hasta-desde), p)
            vertices = nx.to_pandas_edgelist(g)
            for par in vertices.iterrows():
                id1 = listaAleatoria[desde + par[1][0]]
                id2 = listaAleatoria[desde + par[1][1]]
                if (personas.at[grupo[id1],'Estado'] == 1) and (personas.at[grupo[id2],'Estado']==4 or 
                                                                      personas.at[grupo[id2],'Estado']==10):
                    personas.at[grupo[id1],'Estado'] = 3
                    personas.at[grupo[id1],'TiempoTransicion'] = round(np.random.exponential(ti)) #periodo de incubacion   
                    personas.at[grupo[id2],'Contagios'] = personas.at[grupo[id2],'Contagios'] + 1                 
                    personas.at[grupo[id1],'t0'] = dia
                    personas.at[grupo[id1],'LugardeContagio'] = lugar
                if (personas.at[grupo[id2],'Estado'] == 1) and (personas.at[grupo[id1],'Estado']==4 or
                                                                      personas.at[grupo[id1],'Estado']==10):    
                    personas.at[grupo[id2],'Estado'] = 3
                    personas.at[grupo[id2],'TiempoTransicion'] = round(np.random.exponential(ti)) #incubacion               
                    personas.at[grupo[id1],'Contagios'] = personas.at[grupo[id1],'Contagios'] + 1                     
                    personas.at[grupo[id2],'t0'] = dia
                    personas.at[grupo[id2],'LugardeContagio'] = lugar                    

    def realizarTransiciones():
        nonlocal personas
        personas['TiempoTransicion'] = personas['TiempoTransicion'] - 1 
        #Personas que pasan de estar infectados a contagiosos sintomáticos o no sintomáticos
        infectados = (personas['Estado']==3) & (personas['TiempoTransicion']<=0) #En estado 3 está infectado, incubando
        ixs = personas[infectados].index
        if (len(ixs)>0):
            selector = np.random.uniform(0,1,len(ixs))
            ixstocontsyntom = ixs[selector<rho] #rho proporcion that become symptomatic
            ixstocontAsyntom = ixs[selector>=rho]
            personas.loc[ixstocontsyntom,'Estado'] = 4  #Ahora son contagiosos con síntomas
            personas.loc[ixstocontsyntom,'TiempoTransicion'] = np.round(np.random.exponential(tc,len(ixstocontsyntom)))
            personas.loc[ixstocontAsyntom,'Estado'] = 10  #Ahora son contagiosos sin síntomas
            personas.loc[ixstocontAsyntom,'TiempoTransicion'] = np.round(np.random.exponential(tia,len(ixstocontAsyntom)))
    
    #Contagioso con sintomas que pasan a estar en cuarentena      
        contagioso = (personas['Estado']==4) & (personas['TiempoTransicion']<=0) #Los que cambian a contagiosos
        ixs = personas[contagioso].index 
        if len(ixs)>0:
            personas.loc[ixs,'Estado'] = 5  #Ahora esta en cuarentena
            personas.loc[ixs,'TiempoTransicion'] = np.round(np.random.exponential(tq,len(ixs)))
    #Contagioso sin sintomas que pasan a ser recuperados  
        contagioso = (personas['Estado']==10) & (personas['TiempoTransicion']<=0) #Se recuperan
        ixs = personas[contagioso].index 
        if len(ixs)>0:
            personas.loc[ixs,'Estado'] = 9  #Recuperado
            personas.loc[ixs,'TiempoTransicion'] = 0
    
    
    #Personas en cuarentena que pasan a estar hospitalizado
        cuarentena = (personas['Estado']==5) & (personas['TiempoTransicion']<=0) #Los que estan en cuarentena
        ixs = personas[cuarentena].index
        if len(ixs)>0:
            selector = np.random.uniform(0,1,len(ixs))
            ixstoh = ixs[personas[cuarentena]['Pprogreso'] <= selector]
            ixstor = ixs[personas[cuarentena]['Pprogreso'] > selector]
            personas.loc[ixstoh,'Estado'] = 6 #Hospitalizado
            personas.loc[ixstoh,'TiempoTransicion'] = np.round(np.random.exponential(th,len(ixstoh)))
            personas.loc[ixstor,'Estado'] = 9
    
    #Hospitalizado a UCI
        hospitalizado = (personas['Estado']==6) & (personas['TiempoTransicion']<=0) #EStas hospitalizado
        ixs = personas[hospitalizado].index
        if len(ixs)>0:
            selector = np.random.uniform(0,1,len(ixs))
            ixstouci = ixs[personas[hospitalizado]['Pprogreso'] <= selector]
            ixstor = ixs[personas[hospitalizado]['Pprogreso'] > selector]
            personas.loc[ixstouci,'Estado'] = 7 #UCI
            personas.loc[ixstouci,'TiempoTransicion'] = np.round(np.random.exponential(tu,len(ixstouci)))
            personas.loc[ixstor,'Estado'] = 9
    
    #UCI            
        enUCI = (personas['Estado']==7) & (personas['TiempoTransicion']<=0) #Los que cambian a contagiosos
        ixs = personas[enUCI].index
        if len(ixs)>0:
            selector = np.random.uniform(0,1,len(ixs))
            ixstodeath = ixs[personas[enUCI]['Pprogreso'] <= selector]
            ixstor = ixs[personas[enUCI]['Pprogreso'] > selector]
            personas.loc[ixstodeath,'Estado'] = 8 #Muerto
            personas.loc[ixstor,'Estado'] = 9
    
    #Para los que están recuperados
        recuperados = personas['Estado'] == 9
        ixs = personas[recuperados].index
        if len(ixs)>0:            
            selector = np.random.uniform(0,1,len(ixs))
            ixstosuceptible = ixs[selector<epsilon]
            ixstonosuceptible = ixs[selector>=epsilon]
            personas.loc[ixstosuceptible,'Estado'] = 1 #Suceptible
            personas.loc[ixstonosuceptible,'Estado'] = 2 #No Suceptible        
        

    def cargaDatosDirectos(conSchool):
        nonlocal hogares
        nonlocal personas
        nonlocal trabajo
        nonlocal edu_sup
        nonlocal edu_basica
        nonlocal usuariosTP
        nonlocal regionSelected
        nonlocal Comunas
        nonlocal l_hogares
        inicial = time.perf_counter()
        if conSchool == True:
            archivo = "datosinicialesconSchool.pickle"
        else:
            archivo = "datosinicialessinSchool.pickle"

        with open(archivo, 'rb') as handle:
            u_data = pickle.load(handle)   
        personas = u_data.get('personas')
        hogares = u_data.get('hogares') 
        trabajo = u_data.get('trabajo') 
        edu_sup = u_data.get('edu_sup') 
        edu_basica = u_data.get('edu_basica') 
        usuariosTP = u_data.get('usuariosTP') 
        regionSelected = u_data.get('regionSelected')
        Comunas = u_data.get('Comunas') 
        l_hogares = u_data.get('l_hogares')

        final = time.perf_counter()
        print(f"Tiempo para terminar la carga directa de {archivo} fue de {final-inicial} ")    
        
        
    #%%Parametrización
    conSistemaEducativo = conSE
    #Crea Datos y los graba
    #cargarDatos()
    #preparaEstructurasComplementarias(conSistemaEducativo) #True quiere decir que se hace con colegio
    #grabaDatos()
    cargaDatosDirectos(conSistemaEducativo)
    
    #alpha = 1 #No esta implementado
    ti = 3
    rho = 0.5
    tc = 0.5 #Tiempo desde que le aparece la infección hasta que entra en quarentena
    tia = 11
    tq = 6
    #beta = 0.2 #Sin uso
    th = 3
    #gamma = 0.26 #Sin uso
    tu = 3
    #delta = 0.2 #sin uso
    epsilon = 0.05
    ph = 0.3
    peb = 0.1
    pes = 0.1
    pt = 0.1
    pr = 0.1
    ptransporte = 0.1

        
    #viviendas.drop(viviendas[viviendas.REGION!=regionSelected],inplace=True)
    #hogares.drop(hogares[hogares.REGION!=regionSelected].index,inplace=True)
    #personas.drop(personas[personas.REGION!=regionSelected].index,inplace=True)
    
    #%%Condiciones iniciales
    
    GranInicial = time.perf_counter()  
    #Estados :  suceptible = 1,no suceptible = 2, infectado = 3,
    #Contagioso con síntomas(infected en el paper) = 4, cuarentena = 5, hospitalizado = 6, uci = 7, muerto = 8
    #recuperado = 9, contagioso asiNtomatico = 10

    for simulacion in range(0,MC):
        print(f"Inicio de la simulacion {simulacion} de {MC}")
        personas['Estado'] = 1 #Todos en estado de suceptibles
        #Se usa para ver el tiempo de transición entre estados. Varía entre estados
        personas['TiempoTransicion'] = 0 
        #Cuenta a cuántas personas contagió
        personas['Contagios'] = 0
        #En que momento se contagió
        personas['t0'] = -1
        personas['LugardeContagio'] = 0
        
        #P17 = 1 son los trabajadores
        #locales = personas[(personas['REGION']==regionSelected) & (personas['P17']==1) & (personas['COMUNA']==11101) & (personas['T_asignado']==1)]
        locales = personas[(personas['REGION']==regionSelected) & (personas['P17']==1) & (personas['T_asignado']==1)]
        personas.at[locales.iloc[0].name,'Estado'] = 3
        personas.at[locales.iloc[0].name,'t0'] = 0 #El primer contagiado!!
        
        
        # print(personas['Infectadas'].sum())
    
    
    #%%
    
        dC = []

        dia = 0
        SimulacionExitosa = True #Es una bandera, para ver si hay contagiados después de un período
        for semana in range(10):
            if semana==1:
                #Controlamos al final de la primera semana
                if len(personas[personas['t0']>0])<2:
                    #Al final de la primera semana solo dos contagios no es posible
                    print("###Terminó esta simulación por falta de contagiados")
                    SimulacionExitosa = False
                    break
            for diaSemana in range(7):
                dia = dia + 1
                if diaSemana < 5:        
                    print ('Día {0} de la Semana {1}'.format((diaSemana+1), semana))
                else:
                    print ('Día {0} del finde de Semana {1}'.format((diaSemana-4), semana))
        
                dC.append(personas[personas['REGION']==regionSelected].groupby('Estado').count()['COMUNA'])
                 
                #inicial = time.perf_counter()   
                realizarTransiciones()
                #final = time.perf_counter()
                #print("Tiempo para actualizar estados: {0:f} ".format(final-inicial))    
                    
                #Se calcula R
                #Contagios = personas[(personas['REGION']==regionSelected) & ((personas['Estado']==4) | (personas['Estado']==10))]['Contagios'].sum()
                #Enfermos = len(personas[(personas['REGION']==regionSelected) & ((personas['Estado']==4) | (personas['Estado']==10))])
        
                #calculoR.append(Contagios/Enfermos)
                
            #%%Everyone is in the state of rest
            
                # inicial = time.perf_counter()      
                #nik = 0
                for hogar in l_hogares:
                    #print("Comuna {0}".format(idxc)) 
                    #nik = nik + 1
                    #print(nik)
                    if len(hogar) > 1:
                        infeccion(hogar, ph, lugar=1)
                        
                # final = time.perf_counter()
                # print("Tiempo para descanso en casa: {0:f} ".format(final-inicial))    
                
                #%%Every household move to work/education
                
                if diaSemana < 5:
                    # inicial = time.perf_counter()   
                    tamanoBuses = 60
                 
              
                    for idxc, comuna in Comunas[Comunas['REGION']==regionSelected].iterrows():
                        if idxc in usuariosTP:
                            pasajeros = usuariosTP[idxc]            
                            infeccionTransporte(pasajeros, tamanoBuses, ptransporte, lugar=2)                
            
                    # final = time.perf_counter()
                    # print("Tiempo viaje al trabajo: {0:f} ".format(final-inicial))    
                
                
                #%%Everyone is in the state of work/education
                 
                    # inicial = time.perf_counter()      

                    if conSistemaEducativo==True:
                        #Educacion Primaria  
                        # lista = []
                        # for index, relacion in edu_basica.iterrows():
                        #     if relacion['pos']==0:
                        #         infeccion(lista, peb, lugar=3)                
                        #         lista = []
                        #     lista.append(relacion['id_p'])                        
                        
                        # #Se hace el último grupo
                        # infeccion(lista, peb, lugar=3)

                        for colegio in edu_basica.items():
                            infeccion(colegio[1], peb, lugar=3)                
                        
                        
                        ##Educacion superior            
                        # lista = []
                        # for index, relacion in edu_sup.iterrows():
                        #     if relacion['pos']==0:
                        #         if len(lista)>0:
                        #             infeccion(lista, pes, lugar=4)                
                        #             lista = []
                        #     lista.append(relacion['id_p'])
                        
                        # #Se hace el último grupo
                        # infeccion(lista, pes, lugar=4)
                        for carrera in edu_sup.items():
                            infeccion(carrera[1], pes, lugar=4)
                    
                    ##trabajo            
                    # lista = []
                    # for index, relacion in trabajo.iterrows():
                    #     if relacion['pos']==0:
                    #         if len(lista)>0:
                    #             infeccion(lista, pt, lugar=5)    
                    #             lista = []
                    #     lista.append(relacion['id_p'])
                    
                    # #Se hace el último grupo
                    # infeccion(lista, pt, lugar=5)          
                    
                    for empresa in trabajo.items():
                        infeccion(empresa[1], pt, lugar=5)
                            
                    # final = time.perf_counter()
                    # print("Tiempo el trabajo, universidad y colegios: {0:f} ".format(final-inicial))    
                
                            
                
                
                #%%Everyone move to the state of distraction
                # inicial = time.perf_counter() 
                tamanoBuses = 60      
                for idxc, comuna in Comunas[Comunas['REGION']==regionSelected].iterrows():
                    if idxc in usuariosTP:
                        pasajeros = usuariosTP[idxc]            
                        infeccionTransporte(pasajeros, tamanoBuses, ptransporte, lugar=2)                
            
                # final = time.perf_counter()
                # print("Tiempo viaje al momento de ocio: {0:f} ".format(final-inicial))  
                
                
                #%%Everyone in the state of leisure time
                if diaSemana < 5: 
                    #Vamos a suponer que el 0.3 de la población  
                    #acuden a unos 50 lugares cada 100.000 personas
                    porcentajeQuehaceOcio = 0.3
                    ratiodeOcio = 50/100000
                else:
                    #Fin de semana
                    #Vamos a suponer que el 0.6 de la población sale 
                    #acuden a unos 200 lugares cada 100.000 personas
                    porcentajeQuehaceOcio = 0.6
                    ratiodeOcio = 200/100000
                
                
                # inicial = time.perf_counter()        
                for idxc, comuna in Comunas[Comunas['REGION']==regionSelected].iterrows():
                    #print("Comuna {0}".format(idxc))    
                    perss = personas[personas['COMUNA']==idxc].sample(frac=porcentajeQuehaceOcio)
                    lugares = int( ratiodeOcio * len(perss) )
                    
                    numeros = powerlaw.rvs(1.6, size=lugares)
                    distribucion = (numeros / sum(numeros)) * len(perss)
                    
                    for i in range(lugares):
                        lista = []
                        nroPersonas = int(distribucion[i])
                        for j in range(nroPersonas):
                            lista.append(perss.iloc[j].name) #Se agrega el indice
                        infeccion(lista, pr, lugar=6)    
                # final = time.perf_counter()
                # print("Tiempo de ocio: {0:f} ".format(final-inicial))  
                
                
                
                #%%Everyone move to the state of rest
                
                tamanoBuses = 60
                # inicial = time.perf_counter()        
                for idxc, comuna in Comunas[Comunas['REGION']==regionSelected].iterrows():
                    if idxc in usuariosTP:
                        pasajeros = usuariosTP[idxc]            
                        infeccionTransporte(pasajeros, tamanoBuses, ptransporte, lugar=2)                
                
                # final = time.perf_counter()
                # print("Tiempo para el viaje a casa: {0:f} ".format(final-inicial))
                                
        
        #%%Se guardan los datos
        if SimulacionExitosa == True:
            personasRegion = personas[personas['REGION']==regionSelected]
            losdatos = {'DF': personasRegion, "Estados":dC}
            
            simuExitosa = 0
            while True:
                if conSistemaEducativo==True:
                    archivo = "datoscSE{0}.pickle".format(simuExitosa)
                else:
                    archivo = "datossSE{0}.pickle".format(simuExitosa)
                    
                if os.path.exists(archivo) == False:
                    break        
                simuExitosa = simuExitosa + 1
            
            with open(archivo, 'wb') as handle:
                pickle.dump(losdatos, handle, protocol=pickle.HIGHEST_PROTOCOL)
    
    final = time.perf_counter()
    print("Terminó la simulación en: {0:f} ".format(final-GranInicial))
    return


if __name__ == '__main__':
    # jobs = []
    # for i in range(2):
    #     p = multiprocessing.Process(target=Simulacion, args=(1,))
    #     jobs.append(p)
    #     p.start()


    print("Inicio de la Simulacion")
    Simulacion(1, True) #Primer parametro es numero de simulaciones, segundo con o sin escuela
    Simulacion(1, False)