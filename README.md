# Interface da simulação do LSP

Este projeto fornece uma interface de usuário (UI) para configurar e executar um fluxo de trabalho do Abaqus para o processo do *Laser Shock Peening* (LSP). Pela interface, você pode editar os parâmetros do modelo, iniciar a simulação, extrair dados de tensão residual do arquivo ODB gerado e visualizar os perfis de tensão resultantes diretamente na.

## O que a interface faz

A janela principal é dividida em três áreas:

* Painel esquerdo: parâmetros de simulação editáveis.
* Painel superior direito: plota os resultados extraídos de tensão residual.
* Painel inferior direito: mostra o log de execução.

Quando você clica em **Run Simulation**, a interface:

1. Lê os parâmetros do painel esquerdo.
2. Escreve-os em `backend/model_config/model_config.json`.
3. Inicia o Abaqus com `backend/command.py`.
4. Constrói o modelo, executa o *job* e extrai os dados de tensão.
5. Salva os dados extraídos em `backend/data/<nome_do_modelo>_stress_profile.json`.
6. Plota as curvas de tensão de superfície e em profundidade na interface.

## Pré-requisitos e Dependências

Para rodar este projeto, você precisará ter o **Python (versão 3.6 ou superior)** e o software **Abaqus** instalados em sua máquina.

O projeto utiliza as seguintes bibliotecas Python:

* `tkinter` e `json`: Bibliotecas nativas do Python (não exigem instalação separada na maioria dos sistemas).
* `matplotlib`: Necessária para a geração dos gráficos na interface e para o script opcional de plotagem.

Para instalar as dependências necessárias, abra o seu terminal e execute:

```bash
pip install matplotlib
```

## Como iniciar a interface

1. Abra o seu terminal (Prompt de Comando, PowerShell ou Terminal do Linux/macOS).
2. Navegue até o diretório raiz onde o projeto está salvo usando o comando `cd`:
```bash
cd caminho/para/a/pasta/do/projeto
```
3. Inicie a interface executando o arquivo principal:
```bash
python main.py
```
*(Dependendo da configuração do seu sistema operacional, pode ser necessário utilizar `python3 main.py`)*

4. Na janela que se abrirá, edite os parâmetros desejados no painel esquerdo.
5. Altere o nome do modelo se desejar um novo nome para os arquivos de saída.
6. Clique em **Run Simulation**.
7. Acompanhe o log de execução e visualize os gráficos de resultados à direita.

Se você quiser voltar aos valores padrão em qualquer momento, clique em **Restore Defaults** (Restaurar Padrões).

## Parâmetros editáveis na interface

Os parâmetros exibidos inicialmente são preenchidos a partir de `backend/model_config/default_model_config.json`. Apenas os campos com uma entrada `labelUI` aparecem na interface.

### Identificação do Modelo

| Campo | Significado |
| --- | --- |
| Model name | Nome usado para o modelo do Abaqus, para o ODB e para o arquivo JSON de saída. |

### Model Builder > Configurações do Pulso (Pulse Settings)

| Campo | Unidade | Significado |
| --- | --- | --- |
| Initial Pressure | GPa | Pressão em r = 0 usada no perfil espacial do pulso. |
| Maximum Pressure | GPa | Valor do pico de pressão na espacialdade do pulso. |
| Maximum Radius | mm | Raio onde a pressão atinge seu valor máximo. |
| Diameter | mm | Diâmetro de carregamento usado pelo perfil de pressão. |
| Total Pressure Time | ns | Duração do pulso de pressão. |

### Model Builder > Parâmetros da Etapa (Step Parameters)

| Campo | Unidade | Significado |
| --- | --- | --- |
| Rest Phase Duration | µs | Duração da etapa da fase de relaxamento (quando não há mais ação de cargas externas). |

### Model Builder > Propriedades da Malha (Mesh Properties)

| Campo | Unidade | Significado |
| --- | --- | --- |
| Interest Region Size | mm | Tamanho do elemento da região refinada próxima à área de impacto. |
| Maximum Element Size | mm | Limite superior para o tamanho do elemento da malha. |

### Model Builder > Dimensões da Geometria (Geometry Dimensions)

| Campo | Unidade | Significado |
| --- | --- | --- |
| Finite Cube Length | mm | Comprimento do modelo. |
| Finite Cube Height | mm | Altura do modelo. |
| Interest Region Length | mm | Comprimento da região onde a malha é refinada. |
| Interest Region Height | mm | Altura da região onde a malha é refinada |

### Model Builder > Propriedades do Material (Material Properties)

#### Modelo de Johnson-Cook

| Campo | Unidade | Significado |
| --- | --- | --- |
| Yield stress (A) | MPa | Parâmetro A de Johnson-Cook. |
| Hardening constant (B) | MPa | Parâmetro B de Johnson-Cook. |
| Hardening exponent (n) | - | Parâmetro n de Johnson-Cook. |
| Strain rate constant (C) | - | Constante de taxa de deformação (C) de Johnson-Cook. |
| Reference strain rate | 1/s | Taxa de deformação de referência de Johnson-Cook. |

#### Elasticidade

| Campo | Unidade | Significado |
| --- | --- | --- |
| Young's modulus | GPa | Módulo de elasticidade usado pelo modelo. |
| Poisson's ratio | - | Coeficiente de Poisson do material elástico. |

#### Outros

| Campo | Unidade | Significado |
| --- | --- | --- |
| Density | kg/m³ | Densidade do material usado na simulação. |

### Model Builder > Configurações do Job (Job Settings)

| Campo | Unidade | Significado |
| --- | --- | --- |
| Number of CPUs | - | Número de núcleos de CPU usados pelo *job* do Abaqus. |

### Parâmetros de Extração (Extraction Parameters)

| Campo | Unidade | Significado |
| --- | --- | --- |
| Surface Path Distance | mm | Distância do caminho de extração de tensão residual na superfície. |
| Depth Path Distance | mm | Distância do caminho de extração tensão residual em profundidade. |

## Notas sobre parâmetros ocultos

Alguns valores existem no arquivo de configuração, mas não aparecem na interface porque não possuem uma entrada `labelUI`. Eles são mantidos automaticamente quando a interface escreve a configuração de tempo de execução.

Exemplos incluem valores internos, tais como:

* `durationShotPhase`
* `totalFrames`
* `infiniteBorder`
* `m`
* `meltingTemp`
* `transitionTemp`

Esses valores são preservados no JSON gerado, embora não sejam editáveis no formulário.

## Arquivos de saída

Após uma execução bem-sucedida, os arquivos gerados mais relevantes são:

* `backend/model_config/model_config.json` - a configuração escrita pela interface.
* `backend/data/<nome_do_modelo>_stress_profile.json` - dados extraídos do perfil de tensão.
* `backend/log/abaqus_log.txt` - log de execução do fluxo de trabalho do Abaqus.