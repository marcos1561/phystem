import numpy as np
from typing import Callable

import phystem.utils.progress as progress_lib

def list_to_ndarray(*lists) -> list[np.ndarray]:
    ndarrays = []
    for l in lists:
        ndarrays.append(np.array(l))
    
    return ndarrays


class ButcherTable:
    '''
    Classe que representa uma tabela de Butcher.
    '''
    def __init__(self, q_values: list, a_values: list[int]) -> None:
        self.order = len(q_values) + 1

        self.q_values = np.zeros((self.order, self.order))
        self.p_values = np.zeros(self.q_values.shape[0])
        self.a_values = np.array(a_values)
        
        for i in range(1, self.order):
            self.q_values[i, :i] = q_values[i-1] 
            self.p_values[i] = self.q_values[i].sum()

    def __str__(self) -> str:
        precision = 2
        number_space = 2 + precision

        number_separator = "  "

        def get_number_str(n: int):
            if n == 0:
                return "0".center(number_space)
            return f"{n:.{precision}f}".ljust(number_space)

        table_str = ""
        for i in range(self.order):
            line = get_number_str(self.p_values[i])
            line += " | "

            for q_i in self.q_values[i]:
                line += get_number_str(q_i) + number_separator
            line += "\n"
            
            table_str += line
        
        table_str += "-"*len(line) + "\n"

        last_line = " "*number_space + " | "
        for a in self.a_values:
            last_line += get_number_str(a) + number_separator
        
        table_str += last_line
        return table_str

class MethodButcherTable:
    '''
    Coleção de algumas tabelas de Butcher.
    '''
    rk2_ralston = ButcherTable(
        q_values = [
            [2/3],
        ],
        a_values = [1/4, 3/4])
    
    rk2_heun = ButcherTable(
        q_values = [
            [1],
        ],
        a_values = [1/2, 1/2])
    
    rk2_mid_point = ButcherTable(
        q_values = [
            [1/2],
        ],
        a_values = [0, 1])
    
    rk4_3_8 = ButcherTable(
        q_values = [
            [1/3],
            [-1/3, 1],
            [1, -1, 1]],
        a_values = [1/8, 3/8, 3/8, 1/8])

    rk4_classico = ButcherTable(
        q_values = [
            [1/2],
            [0, 1/2],
            [0, 0, 1]],
        a_values = [1/6, 1/3, 1/3, 1/6])


def rk45(x0: np.ndarray, func: Callable[[np.ndarray], np.ndarray], 
        tf: float, dt: float, tol=1e-4, steps_to_update=5):
    x_list = [x0]
    t_list = [0]
    dt_list = [dt]

    butcher_table = ButcherTable(
        q_values=[
            [1/4],
            [3/32, 9/32],
            [1932/2197, -7200/2197, 7296/2197],
            [439/216, -8, 3680/513, -845/4104],
        ],
        a_values = [25/216, 0, 1408/2565, 2197/4101, -1/5]
    )

    q_values_6 = np.array([-8/27, 2, -3544/2565, 1859/4104, -11/40])
    a_values_6 = np.array([16/135, 0, 6656/12825, 28561/56430, -9/50, 2/55])
    p_value_6 = 1/2

    count = 0
    while t_list[-1] < tf:
        if count % steps_to_update == 0 and len(x_list) > 2:
            x1 = x_list[-2]
            x2 = x_list[-1]

            t1 = t_list[-2]

            k_average = k_matrix.dot(q_values_6)
            k_6 = func(x1 + k_average*dt, t1 + p_value_6 * dt)

            x2_better = x1 + (k_matrix.dot(a_values_6[:-1]) + k_6 * a_values_6[-1])* dt

            erro_c = np.linalg.norm(x2_better - x2)
            dt_scale = (tol/erro_c)**(1/(butcher_table.order+1))

            if dt_scale < .5:
                dt_scale = .5
            elif dt_scale > 2:
                dt_scale = 2

            dt *= dt_scale
            
        current_x = x_list[-1]
        t = t_list[-1]
        
        # Para apenas ser executado um passo temporal
        # o tempo final é setado para dt/2, 
        (next_x, _), k_matrix = rk_geral(current_x, func, dt/2, dt, butcher_table, get_k=True)
        next_x = next_x[-1]

        x_list.append(next_x)
        t_list.append(t + dt)
        dt_list.append(dt)
        count += 1
    return list_to_ndarray(x_list, t_list, dt_list)
   
def rk_geral(x0: np.ndarray, func: Callable[[np.ndarray], np.ndarray], 
    tf: float, dt: float, butcher_table: ButcherTable, get_k=False, show_progress=False):
    '''
    Resolve o seguinte sistema de ode's

    dx/dt = func(x, t)

    Utilizando o método de Runge Kutta especificado na tabela de Butcher dada.

    Parâmetros:
    -----------
    x0:
        Vetor com os valores inicias das variáveis a serem integradas.

    func:
        Função que calcula a derivada em relação ao tempo de x. 
        
        Os parâmetros dessa função são:

        x:
            Vetor com o valor das variáveis
        t:
            Tempo
            
        E seu retorno é:

        Vetor com as derivadas temporais de x, na mesma ordem de x.

    butcher_table:
        Tabela de Butcher que será implementada.
    
    Retorno:
    --------
    x: np.ndarray
        Matriz com o valor das variáveis em cada instante de tempo. A i-ésima linha
        de x é o valor das variáveis no instante i. A ordem das variáveis é a mesma 
        em x0.

    t: list
        Instantes de tempos correspondentes em x.        
    '''
    x_list = [x0]
    t_list = [0]

    k_matrix = np.zeros((x0.size, butcher_table.order))

    progress = progress_lib.Continuos(tf)

    while t_list[-1] < tf:
        if show_progress:
            progress.update(t_list[-1])

        current_x = x_list[-1]
        t = t_list[-1]

        k_matrix[:,0] = func(current_x, t)

        for i in range(1, butcher_table.order):
            k_average = k_matrix[:,:i].dot(butcher_table.q_values[i][:i])
            k_matrix[:, i] = func(current_x + k_average*dt, t + butcher_table.p_values[i] * dt)

        next_x = current_x + k_matrix.dot(butcher_table.a_values) * dt

        x_list.append(next_x)
        t_list.append(t + dt)

    result = list_to_ndarray(x_list, t_list)
    if get_k:
        return result, k_matrix
    else:
        return result

def rk_geral_pv(x0: np.ndarray, func: Callable[[np.ndarray], np.ndarray], 
    tf: float, dt: float, butcher_table: ButcherTable, 
    butcher_table_better=MethodButcherTable.rk4_classico, tol=1e-4, steps_to_update=5,
    show_progress=True):
    '''
    Implementa o método de passo variável para o RK especificado em
    `butcher_table`, corrigido pelo RK especificado em `butcher_table_better`.
    
    Parâmetros:
    -----------

    steps_to_update:
        Quantidade de passos para dar antes de atualizar dt.
    '''
    x_list = [x0]
    t_list = [0]
    dt_list = [dt]

    progress = progress_lib.Continuos(tf)

    count = 0
    while t_list[-1] < tf:
        if show_progress:
            progress.update(t_list[-1])

        if count % steps_to_update == 0 and len(x_list) > 2:
            x1 = x_list[-2]
            x2 = x_list[-1]

            # Para apenas ser executado um passo temporal
            # o tempo final é setado para dt/2, 
            x2_better, _ = rk_geral(x1, func, dt/2, dt, butcher_table_better)
            x2_better = x2_better[1]

            erro_c = np.linalg.norm(x2_better - x2)
            dt_scale = (tol/erro_c)**(1/(butcher_table.order+1))

            if dt_scale < .5:
                dt_scale = .5
            elif dt_scale > 2:
                dt_scale = 2

            dt *= dt_scale
        
        current_x = x_list[-1]
        t = t_list[-1]
        
        # Para apenas ser executado um passo temporal
        # o tempo final é setado para dt/2, 
        next_x, _ = rk_geral(current_x, func, dt/2, dt, butcher_table)
        next_x = next_x[-1]

        x_list.append(next_x)
        t_list.append(t + dt)
        dt_list.append(dt)
        count += 1

    return list_to_ndarray(x_list, t_list, dt_list)

if __name__ == "__main__":
    b = ButcherTable([1,2,3], [4, 10, 2])

    print(b)

    # def func(x, t):
    #     return np.array([1 + x**2])

    # x0 = np.array([0])
    # tf = 1.5
    # dt = 0.01
    # tol = 1e-4

    # result = rk45(x0, func, tf, dt, tol)