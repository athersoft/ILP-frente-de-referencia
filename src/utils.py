import requests
import re
import matplotlib.pyplot as plt

def download_data(url):
    print(f"Descargando archivo .dat desde Gist...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error descargando: {e}")
        return None

def parse_num_cds(ampl_data):
    match = re.search(r'set\s+I\s*:=\s*(.*?);', ampl_data, re.DOTALL | re.IGNORECASE)
    if match:
        content = match.group(1)
        cdList_ids = content.split()
        return len(cdList_ids)
    return 0

import json
import os
import sys

def saveEpsilonFront(filePath, instanceUrl, epsilonData):
    allData = {}

    if os.path.exists(filePath):
        with open(filePath, 'r') as file:
            allData = json.load(file)

    instanceEntry = {
        "metadata": {
            "executionTime": epsilonData['time'],
            "hypervolume": epsilonData['hv'],
        },
        "lexicographicPoints": {
            "infraMin": {"transp": epsilonData['transMax'], "infra": epsilonData['infraMin']},
            "infraMax": {"transp": epsilonData['transMin'], "infra": epsilonData['infraMax']}
        },
        "paretoFront": {
            "x": epsilonData['paretoX'], # Transport
            "y": epsilonData['paretoY']  # Infrastructure
        },
        "info":{
            "simplexIterations" : epsilonData['simplexIterations'],
            "branchNodes" : epsilonData['branchNodes']
        }

    }

    allData[instanceUrl] = instanceEntry

    with open(filePath, 'w', encoding='utf-8') as f:
        json.dump(allData, f, indent=4)

    print(f" --- Datos de Epsilon actualizados exitosamente en '{filePath} --- '")

def loadEpsilonResults(filePath, instanceUrl):
    if not os.path.exists(filePath):
        return None

    try:
        with open(filePath, 'r', encoding='utf-8') as f:
            allResults = json.load(f)
            
        if instanceUrl in allResults:
            print(f" --- Resultados previos encontrados para: {instanceUrl} --- ")
            data = allResults[instanceUrl]
            
            return {
                'time': data['metadata']['executionTime'],
                'hv': data['metadata']['hypervolume'],
                'transMin': data['lexicographicPoints']['infraMax']['transp'],
                'transMax': data['lexicographicPoints']['infraMin']['transp'],
                'infraMin': data['lexicographicPoints']['infraMin']['infra'],
                'infraMax': data['lexicographicPoints']['infraMax']['infra'],
                'paretoX': data['paretoFront']['x'],
                'paretoY': data['paretoFront']['y']
            }
    except Exception as e:
        print(f"Error al cargar resultados previos: {e}")
        
    return None

def calcularHipervolumen(puntos, minX, maxX, minY, maxY):
    if len(puntos) == 0:
        return 0.0
        
    rangoX = maxX - minX if maxX > minX else 1.0
    rangoY = maxY - minY if maxY > minY else 1.0
    
    puntos_norm = []
    for p in puntos:
        nx = (p[0] - minX) / rangoX
        ny = (p[1] - minY) / rangoY
        puntos_norm.append((nx, ny))
        
    sortedPoints = sorted(puntos_norm, key=lambda p: p[0])
    
    hipervolumen = 0.0
    
    refX_norm = 1.0 
    refY_norm = 1.0
    
    for i in range(len(sortedPoints)):
        xx = sortedPoints[i][0]
        yy = sortedPoints[i][1]
        
        if xx <= refX_norm and yy <= refY_norm:
            if i + 1 < len(sortedPoints):
                nextX = sortedPoints[i + 1][0]
            else:
                nextX = refX_norm
                
            width = nextX - xx
            height = refY_norm - yy
            
            if width > 0 and height > 0:
                area = width * height
                hipervolumen += area
            
    return hipervolumen

def loadInstance(name):

    if not name.endswith(".dat"):
        fileName = f"{name}.dat"
    else:
        fileName = name
        
    folderName = "instances"
    filePath = os.path.join(folderName, fileName)
    
    try:
        with open(filePath, 'r', encoding='utf-8') as fileObject:
            fileContent = fileObject.read()
        return fileContent
    except FileNotFoundError:
        print(f"Error: El archivo '{fileName}' no se encontró en la carpeta '{folderName}'.")
        return None
    except Exception as errorObject:
        print(f"Error inesperado al leer la instancia: {errorObject}")
        return None