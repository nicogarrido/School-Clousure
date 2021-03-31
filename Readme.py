#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul  6 23:46:16 2020

@author: Disco
"""

La forma de correr una simulación es en dos etapas:
    
1. Primero hay que preparar los datos para ser utilizados. Esto se hace mediante el programa "PreparaDatos.py"

Este código debe especificarse si es con o sin colegios y con que región se trabajará
Hay que estar atento a la variable "Actualizar" que refresca "Todos los datos" y se debe poner la fecha 
en el nombre del archivo
La salida de este programa es el archivo "datosinicialesconSchool.pickle" y "datosinicialessinSchool.pickle"


2. Luego se puede correr el archivo Modelo.py, que se encarga de realizar las simulaciones

El archivo "datosinicialesd.pickle" debe estar en el mismo directorio que Modelo.py