---
title: Acessando dados da simulação enquanto ela roda
author: Marcos Pasa
---

Agora é possível acessar os dados de uma simulação em execução, sem perturbar o estado de execução da mesma. Anteriormente era
necessário pausar a simulação, olhar os dados, e então retornar a simulação, que era um processo bem chato.

O Phystem possuem um sistema de coletores (que pretendo fazer um post sobre em algum momento), que possuem o método `save`, então
o estratégia adotada para implementar essa funcionalidade foi executar esse método de forma periódica.   
O local escolhido para isso foi na função que periodicamente checa se o autossalvamento deve ser feito (`check_autosave` da classe `Collector`, que é a base de todos os coletores), que agora também checa se os dados do coletor devem ser salvos. O processo de autossalvamento é independente do salvamento dos dados.   
Para controlar a frequência de salvamento, foi adicionado o campo `save_state_freq_dt` no classe de configurações do coletores `ColAutoSaveCfg`. Se `save_state_freq_dt` não for informado, os dados apenas serão salvos no fim da simulação, como era anteriormente.  
A função `check_autosave` agora é assim:
```python
def check_autosave(self):
    '''Realiza o auto-salvamento de acordo com a frequência definida.'''
    if self.solver.time - self.autosave_last_time > self.autosave_cfg.freq_dt:
        self.autosave_last_time = self.solver.time
        self.exec_autosave()
    
    if self.autosave_cfg.save_data_freq_dt:
        if self.solver.time - self.autosave_data_last_time > self.autosave_cfg.save_data_freq_dt:
            self.autosave_data_last_time = self.solver.time
            self.save()
```

quando `save()` é executado, os dados são salvos dentro da pasta `data` do respectivo coletor.

# Problemas encontrados
Nem tudo fluiu perfeitamente, pois o método `save` do `DenVelCol` alterava os seus dados internos, que acabava afetando a continuação de sua execução. Esse coletor utiliza `ArraySizeAware` para armazenar os dados, e no momento do salvamento era executado o método `strip`, que remove os dados em branco do array. Para resolver o problema, o `strip` não é mais executado no salvamento, mas sim quando os dados são carregados no `DenVelCalculator`.

Outro problema encontrado foi relacionado ao autossalvamento. Acabei notando que era possível manter uma pasta temporária utilizada no autossalvamento se o programa fosse interrompido na hora certa, mas isso já está resolvido, no momento de carregar um autossalvamento é checado se alguma pasta temporária está presente, e caso esteja, ela é exterminada.