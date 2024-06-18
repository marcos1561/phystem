---
---

* This will become a table of contents (this text will be scrapped).
{:toc}

# Ring (Anéis ativos)
No atual momento, esse é o sistema mais desenvolvido. O seu `Solver` é completamente implementado em `C++` e loops foram paralelizados quando
possível para obter mais desempenho. Duas geometrias estão implementadas

- Bordas periódicas
- Fluxo de Stokes

Existem 4 modos de execução implementados

- `RealTime`: Renderização em tempo real
- `Collect`: Apenas coleta de dados (sem renderização)
- `Replay`: Replay de dados salvos
- `Video`: Geração de vídeo em tempo real ou de dados salvos

Vários coletores e calculadores já implementados, sendo alguns

1. Coletores:
    1. `CheckpointCol`: Utilizado para gerar um checkpoint que podem ser carregado em outras simulações.
    2. `SnapshotsCol`: Utilizado para periodicamente coletar "snapshots" de uma simulação. Ótimo
        para gerar dados que podem ser visualizados no modo de execução `Replay` ou transformados em
        vídeo no modo `Video`.
    3. `DeltaCol`, `DenVelCol`, `CreationRateCol`: Coletores de quantidades de interesse cujas explicações estão fora de escopo do presente texto. Mais detalhes podem ser encontrados nas suas respectivas documentações no código.
    4. `ColManager`: Gerenciador de múltiplos coletores. Útil para utilizar mais de um coletor na mesma simulação. 

2. Calculadores: Cada coletor no item 3 também possui seu calculador.

Todos os coletores e calculadores tomam vantagem do sistema de auto-salvamento presente no phystem. É possível abruptamente interromper uma simulação coletando dados, ou uma análise de dados, e continuar sua execução do último ponto salvo. 

# Como rodar uma simulação?
Para rodar uma simulação precisamos instanciar as configurações necessárias. Nesta seção será dado um exemplo concreto de um possível conjunto de configurações com alguns comentários sobre as mesmas.

> ⚠️ 
>
> A partir de agora é assumido a seguinte importação `from phystem.systems import ring`.

## Configurações da dinâmica do sistema
Controlam elementos como constantes das forças, diâmetro das partículas, etc. Uma possível escolha é a seguinte:

```python
dynamic_cfg = ring.configs.RingCfg(
    spring_k=8,
    spring_r=0.7,
    
    area_potencial="target_area_and_format",
    k_area=2,
    p0=3.5449077018, # Círculo
    
    k_format=0.1,
    p0_format=3.5449, # Círculo
    
    k_invasion=10,

    diameter  = 1,
    max_dist  = 1 + 0.1666,
    rep_force = 12,
    adh_force = 0.75,
    
    relax_time=1,
    mobility=1,
    vo=1,
    
    trans_diff=0.1,
    rot_diff=1,
)
```

## Configurações do espaço
Configurações do espaço físico em que se encontram os anéis. Sempre é um retângulo. Ex:

```python
space_cfg = ring.configs.SpaceCfg(
    height=30,
    length=30,
)
```

## Configurações do estado inicial
Configurações passados para o `Creator`, o objeto responsável por criar a configuração
inicial do sistema. No momento apenas existe um único `Creator`, que necessita das posições iniciais
dos centros de massa dos anéis e suas direções autopropulsoras. O seguinte exemplo gera 4 anéis com 30 partículas,
colocado-os ao redor da origem com a direção autopropulsora apontando para a origem:

```python
from math import pi

num_particles = 30
radius = ring.utils.get_ring_radius(
    dynamic_cfg.diameter, num_particles
)
k = 2

creator_cfg = ring.configs.CreatorCfg(
    num_rings=4,
    num_p=num_particles,
    r=radius,
    angle=[pi/4, -3*pi/4, 3*pi/4, -pi/4],
    center=[
        [-k * radius, -k * radius], 
        [k * radius, k * radius], 
        [k * radius, -k * radius], 
        [-k * radius, k * radius], 
    ]
)
```

Essa configuração é irrelevante para a geometria do fluxo de stokes, no entanto,
é nela que é especificado o número de partículas por anel, informação importante para o stokes, então é possível criá-la ignorando todos os outros parâmetros

```python
creator_cfg = ring.configs.CreatorCfg(
    num_rings=0,
    num_p=30,
    r=None, angle=[], center=[],
)
```

> ℹ️
>
> No futuro pretendo melhor isso, tornado necessário apenas informar `num_p`.

## Configurações de integração
Configuração relacionadas a integração das equações que governam o sistema, como o $$ \Delta t $$. Uma técnica de particionamento de espaço é utiliza para otimizar o cálculo de distâncias, suas configurações são setadas aqui. Ainda, é aqui que escolhemos se queremos bordas periódicas ou fluxo de stokes. Ex:

```python
from ring.run_config import ParticleWindows, IntegrationType, InPolCheckerCfg

# Raio do anel em equilíbrio
radius = ring.utils.get_ring_radius(
    dynamic_cfg.diameter, num_particles
)

# Dimensões do particionamento do espaço a nível das
# partículas e dos anéis.
num_cols, num_rows = ring.utils.particle_grid_shape(space_cfg, dynamic_cfg.max_dist)
num_cols_cm, num_rows_cm = ring.utils.rings_grid_shape(space_cfg, radius)

int_cfg = ring.configs.IntegrationCfg(
        dt=0.001,
        particle_win_cfg=ParticleWindows(
            num_cols=num_cols, num_rows=num_rows,
            update_freq=1
        ),
        integration_type=IntegrationType.euler,
        update_type=UpdateType.PERIODIC_WINDOWS,
        in_pol_checker=InPolCheckerCfg(num_cols_cm, num_rows_cm, 50),
)
```

Essa configuração sempre é passada para alguma configuração de execução.

## Configurações da Geometria de Stokes
Caso seja escolhido o fluxo de stokes (`update_type=UpdateType.STOKES`) nas configurações de integração, é necessário informar a configuração dessa geometria. Ex: Obstáculo centrado na origem com
raio igual a 1/5 da altura do canal.

```python
# Raio do anel em equilíbrio
radius = ring.utils.get_ring_radius(
    dynamic_cfg.diameter, num_particles
)

# Quantidade de anéis que cabem no canal
num_ring_in_rect = ring.utils.num_rings_in_rect(2*radius, space_cfg)

stokes_cfg = ring.configs.StokesCfg(
    obstacle_r  = space_cfg.height/5,
    obstacle_x  = 0,
    obstacle_y  = 0,
    create_length = radius * 2.01,
    remove_length = radius * 2.01,
    flux_force = 1, 
    obs_force = 15,
    num_max_rings = int(1.1 * num_ring_in_rect), 
)
```

## Configurações do modo de execução
Agora apenas nos resta escolher o modo de execução e rodar a simulação

### RealTime
Nessa configuração podemos controlar o fps, número de passos que o `Solver` executa por frame, etc. Também podemos escolher qual gráfico utilizar para ver o sistema, exitem duas opções

- `MainGraph`: Possui vários auxílios visuais, como coloração das molas, setas indicando as forças. etc. É bastante lento.
- `SimpleGraph`: Sem muitos auxílios visuais, mas é mais rápido.

Para escolher o gráfico apenas basta passar a sua configuração, vamos escolher o `MainGraph`

```python
from phystem.systems.ring.ui.graphs_cfg import MainGraphCfg

real_time_cfg = ring.run_config.RealTimeCfg(
    int_cfg=int_cfg,
    num_steps_frame=500,
    fps=30,
    graph_cfg=MainGraphCfg(
        show_circles=True,
    ),
)
```

### Video
Configurações para salvar um vídeo. O principal elemento que podemos controlar é a
velocidade da animação, que é influenciada pelos seguintes parâmetros

- speed: Razão entre o tempo da simulação e o tempo do vídeo.
- tf: Tempo final da simulação.
- duration: Duração do vídeo.

Esses 3 parâmetros não são independentes, mas essa configuração aceita qualquer combinação de 2 deles (então fixando o valor do último). Ex: Gerar um vídeo 
chamado "video_test.mp4" de um simulação que vai até t=60:

```python
from phystem.systems.ring.ui.graphs_cfg import MainGraphCfg

save_cfg = ring.run_config.SaveCfg(
    int_cfg=int_cfg,
    path = "./video_test.mp4",
    speed=3,
    tf=60,
    fps=30, 
    graph_cfg = MainGraphCfg(
        show_circles  = True,
    ),
)
```

Os últimos dois modos de execução restantes (`Collect` e `Replay`) possuem suas próprias seções.

## Finalmente rodando a simulação
Com as configurações criadas, agora é só instancias o `Simulation` e executar
```python
sim = ring.Simulation(
    creator_cfg=creator_cfg, 
    dynamic_cfg=dynamic_cfg, 
    space_cfg=space_cfg, 
    run_cfg=run_cfg
)

sim.run()
```
Em que `run_cfg` é alguma das configurações dos modos de execução.

As configurações da geometria de Stokes devem ser passadas da seguinte forma:
```python
sim = ring.Simulation(
    creator_cfg=creator_cfg, 
    dynamic_cfg=dynamic_cfg, 
    space_cfg=space_cfg, 
    run_cfg=run_cfg,
    other_cfgs={"stokes": stokes_cfg},
)
```

# Como salvar, carregar e compartilhar simulações?
{: #saving_configs}
Após ter criado uma instância de `Simulation`, todas as suas configurações
podem ser salvas da seguinte forma

```python
sim = ring.Simulation(**configs)
sim.save_configs("<path to my_configs>")
```

As configurações são salvas em um arquivo [.yaml](https://yaml.org/spec/1.2.2/). Esse arquivo, então, pode ser utilizado para carregar uma simulação

```python
sim = ring.Simulation.load_from_configs("<path to some configs>")
sim.run()
```

Portanto, para compartilhar uma simulação com alguém, apenas é necessário compartilhar o arquivo de configurações gerado pelo método `.save_configs()`.

Ainda, caso seja necessário modificar as configurações salvas antes da execução, digamos dobrar a altura do espaço, podemos fazer assim

```python
configs = ring.run_config.load_configs("<path to configs>")
configs["space_cfg"].height *= 2 

sim = ring.Simulation(**configs)
sim.run()
```

# Como coletar dados?
Para coletar dados, precisamos utilizar a configuração de execução `CollectCfg`. Suas principais configurações são

- func: Função que realiza o procedimento de coleta de dados. Sua assinatura é a seguinte:
    ```python
    def func_name(sim: ring.Simulation, cfg: Any) -> None
    ```
    Geralmente, essa função é chamada de pipeline de coletada de dados.

- func_cfg: Configurações que são passadas para func (o parâmetro `cfg` acima).

## Exemplo: Simples
Vamos criar uma função que coleta as posições dos anéis de forma periódica no tempo,
até o tempo final da simulação. 

```python
import numpy as np
from pathlib import Path

from phystem.systems import ring
from phystem.systems.ring.run_config import CollectDataCfg

def collect_pipeline(sim: ring.Simulation, cfg):
    # Extraindo objetos de interesse
    solver = sim.solver
    collect_cfg: CollectDataCfg = sim.run_cfg
    
    # Pasta onde os dados serão salvos
    save_path = collect_cfg.folder_path 

    count = 0
    collect_last_time = solver.time
    times = []
    while solver.time < collect_cfg.tf:
        solver.update()

        # Realiza a coleta a cada 'cfg["collect_dt"]' unidades de tempo.
        if solver.time - collect_last_time > cfg["collect_dt"]:
            # Ids dos anéis ativos:
            # Em bordas periódicos isso é desnecessário
            # e self.solver.rings_ids pode ser utilizado
            # diretamente.
            ring_ids = solver.rings_ids[:solver.num_active_rings]

            # Posições dos anéis
            pos = np.array(solver.pos)[ring_ids]
            
            # Guardando o tempo de coleta
            times.append(solver.time)

            # Salvando as posições
            file_path = save_path / f"pos_{count}.npy"
            np.save(file_path, pos)
            
            count += 1
            collect_last_time = solver.time
    
    # Salvando o tempo
    file_path = save_path / "times.npy"
    np.save(file_path, np.array(times))

    # Salvando as configurações da simulação
    sim.save_configs(save_path / "configs")
```

Com a função de coleta criada, a instanciação de `CollectCfg` é feita assim

```python
collect_data_cfg = CollectDataCfg(
    int_cfg=int_cfg, # Configuração criada anteriormente
    tf=10,
    folder_path="./data",
    func=collect_pipeline,
    func_cfg={"collect_dt": 1}, 
)
```

e a execução da simulação é o usual

```python
sim = ring.Simulation(
    creator_cfg=creator_cfg, 
    dynamic_cfg=dynamic_cfg, 
    space_cfg=space_cfg, 
    run_cfg=collect_data_cfg,
)

sim.run()
```

## Exemplo: Usando coletores
Existe um coletor que já coleta as posições dos anéis de forma periódica no tempo 
(para ser mais exato, ele coleta o estado do sistema, que inclui mais do que somente a posição), chamado `SnapshotsCol`, então podemos usá-lo. Ainda, ele já possui a sua pipeline de coleta de dados pronta, dessa forma só precisamos setar as configurações:

```python
from phystem.systems.ring.collectors import SnapshotsCol, SnapshotsColCfg

collect_data_cfg = CollectDataCfg(
    int_cfg=int_cfg, # Configuração criada anteriormente
    tf=10,
    folder_path="./data",
    func=SnapshotsCol.pipeline,
    func_cfg=SnapshotsColCfg(
        snaps_dt=1,
    ), 
)
```

Rodando a simulação com essa configuração, vamos obter o mesmo resultado do [Exemplo: Simples](#exemplo-simples), com a adição de mais alguns dados.

> ℹ️
>
> O `SnapshotsCol` vai gerar a seguinte estrutura de arquivos
>
>   
```
data
├── autosave
   ├── autosave
   ├── backup
├── data
├── config.yaml
```
> Os dados estão em `data/data` e `config.yaml` são as configurações da simulação. Como não configuramos nada sobre auto-salvamento, a pasta `autosave` pode ser ignorada nesse caso. 

## Como utilizar auto-salvamentos?
As simulações em geral são bem demoradas, então é interessante criar pontos de salvamento que podem ser restabelecidos em casos de interrupções. Os coletores possuem a configuração `ColAutoSaveCfg`, que quando informada faz com que ocorra o auto-salvamento. Vamos utilizar o `SnapshotsCol` para demostrar esse sistema em ação, a única modificação que precisamos fazer para realizar o auto-salvamento do [Exemplo: Usando coletores](#exemplo-usando-coletores) é a seguinte

```python
from phystem.systems import ring
from phystem.systems.ring.collectors import (
    SnapshotsCol, 
    SnapshotsColCfg, 
    ColAutoSaveCfg,
)

collect_data_cfg = ring.run_config.CollectDataCfg(
    int_cfg=int_cfg, # Configuração criada anteriormente
    tf=10,
    folder_path="./data",
    func=SnapshotsCol.pipeline,
    func_cfg=SnapshotsColCfg(
        snaps_dt=1,
        autosave_cfg=ColAutoSaveCfg(
            freq_dt=3,
        ),
    ), 
)
```

ou seja, adicionamos a configuração `ColAutoSaveCfg` nas configurações de `SnapshotsColCfg`, fazendo com que o auto-salvamento ocorra a cada 3 unidades de tempo. A simulação pode ser rodada a partir do seguinte arquivo:
```python
# main.py
from phystem.systems import ring
from phystem.systems.ring.collectors import (
    SnapshotsCol, 
    SnapshotsColCfg, 
    ColAutoSaveCfg,
)

# Criando as configurações:
#   - creator_cfg 
#   - dynamic_cfg 
#   - space_cfg 
#   - int_cfg

collect_data_cfg = ring.run_config.CollectDataCfg(
    int_cfg=int_cfg, 
    tf=10,
    folder_path="./data",
    func=SnapshotsCol.pipeline,
    func_cfg=SnapshotsColCfg(
        snaps_dt=1,
        autosave_cfg=ColAutoSaveCfg(
            freq_dt=3,
        ),
    ), 
)

sim = ring.Simulation(
    creator_cfg=creator_cfg, 
    dynamic_cfg=dynamic_cfg, 
    space_cfg=space_cfg, 
    run_cfg=collect_data_cfg,
)
sim.run()
```
Rode `main.py` e interrompa a execução com `Ctrl-C` antes que ela termine. Para recarregar do último ponto salvo, basta adicionar o parâmetro `checkpoint` em
`CollectDataCfg`, passando um instância de `CheckpointCfg`, cujo principal argumento
é a pasta onde está o auto-salvamento, no nosso caso sendo `./data/autosave`. Portanto, `collect_data_cfg` deve ficar assim:

```python
collect_data_cfg = CollectDataCfg(
    int_cfg=int_cfg, # Configuração criada anteriormente
    tf=10,
    folder_path="./data",
    func=SnapshotsCol.pipeline,
    func_cfg=SnapshotsColCfg(
        snaps_dt=1,
        autosave_cfg=ColAutoSaveCfg(
            freq_dt=3,
        ),
    ), 
    checkpoint=ring.run_config.CheckpointCfg("./data/autosave"),
)
```
com essa modificação, rodando `main.py` novamente irá fazer com que a execução continue do último ponto salvo.

Alternativamente, é possível carregar o último ponto salvo em um arquivo novo

```python
# load_autosave.py
from phystem.systems.ring import Simulation
from phystem.systems.ring.collectors import SnapshotsCol

configs = Simulation.configs_from_autosave("./data/autosave")
configs["run_cfg"].func = SnapshotsCol.pipeline

sim = Simulation(**configs) 
sim.run()
```

E necessário setar `run_cfg` antes de rodar, pois essa configuração não é salva. `load_autosave.py` deve estar na mesma pasta de `main.py`.

## Exemplo: Utilizando vários coletores na mesma simulação
Suponha que queremos coletar as quantidades arbitrárias Q1, Q2 e Q3 em uma simulação. Elas são completamente independentes. Se criarmos um coletor para cada quantidade, digamos `ColQ1`, `ColQ2` e `ColQ3`, poderíamos prosseguir criando uma pipeline de coleta de dados que os utiliza, mas como isso é algo relativamente comum, existe um gerenciador de coletores que automatiza esse processo. Uma forma de configurar essa simulação de coleta de múltiplos dados é:

```python
from phystem.systems.ring.collectors import ColManager, ColAutoSaveCfg

collect_data_cfg = CollectDataCfg(
    int_cfg=int_cfg, 
    tf=tf,
    folder_path="<path to datas directory>",
    func=ColManager.get_pipeline({
            "q1": ColQ1,
            "q2": ColQ2,
            "q3": ColQ3,
    }),
    func_cfg={
        "q1": "<configs to ColQ1>",
        "q2": "<configs to ColQ2>",
        "q3": "<configs to ColQ3>",
        "autosave_cfg": ColAutoSaveCfg(freq_dt=freq_dt),
    },
)
```

Agora é só rodar a simulação para iniciar o processo de coleta. As vantagens de fazer assim são:

- Não é preciso manualmente escrever a pipeline de coleta de dados.
- O `ColManger` se encarregar de realizar o auto-salvamento de todos os seus coletores de forma sincronizada, e de salvar o estado do sistema somente uma vez. Se a pipeline fosse feita manualmente, além de precisar garantir que todo mundo salva no mesmo instante, cada coletor teria uma cópia do estado do sistema em seu auto-salvamento, o que é redundante.