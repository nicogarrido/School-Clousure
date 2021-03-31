#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  2 22:43:58 2020

@author: Disco
"""

import random
import pandas as pd
import time
import pickle


conSchool = False #

hogares =[]
personas = []
trabajo = []
edu_sup = []
edu_basica = []    
l_hogares = []
usuariosTP = {}

regionSelected = 13 #Region Metropolitana
regionSelected = 11 #Es Aysen
Comunas = []

Actualizar = False
GranInicial = time.perf_counter()

#%%
aPath = ""

###Carga de datos pesados
inicial = time.perf_counter()
aViviendas = aPath + "Microdato_Censo2017-Viviendas.csv"
viviendas = pd.read_csv(aViviendas, sep=";")
viviendas = viviendas[['REGION', 'PROVINCIA','COMUNA','DC','AREA','ID_ZONA_LOC','NVIV']]
final = time.perf_counter()
print("Carga de Datos Viviendas {0:f}".format(final-inicial))


inicial = time.perf_counter()
if Actualizar==True:
    aHogares = aPath + "Microdato_Censo2017-Hogares.csv"
    hogares = pd.read_csv(aHogares, sep=";")
    hogares = hogares[['REGION', 'PROVINCIA','COMUNA','DC','AREA','ID_ZONA_LOC','NVIV','NHOGAR']]
else:
    hogares=pd.read_csv("Hogares_Creado0707.csv")
final = time.perf_counter()    
print("Carga de Datos Hogares {0:f}".format(final-inicial))


inicial = time.perf_counter()
if Actualizar==True:
    aPersonas = aPath + "Microdato_Censo2017-Personas.csv"
    personas = pd.read_csv(aPersonas, sep=";")
    personas = personas[['REGION', 'PROVINCIA','COMUNA','DC','AREA','ID_ZONA_LOC','NVIV'
                  ,'NHOGAR','PERSONAN','P08','P09','P13','P15','P17']]
else:
    personas=pd.read_csv('Personas_Creado0707.csv')
final = time.perf_counter()
print("Carga de Datos Personas {0:f}".format(final-inicial))


inicial = time.perf_counter()
aEmpresas = aPath + "empresas2017.csv"
Empresas = pd.read_csv(aEmpresas, sep=";")
Empresas.rename(columns={"Cod Region":"REGION", "Cod Comuna":"COMUNA"},inplace=True)
final = time.perf_counter()
##########Reasignacion de empresas entre comunas para corregir cupos
rPer = personas[personas['P17']==1].groupby('COMUNA').agg({'P17':'count','REGION':'min'}) #Personas por Comuna que trabajan
rFir =  Empresas.groupby('COMUNA').sum()['Trabajadores'] #Oferta de trabajo de las empresas
rFir.rename("Puestos", inplace=True)

capacidades = pd.concat([rPer,rFir],axis=1, sort=False)
capacidades['indice'] = capacidades['P17'] / capacidades['Puestos']

relLaboral = capacidades.groupby('REGION').sum()
relLaboral['ratio'] = relLaboral['P17']/relLaboral['Puestos']

Superavit = relLaboral[relLaboral['ratio']<=1] #La Unica Región es la 13

comunasSuperavit = capacidades[(capacidades['REGION']==13) & (capacidades['indice']<1)]
cDeficit = capacidades[(capacidades['indice']>1)]

cS = comunasSuperavit.sort_values(by="indice", ascending=True).copy(deep=True)

for idxdc, comd in cDeficit.iterrows(): #trab > cupos
    trad = comd['P17']
    pud = comd['Puestos']
    for idxsc, coms in cS.iterrows(): #trab < cupos
        tras = coms['P17']
        pus = coms['Puestos']
        if (tras/pus) < 0.9: #Tomando el deficit general 7/8=0.875
            for idxf, comf in Empresas[Empresas['COMUNA']==idxsc].iterrows():
                Empresas.at[idxf,'COMUNA'] = idxdc
                Empresas.at[idxf,'REGION'] = comd['REGION']
                pus = pus - comf['Trabajadores'] #Menos superavitaria
                cS.at[idxsc,'Puestos'] = pus
                pud = pud + comf['Trabajadores'] #se reduce el deficit
                cDeficit.at[idxdc,'Puestos'] = pud
                if (tras/pus) > 0.9:
                    break
                if pud==0:
                    continue
                if (trad/pud) < 1: #Todos van a quedar deficitaria
                    break
            if (trad/pud) < 1:
                break
print("Carga de Datos Empresas {0:f}".format(final-inicial))



inicial = time.perf_counter()
aUniversidades = aPath + "Matricula_U_2017.csv"
Universidades = pd.read_csv(aUniversidades, sep=";")
Universidades.rename(columns={"Region":"REGION","Comuna":"COMUNA"},inplace=True)
Univer = Universidades.groupby(["COMUNA","Jornada"]).agg(
{"Total":["sum"],
  "REGION":["max"]})
Univer = Univer.reset_index(level="Jornada")
final = time.perf_counter()
print("Carga de Datos Universidades {0:f}".format(final-inicial))

inicial = time.perf_counter()
aEducacion = aPath + "Matricula_SE_2017.csv"
Educacion = pd.read_csv(aEducacion, sep="\t")
Educacion.rename(columns={"COD_REG_RBD":"REGION","COD_COM_RBD":"COMUNA"},inplace=True)
final = time.perf_counter()
print("Carga de Datos Educacion {0:f}".format(final-inicial))

aPermisos = aPath + 'permisos-de-circulacion2017.csv'
inicial = time.perf_counter()
Vehiculos = pd.read_csv(aPermisos, sep=";")
final = time.perf_counter()


Vehiculos['Total'] = Vehiculos['Catalitico'] + Vehiculos['NoCatalitico']
Vehic = Vehiculos[Vehiculos["Destino"]==1].groupby('COMUNA').agg({'Total':'sum','REGION':'min'})


#%%

#Primero los datos llegan filtrados hasta aqui

personas["T_asignado"] = 0
personas["U_asignado"] = 0
personas["E_asignado"] = 0

per = personas[personas['REGION']==regionSelected]
#viv = viviendas[viviendas['REGION']==regionSelected]
#hog = hogares[hogares['REGION']==regionSelected]
res = Univer['REGION']==regionSelected
univ = Univer[res["max"]]
edu = Educacion[Educacion['REGION']==regionSelected]
firms = Empresas[Empresas['REGION']==regionSelected]
    

#%% Se asignan trabajadores a sus puestos de trabajo
#Se asignan los trabajadores de una comuna a los puestos de trabajos disponibles

inicial = time.perf_counter()
rPer = per[per['P17']==1].groupby('COMUNA').count()['P17'] #Personas por Comuna que trabajan
rPer.rename("Trabaj", inplace=True)
rFir =  firms.groupby('COMUNA').sum()['Trabajadores'] #Oferta de trabajo de las empresas
rFir.rename("Puestos", inplace=True)

capacidades = pd.concat([rPer,rFir],axis=1, sort=False)
capacidades["usadas"] = 0

#ATENCION:
# ****** Revisar 

#personas["T_asignado"] = 0
Empresas["asignados"] = 0
trabajo = pd.DataFrame([],columns=['id_p','id_f', 'pos'])
#trabajod = dict()
for idxc, datos in capacidades.iterrows():
    lista = []
    #Se construyen las capacidades
    for idx, firma in Empresas[Empresas["COMUNA"]==idxc].iterrows():
        for i in range(int(firma["Trabajadores"])):
            lista.append([0, idx, i])
    if len(lista)==0: 
        continue
    muestra = random.sample(range(len(lista)),len(lista))

    i = 0
    for idx, persona in personas[(personas["COMUNA"]==idxc) & (personas['P17']==1) & (personas['T_asignado']==0)].iterrows():
        # if persona['P17']==1 and persona["T_asignado"]==0:
        personas.at[idx,"T_asignado"] = 1 ##NOTAR QUE SE ASIGNA SOBRE EL GRAN DATAFRAME
        lista[muestra[i]][0] = idx
        i = i + 1
        if i == len(lista):
            break
    
    trabajo = pd.concat([trabajo, pd.DataFrame(lista,
                                columns=['id_p','id_f', 'pos'])],axis=0,sort=False)
    
    #Se asignan los que quedaron fuera
    # cuposlibres = trabajo[trabajo["id_p"]==0].index.tolist()
    
    # if len(cuposlibres)==0:
    #     continue #Se asignaron todos los puestos de trabajo disponibles
    
    # i = 0
    # for idx, persona in personas[(personas["REGION"]==regionSelected) & (personas['P17']==1) & (personas['T_asignado']==0)].iterrows(): ####MUY INEFICIENTE
    #     # if persona['P17']==1 and persona["T_asignado"]==0:
    #     trabajo.at[cuposlibres[i],"id_p"] = idx
    #     personas.at[idx,"T_asignado"] = 1 ##NOTAR QUE SE ASIGNA SOBRE EL GRAN DATAFRAME            
    #     i = i + 1
    #     if i == len(cuposlibres):
    #         break

    
    
final = time.perf_counter()
print("Tiempo para terminar el proceso de trabajo: {0:f} ".format(final-inicial))  


#%% Sistema de Educacion Superior

inicial = time.perf_counter()
#Personas por Comuna que estudian en educacion universitaria
#P13, es si asiste a la educacion formal
rPer = per[per['P13']==1 & per['P15'].between(11,14)].groupby('COMUNA').count()['P13'] 
rPer.rename("Estudiantes", inplace=True)
rUniv = univ.groupby('COMUNA').sum()['Total']["sum"] #Para obtener una serie
rUniv.rename("Matricula", inplace=True)
capacidades = pd.concat([rPer,rUniv],axis=1, sort=False).fillna(0)
capacidades["usadas"] = 0

#ATENCION:
# ****** Funciona bien para cuando las Matriculas son mayores que los Estudiantes

#personas["U_asignado"] = 0
Universidades["asignados"] = 0
edu_sup = pd.DataFrame([],columns=['id_p','id_u', 'pos'])
for idxc, datos in capacidades.iterrows():
    lista = []
    #Se construyen las capacidades
    for idx, carrera in Universidades[Universidades["COMUNA"]==idxc].iterrows():
        for i in range(int(carrera["Total"])):
            lista.append([0, idx, i])
    if len(lista)==0: 
        continue
    muestra = random.sample(range(len(lista)),len(lista))

    i = 0
    for idx, persona in personas[(personas["COMUNA"]==idxc) & (personas['P13']==1) & 
                                 (personas['P15'] >= 11) & (personas['P15'] <= 14) & (personas["U_asignado"]==0)].iterrows():
        # if persona['P13']==1 and 11 <= persona['P15'] <= 14 and persona["U_asignado"]==0:
        personas.at[idx,"U_asignado"] = 1 ##NOTAR QUE SE ASIGNA SOBRE EL GRAN DATAFRAME
        lista[muestra[i]][0] = idx
        i = i + 1
        if i == len(lista):
            break
    
    edu_sup = pd.concat([edu_sup, pd.DataFrame(lista,
                                columns=['id_p','id_u', 'pos'])],axis=0,sort=False)
    
    #Se asignan los que quedaron fuera
    cuposlibres = edu_sup[edu_sup["id_p"]==0].index.tolist()
    
    if len(cuposlibres)==0:
        continue #Se asignaron todos 

    
    i = 0
    for idx, persona in personas[(personas["REGION"]==regionSelected) & (personas['P13']==1) & 
                                 (personas['P15'] >= 11) & (personas['P15'] <= 14) & (personas["U_asignado"]==0)].iterrows(): ####MUY INEFICIENTE
        # if persona['P13']==1 and 11 <= persona['P15'] <= 14 and persona["U_asignado"]==0:
        edu_sup.at[cuposlibres[i],"id_p"] = idx
        personas.at[idx,"U_asignado"] = 1 ##NOTAR QUE SE ASIGNA SOBRE EL GRAN DATAFRAME
        i = i + 1
        if i == len(cuposlibres):
            break
    
final = time.perf_counter()
print("Tiempo para terminar el proceso de edu superior: {0:f} ".format(final-inicial))    
    
#%%
#Sistema de educación primara y secundaria
inicial = time.perf_counter()

rPer = per[per['P13']==1 & per['P15'].between(1,10)].groupby('COMUNA').count()['P13'] 
rPer.rename("Estudiantes", inplace=True)
rEdu = edu.groupby('COMUNA').sum()['MAT_TOTAL'] #Para obtener una serie
rEdu.rename("Matricula", inplace=True)
capacidades = pd.concat([rPer,rEdu],axis=1, sort=False).fillna(0)
capacidades["usadas"] = 0

#personas["E_asignado"] = 0
Educacion["asignados"] = 0
edu_basica = pd.DataFrame([],columns=['id_p','id_e', 'pos'])
for idxc, datos in capacidades.iterrows():
    lista = []
    #Se construyen las capacidades
    for idx, dependencia in Educacion[Educacion["COMUNA"]==idxc].iterrows():
        for i in range(int(dependencia["MAT_TOTAL"])):
            lista.append([0, idx, i])
    if len(lista)==0: 
        continue
    muestra = random.sample(range(len(lista)),len(lista))

    i = 0
    for idx, persona in personas[(personas["COMUNA"]==idxc) & (personas['P13']==1) & 
                                 (personas['P15']>=1) & (personas['P15'] <= 10) & (personas["E_asignado"]==0)].iterrows():    
    # for idx, persona in per[per["COMUNA"]==idxc].iterrows():
    #     if persona['P13']==1 and 1 <= persona['P15'] <= 10 and persona["E_asignado"]==0:
        personas.at[idx,"E_asignado"] = 1 ##NOTAR QUE SE ASIGNA SOBRE EL GRAN DATAFRAME
        lista[muestra[i]][0] = idx
        i = i + 1
        if i == len(lista):
            break
    
    edu_basica = pd.concat([edu_basica, pd.DataFrame(lista,
                                columns=['id_p','id_e', 'pos'])],axis=0,sort=False)
    
    #Se asignan los que quedaron fuera
    cuposlibres = edu_basica[edu_basica["id_p"]==0].index.tolist()
    if len(cuposlibres)==0:
        continue #Esto quiere decir que no hay cupos libres, y quedaron mas estudiantes que cupos
        
    i = 0
    for idx, persona in personas[(personas["REGION"]==regionSelected) & (personas['P13']==1) & 
                                 (personas['P15'] >=1 ) & (personas['P15'] <= 10) & (personas["E_asignado"]==0)].iterrows(): ####MUY INEFICIENTE: ####MUY INEFICIENTE
        # if persona['P13']==1 and 1 <= persona['P15'] <= 10 and persona["E_asignado"]==0:
        edu_basica.at[cuposlibres[i],"id_p"] = idx
        personas.at[idx,"E_asignado"] = 1 ##NOTAR QUE SE ASIGNA SOBRE EL GRAN DATAFRAME
        i = i + 1
        if i == len(cuposlibres):
            break

    
final = time.perf_counter()
print('Tiempo para terminar el proceso de edu basica: {0:2f} '.format(final-inicial))    

#%%
#Ahora se construyen diccionarios de todas las estructuras de datos
#trabajo = pd.DataFrame([],columns=['id_p','id_f', 'pos'])
#edu_sup = pd.DataFrame([],columns=['id_p','id_u', 'pos'])
#edu_basica = pd.DataFrame([],columns=['id_p','id_e', 'pos'])
lista = []
edu_basicad = dict()
for index, relacion in edu_basica.iterrows():
    if relacion['pos']==0:
        edu_basicad[relacion['id_e']] = lista               
        lista = []
    lista.append(relacion['id_p'])                        

#Se hace el último grupo
edu_basicad[relacion['id_e']] = lista


##Educacion superior            
lista = []
edu_supd = dict()
for index, relacion in edu_sup.iterrows():
    if relacion['pos']==0:
        if len(lista)>0:
            edu_supd[relacion['id_u']] = lista                
            lista = []
    lista.append(relacion['id_p'])

#Se hace el último grupo
edu_supd[relacion['id_u']] = lista

##trabajo            
lista = []
trabajod = dict()
for index, relacion in trabajo.iterrows():
    if relacion['pos']==0:
        if len(lista)>0:
            trabajod[relacion['id_f']] = lista    
            lista = []
    lista.append(relacion['id_p'])

#Se hace el último grupo
trabajod[relacion['id_f']] = lista          


#%% Distribucion de Transporte entre los hogares

inicial = time.perf_counter()

rHogar = hogares[hogares['REGION']==regionSelected].groupby('COMUNA').count()['NHOGAR'] 
rHogar.rename('Hogares', inplace=True)
rVehic = Vehic[Vehic['REGION']==regionSelected].groupby('COMUNA').sum()['Total'] #Para obtener una serie
rVehic.rename("Autos", inplace=True)
capacidades = pd.concat([rHogar,rVehic],axis=1, sort=False).fillna(0)

hogares['conAuto'] = 0
for idxc, datos in capacidades.iterrows():
    hogaresconauto = int(min((datos['Autos'] * 0.9),datos['Hogares']))
    
    muestra = random.sample(range(hogaresconauto),hogaresconauto)

    indices = hogares[hogares['COMUNA']==idxc]
    for i in range(hogaresconauto):
        idx = indices.index[i]
        hogares.at[idx,"conAuto"] = 1 ##NOTAR QUE SE ASIGNA SOBRE EL GRAN DATAFRAME
      
final = time.perf_counter()
print('Tiempo para terminar la asignación de autos: {0:2f} '.format(final-inicial))    
    


#%%


################################################################
#def preparaEstructurasComplementarias(conSchool):
    

if Actualizar==True:
    hogares['ID'] = (hogares['ID_ZONA_LOC']+100000).astype(str)+(hogares['NVIV']+1000).astype(str)+hogares['NHOGAR'].astype(str)
    personas['ID'] = (personas['ID_ZONA_LOC']+100000).astype(str)+(personas['NVIV']+1000).astype(str)+personas['NHOGAR'].astype(str)
hogares.set_index('ID')
personas.set_index('ID')
Comunas = hogares.groupby('COMUNA').agg({'REGION':'min'})
print('Indices Establecidos en Personas y Hogares')
# #hogares['ID'] = hogares[['ID_ZONA_LOC', 'NVIV', 'NHOGAR']].agg('-'.join, axis=1)

#%% Estructura de Probabilidad

p = 0.01 #La probabilida de progresión de un bebé
oddratio = p / (1-p)

personas['Pprogreso'] = oddratio * (1.08)**personas['P09']/(1 + oddratio * (1.08)**personas['P09'])

#%%
print('Creando la estructura de pasajeros y de educacion')
if conSchool == True:
    Sistema = "Con Escuelas"
    l_hogares = []
    usuariosTP = {}
    for idxc, comuna in Comunas[Comunas['REGION']==regionSelected].iterrows():  
        perss = personas[personas['COMUNA']==idxc]
        pasajeros = []
        for idxh, hogar in hogares[hogares['COMUNA']==idxc].iterrows():
            idHogar = hogar['ID']        
            grupo = perss[perss['ID']==idHogar].index
            l_hogares.append(grupo) #Esta tiene la lista de personas en cada hogar
            if hogar['conAuto'] == 0: #Si no tienen auto
                pasajeros.extend(grupo.tolist())
                usuariosTP[idxc] = pasajeros
else:

    Sistema = "Sin Escuelas"
    l_hogares = []
    usuariosTP = {}
    for idxc, comuna in Comunas[Comunas['REGION']==regionSelected].iterrows():  
        perss = personas[personas['COMUNA']==idxc]
        pasajeros = []
        for idxh, hogar in hogares[hogares['COMUNA']==idxc].iterrows():
            idHogar = hogar['ID']        
            grupo = perss[perss['ID']==idHogar].index
            l_hogares.append(grupo) #Esta tiene la lista de personas en cada hogar
            if hogar['conAuto'] == 0: #Si no tienen auto
                for idpersona in grupo:
                    if perss.loc[idpersona,'P13']!=1 or perss.loc[idpersona,'P17']!=5:
                        pasajeros.append(idpersona)
        usuariosTP[idxc] = pasajeros
             
####################################################            
#def grabaDatos():
losdatos = {'personas': personas, "hogares":hogares, "edu_basica":edu_basicad, "edu_sup":edu_supd,
    "trabajo":trabajod, "regionSelected":regionSelected, "Comunas":Comunas, 
    "usuariosTP":usuariosTP,"l_hogares":l_hogares}
if conSchool == True:
    archivo = "datosinicialesconSchool.pickle"
else:
    archivo = "datosinicialessinSchool.pickle"

with open(archivo, 'wb') as handle:
    pickle.dump(losdatos, handle, protocol=pickle.HIGHEST_PROTOCOL)
    
if Actualizar==True:
    hogares.to_csv(r'Hogares_Creado0707.csv')
    personas.to_csv(r'Personas_Creado0707.csv')
    
final = time.perf_counter()
print('Tiempo para terminar TODO {0:f}'.format(final-GranInicial))    

