# Relatório Técnico: Modelação e Calibração Automatizada de Laser Shock Peening (LSP)

## 1. Objetivo
A determinação das propriedades exatas de materiais sujeitos a altas taxas de deformação, como ocorre no processo de *Laser Shock Peening* (LSP), é um desafio complexo. A utilização de dados de literatura muitas vezes não reflete o comportamento real do material sob as condições específicas do laser.

O objetivo deste projeto é desenvolver uma arquitetura computacional em circuito fechado (*closed-loop*) para calibrar automaticamente os parâmetros do modelo constitutivo de *Johnson-Cook* ($A$, $B$ e $n$). Através da otimização heurística, o sistema ajusta estes parâmetros iterativamente até que o perfil de tensão residual simulado corresponda ao perfil alvo obtido experimentalmente.

---

## 2. Configuração da Simulação Numérica (Abaqus)
A base física deste projeto assenta num modelo de elementos finitos desenvolvido no Abaqus. 

* **Abordagem Dinâmica Explícita:** O processo de LSP caracteriza-se por um impacto de curtíssima duração. Utilizamos o *solver* `Abaqus/Explicit` para capturar a propagação das ondas de choque de alta frequência através da espessura do material.
* **Modelo Constitutivo:** O material é modelado utilizando a lei de *Johnson-Cook*, que relaciona a tensão de escoamento com a deformação plástica e a taxa de deformação.
* **Carregamento (Loading):** O impacto do laser é modelado como um pulso de pressão dependente do tempo e do espaço, aplicado na superfície superior do bloco metálico.
* **Fases da Simulação:** A simulação é dividida em dois passos principais: a fase de impacto dinâmico (onde a pressão é aplicada) e a fase de relaxamento (onde a energia se dissipa e o campo de tensões estabiliza).

---

## 3. Estudo de Convergência de Malha
Para garantir a precisão dos resultados e evitar tempos de computação desnecessários, foi realizado um estudo rigoroso de convergência de malha.

* **Estratégia:** Foi aplicada uma técnica de particionamento (*bias*), onde a zona de impacto (superfície) possui uma malha extremamente refinada para capturar os elevados gradientes de tensão e deformação, enquanto as zonas mais profundas e afastadas possuem elementos maiores.
* **Elementos Utilizados:** Foram utilizados elementos hexaédricos com integração reduzida para evitar problemas de *volumetric locking* e garantir a correta propagação da onda de choque.
* **Resultado:** O tamanho do elemento na zona de impacto foi progressivamente reduzido até que o perfil de tensão residual na profundidade atingisse uma assíntota (mudança negligenciável entre iterações).

*> Figura 1: Variação da tensão residual de pico em função do tamanho característico do elemento na zona de impacto.*

---

## 4. Convergência do Tamanho do Modelo
Em simulações dinâmicas de ondas de choque, os limites geométricos do modelo podem causar reflexões artificiais (efeito de fronteira) que retornam à zona de interesse e poluem os resultados da tensão residual.

* **Metodologia:** As dimensões laterais e a profundidade do bloco foram progressivamente aumentadas.
* **Critério de Aceitação:** O tamanho ideal do modelo foi estabelecido no ponto em que as ondas de tensão refletidas pelas fronteiras já não têm energia suficiente para alterar o estado de tensão residual no centro da peça (zona de medição). Isto assegura que o modelo numérico representa de forma fiel um meio semi-infinito, análogo a uma peça real de grandes dimensões.

*> Figura 2: Impacto da reflexão das ondas de choque no perfil de tensão de acordo com as dimensões do bloco.*

---

## 5. Convergência do Tempo de Relaxamento
Um dos aspetos mais críticos da modelação de LSP é determinar o momento exato em que o processo dinâmico termina e a peça atinge o equilíbrio estático. Extrair os resultados demasiado cedo resulta na medição de vibrações elásticas transientes, e não da verdadeira tensão residual.

* **Análise Energética:** Monitorizou-se o rácio entre a Energia Cinética (ALLKE) e a Energia Interna (ALLIE) do sistema ao longo do tempo.
* **Critério de Paragem:** O tempo de relaxamento foi considerado convergente quando a energia cinética do sistema caiu para uma fração negligenciável (geralmente < 1% a 5%) da energia interna total, indicando que as oscilações cessaram e o campo de tensões residuais está permanentemente estabelecido.

*> Figura 3: Dissipação da Energia Cinética vs. Tempo de Relaxamento.*

---

## 6. Otimização por Enxame de Partículas (PSO) e Automação
Com o modelo de elementos finitos validado (malha, tamanho e relaxamento otimizados), implementou-se a camada de calibração utilizando *Particle Swarm Optimization* (PSO).

* **Arquitetura:** O processo é gerido por um ambiente Python externo (`pyswarms`), que interage de forma autónoma com o Abaqus através de ficheiros JSON de configuração.
* **O Algoritmo:**
  1. O enxame é inicializado com várias "partículas", cada uma contendo um palpite para os parâmetros de *Johnson-Cook* ($A, B, n$).
  2. Para cada partícula, o Python atualiza o ficheiro `model_config.json` e lança o Abaqus em modo invisível (`noGUI`).
  3. O Abaqus constrói a geometria, aplica a malha convergida, simula o impacto, aguarda o tempo de relaxamento e extrai as tensões da superfície para um ficheiro JSON de saída.
  4. O Python lê esta saída e calcula a Função Objetivo (Erro Quadrático Médio - MSE) comparando a simulação com a `target_curve.pkl`.
  5. As partículas ajustam as suas posições (parâmetros $A, B, n$) com base no seu próprio sucesso e no sucesso do grupo, convergindo progressivamente para o erro mínimo.

*> Animação 1: Evolução das tentativas de calibração do enxame iterando em direção ao perfil de tensão alvo.*