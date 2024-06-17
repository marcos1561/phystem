---
---

## Como utilizar os sistemas físicos já implementados com o phystem?
O sub-pacote `phystem.systems` contém os sistemas físicos já implementados com o phystem. 

Em geral, para utilizá-los é necessário criar uma instância de `Simulation`, que está no módulo `simulation.py` do respectivo sistema, e rodar o método `run`. `Simulation` requer que sejam passadas as seguintes configurações

1. creator_cfg: Configurações da criação da configuração inicial do sistema.
2. dynamic_cfg: Configurações da dinâmica do sistema.
3. space_cfg: Configurações do espaço físico em que o sistema se encontra.
4. run_cfg: Configurações do modo de execução.

Os itens 1, 2 e 3 estão no módulo `configs.py` do respectivo sistema, então basta olhar nesse arquivo para saber como instanciar essas configurações.

O item 4 pode estar em dois locais:

1. Caso o sistema utiliza as configurações padrões de execução, elas se encontram em `phystem.core.run_config`
2. Caso o sistema extendeu tais configurações, elas se encontram no módulo `run_config.py` do respectivo sistema. 

> ⚠️
>
> 1. Caso você utilize um sistema que utiliza o módulo feito em c++ (ring e szabo), é necessário compilar o código que gera tal módulo. 
Para tal, consulte [Compilando o módulo em C++]({{ "docs/installation.html#installation_compilation" | relative_url }}).

No momento atual, existem os seguintes sistemas implementados:

### Ring
Implementação de múltiplos anéis ativos, com algumas pequenas modificações, apresentado em Teixeira [[1]](#1).

<!-- ![]({{ "assets/images/rings.gif" | relative_url }}) -->
<img src="{{ 'assets/images/rings.gif' | relative_url }}" alt width="700"/>

### Szabo
Implementação do modelo de partículas ativas proposto em Szabó [[2]](#2)

<!-- ![]({{ "assets/images/szabo.gif" | relative_url }}) -->
<img src="{{ 'assets/images/szabo.gif' | relative_url }}" alt width="700"/>

### Vicsek
Implementação do modelo proposto em Vicsek [[3]](#3). 
> ⚠️
> 
> A implementação não está completa, apenas tem uma versão do seu solver extremamente desorganizada.

### Random Walker
Sistema implementado no tutorial [Como utilizar o phystem?]({{ 'docs/tutorial_step_by_step.html' | relative_url }}).

## Referências
<a id="1">[1]</a> 
TEIXEIRA, E. F.; FERNANDES, H. C. M.; BRUNNET, L. G. A single active ring model with velocity self-alignment. Soft Matter, v. 17, n. 24, p. 5991–6000, 23 jun. 2021. 

<a id="2">[2]</a>
SZABÓ, B. et al. Phase transition in the collective migration of tissue cells: experiment and model. Physical Review. E, Statistical, Nonlinear, and Soft Matter Physics, v. 74, n. 6 Pt 1, p. 061908, dez. 2006.

<a id="3">[3]</a>
VICSEK, T. et al. Novel type of phase transition in a system of self-driven particles. Physical Review Letters, v. 75, n. 6, p. 1226–1229, 7 ago. 1995. 