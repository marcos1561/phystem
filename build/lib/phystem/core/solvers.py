from abc import ABC, abstractmethod
import numpy as np

class SolverCore(ABC):
    '''Responsável pela integração do sistema.'''
    def __init__(self) -> None:
        self.dt: float
        self.time: float

    @abstractmethod
    def update(self) -> None:
        '''Deve avançar o sistema em um passo temporal'''
        pass

class ButcherTable:
    '''Classe que representa uma tabela de Butcher.'''
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

class ButcherTableCol:
    '''Coleção de algumas tabelas de Butcher.'''
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

class RkSolver(SolverCore):
    def __init__(self, x0: np.ndarray, dt: float, butcher_table=ButcherTableCol.rk4_classico) -> None:
        self.butcher_table = butcher_table
        
        self.x = x0

        self.dt = dt
        self.time = 0
        
        self.k_matrix = np.zeros((self.x.size, self.butcher_table.order))

    @abstractmethod
    def calc_derivatives(self, x: np.ndarray, t: float) -> np.ndarray:
        pass

    def update(self) -> None:
        k_matrix = self.k_matrix

        k_matrix[:,0] = self.calc_derivatives(self.x, self.time)
        for i in range(1, self.butcher_table.order):
            k_average = k_matrix[:,:i].dot(self.butcher_table.q_values[i][:i])
            k_matrix[:, i] = self.calc_derivatives(self.x + k_average * self.dt, self.time + self.butcher_table.p_values[i] * self.dt)

        self.x[:] = self.x + k_matrix.dot(self.butcher_table.a_values) * self.dt

        self.time += self.dt