---
title: "Pequenas Melhorias"
author: Marcos Pasa
---

# Ring
- Novo `Creator`: Foi adicionado um `Creator` para os anéis, o `RectangularGridCreator`, que cria os anéis em uma grade retangular. É possível controlar a quantidade de anéis e o espaçamento entre anéis vizinhos em cada dimensão.  
O usuário deve criar a configuração `RectangularGridCfg` para usá-lo. Por questão de conveniência, existe um método que constrói essa configuração dada uma densidade relativa ao equilíbrio (`.from_relative_density`). A densidade de equilíbrio é aquela que se obtém quando o espaçamento entre anéis é nulo.

- Novos `Calculators`: Adicionado três novos calculadores:
    
    - `VelocityCalculator`
    - `DensityCalculator`
    - `TextureCalc`

    Todos possuem a funcionalidade de dividir o espaço em uma grade retangular e calcular as respectivas quantidades em cada célula da grade. Ainda, eles podem fazer média temporal se os dados forem de vários instantes de tempo. Por enquanto, todos atuam nos dados do tipo `DenVelData`, pois esse cara já coleta os centros de massa de forma periódica, que é o que todos necessitam para fazer seus cálculos.  
    Para fazer os cálculos em células nas grades, é utilizado a classe `RegularGrid` (que no momento está no módulo `ring.utils`). Essa classe abstrai toda a complexidade relacionada ao particionamento do espaço e possui vários métodos úteis, como `coords()`, que retornas as posições na grade dado uma lista de pontos.

- Removido adesão entre partículas do mesmo anel.

- Reformulado o módulo de utilidades: Várias funções úteis foram adicionadas nesse módulo, alguns exemplo são:

    - `get_equilibrium_p0`: Retorna o `p0` em que `area0` é igual a área de equilíbrio apenas considerando as molas.
    - `get_invasion_equilibrium_config`: Considerando a situação de equilíbrio do pior cenário de invasão entre anéis, retorna as quantidades que caracterizam essa configuração.
    - `get_equilibrium_relative_area`: Retorna a área de equilíbrio de um anel sozinho em relação a `area0`.

- Resolvido inconveniência do criador para o `Stokes`: Finalmente foi resolvido o problema de inconveniência no momento de gerar o criador para o fluxo de Stokes. Agora a configuração `CreatorCfg` possui o método de classe `empty()`, cujo único argumento é `num_particles`, que retorna uma configuração de criação vazia válida. 

- Obter informações das partículas na interface visual: Agora, quando executando no modo de renderização em tempo real, ao clicar em uma partícula, é mostrado algumas informações sobre a mesma e ao anel que ela pertence, como a sua área.

- Cores aleatórias no replay: Agora cores aleatórias também funcionam no mode replay. 

- Adição de barra de cor: As visualizações de densidade e direção de velocidade agora também possui barras de cores indicando o valor das cores.

# Exemplos
A paste de exemplos foi reformulada, pois antes elas apenas possuía experimentos meus e não exemplos propriamente ditos. Agora ela possui exemplos simples de renderização em tempo real para todos os sistemas implementados até o momento. 