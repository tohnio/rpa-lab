# 🤖 RPA Lab

Sistema de Automação de Processos Robóticos (RPA) em Python com interface gráfica moderna.

## ✨ Funcionalidades

### 📝 Gerenciamento de Tarefas
- **Criação de Tarefas**: Crie tarefas com nome e descrição
- **Edição de Tarefas**: Edite tarefas existentes adicionando ou removendo ações
- **Exclusão de Tarefas**: Remova tarefas que não são mais necessárias
- **Execução de Tarefas**: Execute tarefas com diferentes velocidades

### ⏺️ Gravação de Ações
- **Gravação Automática**: Capture cliques, digitação e scrolls do mouse
- **Gravação de Teclas**: Capture atalhos de teclado (hotkeys)
- **Contagem Regressiva**: Botão para capturar posição do mouse com contagem 3, 2, 1
- **Parada com ESC**: Interrompa a gravação pressionando ESC

### ➕ Ações Manuais
- **Click**: Adicione cliques em coordenadas específicas
  - Campos X e Y para coordenadas
  - Botão "🎯 Capturar Posição (3s)" com contagem regressiva
- **Digitar**: Digite textos em campos
- **Hotkey**: Pressione combinações de teclas (ex: ctrl+c)
- **Wait**: Aguarde um tempo em segundos
- **Imagem**: Clique baseado em reconhecimento de imagem
  - Botão "📁 Localizar" para selecionar imagens

### 🖼️ Reconhecimento de Imagem
- Encontre e clique em elementos na tela usando imagens
- Configure o nível de confiança (0.0 a 1.0)
- Screenshots salvos automaticamente em `data/screenshots/`

### ⚡ Controle de Velocidade

| Modo | Multiplicador | Descrição |
|------|---------------|-----------|
| Normal | 1x | Velocidade de gravação |
| Rápido | 2x | 2x mais rápido |
| Turbo | 10x | 10x mais rápido |
| Instantâneo | ∞ | Sem delays |

### 📅 Agendamento
- **Diário**: Execute todos os dias em um horário específico
- **Semanal**: Execute em dias específicos da semana (Seg-Dom)
- **Mensal**: Execute em um dia específico do mês
- **Intervalo**: Execute em intervalos regulares (minutos)

### 📊 Histórico de Execuções
- Acompanhe todas as execuções realizadas
- Visualize status (sucesso/falha)
- Veja duração e mensagens de erro
- Logs detalhados para auditoria

## 📋 Requisitos

- Python 3.11 ou superior
- Windows 10/11 (testado)

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/tohnio/rpa-lab.git
cd rpa-lab
```

### 2. Crie um ambiente virtual (recomendado)

```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Execute a aplicação

```bash
python main.py
```

## 📖 Guia de Uso

### Criando uma Nova Tarefa

1. Vá para o painel "📋 Tarefas"
2. Clique em "+ Nova Tarefa"
3. Digite um nome e descrição para a tarefa
4. Clique em "Salvar"

### Gravando Ações

1. Com a tarefa aberta, clique em "⏺️ Gravar"
2. Execute as ações desejadas (cliques, digitação, etc.)
3. Pressione **ESC** ou clique em "⏹️ Parar" para finalizar
4. Clique em "💾 Salvar" para salvar a tarefa

### Adicionando Ações Manuais

1. Na área de edição da tarefa, clique em um dos botões:
   - **Click**: Informe X, Y ou use "🎯 Capturar Posição (3s)"
   - **Digitar**: Digite o texto desejado
   - **Hotkey**: Informe as teclas (ex: ctrl,c)
   - **Wait**: Informe o tempo em segundos
   - **Imagem**: Use "📁 Localizar" para selecionar uma imagem

### Executando uma Tarefa

1. Vá para o painel "📋 Tarefas"
2. Encontre a tarefa desejada
3. Clique em "▶️ Executar"

### Agendando uma Tarefa

1. No painel de tarefas, clique em "📅 Agendar"
2. Selecione o tipo de agendamento
3. Defina o horário (formato HH:MM)
4. Clique em "Salvar"

## 🛡️ Segurança

- **FAILSAFE**: O sistema pára automaticamente se o mouse for movido para o canto superior esquerdo
- **ESC**: Pressione ESC para interromper gravações ou execuções
- **Logs**: Todas as execuções são registradas para auditoria

## 🔧 Tecnologias Utilizadas

- **Python 3.11+**: Linguagem principal
- **CustomTkinter**: Interface gráfica moderna
- **PyAutoGUI**: Automação de mouse/teclado
- **OpenCV**: Reconhecimento de imagem
- **SQLAlchemy**: ORM para banco de dados
- **APScheduler**: Agendamento de tarefas
- **Pydantic**: Validação de dados
- **Loguru**: Sistema de logging

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

---

**RPA Lab** - Automatize suas tarefas repetitivas com facilidade! 🚀