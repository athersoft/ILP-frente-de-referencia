import sys
import numpy as np
from src.model import mInfrastructure, mTransport, lexInfrastructure, lexTransport
from src.utils import download_data, calcularHipervolumen, saveEpsilonFront, loadInstance
from src.solver import solveInstance, solveEpsilon
import matplotlib.pyplot as plt
import multiprocessing as mp
import time
import math

#Instancias
#Generadas por diferentes modelos LLM 

N_CORES = 15       #Número de nucleos
LICENSE_UUID = "b84215a6-2e17-4c6f-8d78-2019e0f3c0ff" #Mi licencia de AMPL, no tocar

if __name__ == "__main__":

    instancesToEvaluate = ["30x15-0","30x15-1","30x15-3","30x15-5","50x25-0","50x25-1","50x25-3","50x25-5"]

    for instance in instancesToEvaluate:
        #DATA_URL = instance #Acá se selecciona la instancia que se evaluará
        DATA_URL = ""
        name = instance
        #currentInstance = download_data(DATA_URL)
        currentInstance = loadInstance(name)
        if not currentInstance:
            sys.exit(1)

        startTimeLex = time.time()

        transportMin, aux = solveInstance(currentInstance, model = lexTransport, limitVar= "minInfra")
        aux, infraMax = solveInstance(currentInstance, model = lexInfrastructure, limitVar = "minTransp", limitValue = math.ceil(transportMin))
        
        aux, infraMin = solveInstance(currentInstance, model = lexInfrastructure, limitVar="minTransp")
        transportMax, aux = solveInstance(currentInstance, model = lexTransport, limitVar = "minInfra", limitValue = math.ceil(infraMin))

        endTimeLex = time.time() 
        tiempoLex = endTimeLex - startTimeLex

        steps = 10
        paretoX = []
        paretoY = []
        paretoCDs = []

        epsilonSteps1 = np.linspace(infraMin, infraMax, steps)
        
        startTimeEp1 = time.time()
        for step in epsilonSteps1:
            transportCost, infraCost, cdsAbiertos = solveEpsilon(currentInstance, mTransport, step)
            if transportCost is not None:
                paretoX.append(transportCost)
                paretoY.append(infraCost)
                paretoCDs.append(cdsAbiertos)
        endTimeEp1 = time.time()
        tiempoEp1 = endTimeEp1 - startTimeEp1

        epsilonSteps2 = np.linspace(transportMin, transportMax, steps)
        
        startTimeEp2 = time.time()
        for step in epsilonSteps2:
            transportCost, infraCost,cdsAbiertos = solveEpsilon(currentInstance, mInfrastructure, step)
            if infraCost is not None:
                paretoX.append(transportCost)
                paretoY.append(infraCost)
                paretoCDs.append(cdsAbiertos)
        endTimeEp2 = time.time() 
        tiempoEp2 = endTimeEp2 - startTimeEp2

        tiempoTotal = tiempoLex + tiempoEp1 + tiempoEp2

        puntosUnicos = {}
        for i in range(len(paretoX)):
            coord = (round(paretoX[i], 2), round(paretoY[i], 2))
            if coord not in puntosUnicos:
                puntosUnicos[coord] = (paretoX[i], paretoY[i], paretoCDs[i])

        sortedPoints = sorted(puntosUnicos.values(), key=lambda x: x[0])

        paretoX = [p[0] for p in sortedPoints]
        paretoY = [p[1] for p in sortedPoints]
        paretoCDs = [p[2] for p in sortedPoints]

    #####################################################################################
        reporte = []
        reporte.append("==================================================")
        reporte.append("      REPORTE DE EJECUCIÓN EPSILON-CONSTRAINT     ")
        reporte.append("==================================================")
        reporte.append(f"URL Instancia Evaluada: {name}\n")

        reporte.append("--- TIEMPOS DE EJECUCIÓN ---")
        reporte.append(f"Tiempo Lexicográficos : {tiempoLex:.4f} s")
        reporte.append(f"Tiempo Epsilon 1      : {tiempoEp1:.4f} s")
        reporte.append(f"Tiempo Epsilon 2      : {tiempoEp2:.4f} s")
        reporte.append(f"Tiempo Total          : {tiempoTotal:.4f} s\n")

        reporte.append("--- PUNTOS LEXICOGRÁFICOS EXTREMOS ---")
        reporte.append(f"Nadir (Teórico)   : Transp={transportMax:.2f}, Infra={infraMax:.2f}")
        reporte.append(f"Transporte Mínimo : Transp={transportMin:.2f}, Infra={infraMax:.2f}")
        reporte.append(f"Infraestructura Mín: Transp={transportMax:.2f}, Infra={infraMin:.2f}\n")

        reporte.append(f"--- FRENTE DE PARETO ({len(paretoX)} puntos únicos) ---")
        for i in range(len(paretoX)):
            t_val = paretoX[i]
            i_val = paretoY[i]
            cds = paretoCDs[i]
            reporte.append(f"  Punto {i+1}: Transp={t_val:.2f}, Infra={i_val:.2f} | CDs Abiertos: {cds}")

        asignacion = f"transportMin, transportMax, infraMin, infraMax, paretoX, paretoY = {transportMin}, {transportMax}, {infraMin}, {infraMax}, {paretoX}, {paretoY}"
        
        reporte.append("\nASIGNACIÓN")
        reporte.append(asignacion)

        nombreArchivo = f"Resultados_{instance.split('/')[-1]}_{time.time()}.txt"
        with open(nombreArchivo, "w", encoding="utf-8") as f:
            f.write("\n".join(reporte))

        print(f"\n*** Los resultados han sido guardados exitosamente en '{nombreArchivo}' ***\n")

    ###############################################################################################
        plt.plot(paretoX, paretoY, marker='o', linestyle='-', color='green', label="Frente Epsilon")
        plt.scatter([transportMin, transportMax], [infraMax, infraMin], c=['blue', 'red'], zorder=5)
        
        plt.xlabel("Costo Transporte")
        plt.ylabel("Costo Infraestructura")
        plt.grid(True, linestyle=':', alpha=0.7)
        plt.legend()
        plt.tight_layout()
        plt.savefig(f"{instance.split('/')[-1]}.png", dpi=300, bbox_inches='tight')
        #plt.show()
        plt.close()
        

        epsilonPoints = [(x, y) for x, y in zip(paretoX, paretoY)]
        hipervolumenEpsilon = calcularHipervolumen(epsilonPoints, transportMin, transportMax, infraMin, infraMax)
        dataToSave = {
            "time": tiempoTotal,
            "hv": hipervolumenEpsilon,
            "transMin": transportMin,
            "transMax": transportMax,
            "infraMin": infraMin,
            "infraMax": infraMax,
            "paretoX": paretoX, 
            "paretoY": paretoY  
        }
        jsonName = f"{instance.split('/')[-1]}.json"
        saveEpsilonFront(jsonName, name, dataToSave)

    