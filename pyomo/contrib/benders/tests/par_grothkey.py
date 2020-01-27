from pyomo.contrib.benders.benders_cuts import BendersCutGenerator
import pyomo.environ as pe
import numpy as np

def test_grothey():
    def create_master():
        m = pe.ConcreteModel()
        m.y = pe.Var(bounds=(1, None))
        m.eta = pe.Var(bounds=(-10, None))
        m.obj = pe.Objective(expr=m.y ** 2 + m.eta)
        return m

    def create_subproblem(master):
        m = pe.ConcreteModel()
        m.x1 = pe.Var()
        m.x2 = pe.Var()
        m.y = pe.Var()
        m.obj = pe.Objective(expr=-m.x2)
        m.c1 = pe.Constraint(expr=(m.x1 - 1) ** 2 + m.x2 ** 2 <= pe.log(m.y))
        m.c2 = pe.Constraint(expr=(m.x1 + 1) ** 2 + m.x2 ** 2 <= pe.log(m.y))

        complicating_vars_map = pe.ComponentMap()
        complicating_vars_map[master.y] = m.y

        return m, complicating_vars_map

    m = create_master()
    master_vars = [m.y]
    m.benders = BendersCutGenerator()
    m.benders.set_input(master_vars=master_vars, tol=1e-8)
    m.benders.add_subproblem(subproblem_fn=create_subproblem,
                             subproblem_fn_kwargs={'master': m},
                             master_eta=m.eta,
                             subproblem_solver='ipopt', )
    opt = pe.SolverFactory('ipopt')

    for i in range(30):
        res = opt.solve(m, tee=False)
        cuts_added = m.benders.generate_cut()
        if len(cuts_added) == 0:
            break

    assert round(m.y.value - 2.721381, 4) == 0
    assert round(m.eta.value - (-0.0337568), 4) == 0


if __name__ == '__main__':
    test_grothey()
