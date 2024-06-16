---
---

# Linux

## Criando um ambiente virtual
Se for do seu gosto, crie um ambiente virtual, mas essa etapa não é necessária. Além de isolar o ambiente de desenvolvimento (ótimo para evitar problemas com dependências entre múltiplos projetos), a criação de um ambiente virtual permite que o usuário consiga instalar pacotes sem problemas, o que pode acontecer quando você não é administrador.

Para criar um ambiente virtual no caminho `<venv path>`, execute

```bash
python3 -m venv <venv path>
```

Após a criação, é necessário ativar o ambiente

```bash
source <venv path>/bin/activate
```

Para desativar o ambiente, apenas execute

```bash
deactivate
```

> ℹ️
>
> Para mais informações sobre ambientes virtuais, [clique aqui](https://packaging.python.org/en/latest/tutorials/installing-packages/#creating-virtual-environments).

## Método 1: A partir do git
A forma mais fácil de instalar o phystem é através do git, que apenas necessita do seguinte comando

```bash
pip install -e "git+https://github.com/marcos1561/phystem.git/#egg=phystem"
```

Após sua execução, será possível executar `import phystem` em qualquer lugar. Os arquivos do phystem são instalados em:

- `<venv path>/src/`: Utilizando ambiente virtual.
- `<current dir>/src/`: Utilizando instalação global.

Se desejável, é possível configurar o local da instalação com a flag `--src`.

A flag `-e` é para a instalação ser editável, dessa forma, mudanças nos arquivos do phystem são aplicadas automaticamente, caso contrário, é necessário reinstalar a cada alteração feita.

## Método 2: Clonando o repositório
Primeiro clone o repositório

```bash
git clone https://github.com/marcos1561/phystem.git
```

em sequência, instale utilizando o `pip`

```bash
pip install -e phystem
```

## Testando a instalação
Para testar a instalação, abra um REPL do python e execute

```python
>>> import phystem.test_install
```

Uma janela deve abrir contendo uma animação do sistema implementado no tutorial [Como utilizar o phystem?]({{ 'docs/tutorial_step_by_step.html' | relative_url }}).

## Compilando o módulo em C++
{: #installation_compilation}
Para explorar sistemas que utilizam o módulo feito em C++, é necessário compilar esse código.
Para isso, apenas execute o script `build.sh` que está localizado na pasta `/src/phystem/cpp/pybind`.
A compilação pode demorar um pouco. 

```bash
source <caminho para o build.sh>/build.sh
```