import numpy as np

def conv_arr(arr: np.ndarray, kernel_size: int):
    '''Suaviza o array `arr` realizando uma convolução com
    um kernel de `kernel_size` 1's. Apenas retorna os elementos
    em que o kernel totalmente intersecta `arr`.
    '''
    # num_points = arr.size - kernel_size
    # new_arr = np.zeros(num_points, dtype=arr.dtype)
    # for i in range(num_points):
    #     new_arr[i] = arr[i:i+kernel_size].sum()
    # return new_arr
    return np.convolve(arr, np.ones(kernel_size, dtype=float), "valid")


def mean_arr(arr: np.ndarray, kernel_size: int, r=1):
    '''Suaviza o array `arr` realizando a média a cada `kernel_size`
    elementos se `r=1`, caso contrário, o tamanho da janela da média aumenta 
    a cada iteração por um fator `r`, ou seja, o i-ésimo elemento é

    ```    
    start_id = kernel_size * r**i
    end_id = kernel_size * r**(i+1) 
    arr[start_id, end_id].sum() / (end_id - start_id)
    ```
    '''
    if r == 1:
        result = conv_arr(arr, kernel_size)
        result = result[np.arange(result.size) % kernel_size == 0] / kernel_size
        return result
    else:
        new_arr = []
        kernel_size_round = round(kernel_size)
        start_id = 0
        end_id = start_id + kernel_size
        while end_id <= arr.size:
            new_arr.append(arr[start_id:end_id].sum()/kernel_size_round)
            start_id = end_id
            kernel_size = r*kernel_size
            kernel_size_round = round(kernel_size)
            end_id += kernel_size_round

        return np.array(new_arr)


if __name__ == "__main__":
    a = np.array([1,2,3,4,5])
    
    r = conv_arr(a, 3)
    comp = r == np.array([6, 9, 12])
    print("conv test:", comp.all())

    r = mean_arr(a, 2)
    comp = r == np.array([3/2, 7/2])
    print("mean test:", comp.all())