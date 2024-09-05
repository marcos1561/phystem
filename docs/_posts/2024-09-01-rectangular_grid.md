---
title: "Anéis: Novo criador"
author: Marcos Pasa
---

Foi adicionado um `Creator` para os anéis, o `RectangularGridCreator`, que cria os anéis em uma grade retangular. É possível controlar a quantidade de anéis e o espaçamento entre anéis vizinhos em cada dimensão.  
O usuário deve criar a configuração `RectangularGridCfg` para usá-lo. Por questão de conveniência, existe um método que constrói essa configuração, dada uma densidade relativa ao equilíbrio (`.from_relative_density`). A densidade de equilíbrio é aquela que se obtém quando o espaçamento entre anéis é nulo. 


