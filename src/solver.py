import time
from amplpy import AMPL, ampl_notebook

workerAmpl = None

def solveInstance(instance, model, limitVar = "epsilon", limitValue = 1e20):
    ampl = AMPL()
    ampl.eval("reset;")
    ampl.eval(model)
    ampl.eval(instance)
    ampl.param[limitVar] = limitValue
    ampl.setOption("solver", "gurobi")
    #ampl.option["gurobi_options"] = "NonConvex=2 MIPGap=1e-8 FeasTol=1e-9 BarConvTol=1e-9"
    ampl.option["gurobi_options"] = "NonConvex=2 MIPGap=1e-9" 
    #ampl.setOption("solver", "knitro")
    #ampl.option["knitro_options"] = "ms_enable=1"
    #ampl.setOption("solver", "baron")
    #ampl.setOption("solver", "cplex")

    ampl.solve()
    
    transp = ampl.getValue("CostoTransp")
    infra = ampl.getValue("CostoInfra")
    print(f"Cds abiertos: {ampl.getData("Z")} ")
    ampl.close()
    return transp, infra


def solveEpsilon(instance, model, epsilonValue):
    ampl = AMPL()
    ampl.eval("reset;")
    ampl.eval(model)
    ampl.eval(instance)
    ampl.param["epsilon"] = epsilonValue
    ampl.setOption("solver", "gurobi")
    
    ampl.option["gurobi_options"] = "NonConvex=2 MIPGap=1e-9" 
    #ampl.option["gurobi_options"] = "NonConvex=2"
    #ampl.setOption("solver", "knitro")
    #ampl.setOption("solver", "baron")
    #ampl.setOption("solver", "cplex")
    #ampl.option["knitro_options"] = "ms_enable=1"
    
    ampl.solve()
    
    solveResult = ampl.getValue("solve_result")
    if solveResult == "solved":
        transp = ampl.getValue("CostoTransp")
        infra = ampl.getValue("CostoInfra")

        y_vals = ampl.getVariable("Z").getValues().toDict()
        cds_abiertos = [cd for cd, abierto in y_vals.items() if abierto > 0.5]
        
        ampl.close()
        return transp, infra, cds_abiertos
    
    ampl.close()
    return None, None, None

