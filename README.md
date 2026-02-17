# 🤖 RPA Lab

Sistema de Automação de Processos Robóticos (RPA) em Python com interface gráfica moderna.

## ✨ Funcionalidades

- **📝 Gravação de Tarefas**: Capture ações de mouse e teclado automaticamente
- **🔄 Reprodução de Tarefas**: Execute tarefas gravadas com variáveis diferentes
- **📅 Agendamento**: Programe execuções diárias, semanais ou mensais
- **🖼️ Reconhecimento de Imagem**: Clique em elementos baseado em imagens (OpenCV)
- **⚡ Controle de Velocidade**: Execute em velocidade normal, rápida, turbo ou instantânea
- **📊 Variáveis Reutilizáveis**: Use `{{variavel}}` para parametrizar tarefas
- **📈 Histórico de Execuções**: Acompanhe logs e estatísticas de execução

## 📋 Requisitos

- Python 3.11 ou superior
- Windows 10/11 (testado)

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/rpa-lab.git
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

### Gravando uma Nova Tarefa

1. Clique em "⏺️ Nova Gravação" no painel lateral
2. Digite um nome para a tarefa
3. Clique em "⏺️ Gravar" para iniciar a gravação
4. Execute as ações desejadas (cliques, digitação, etc.)
5. Pressione **ESC** ou clique em "⏹️ Parar" para finalizar
6. Clique em "💾 Salvar" para salvar a tarefa

### Executando uma Tarefa

1. Vá para o painel "📋 Tarefas"
2. Encontre a tarefa desejada
3. Clique em "▶️ Executar"

### Agendando uma Tarefa

1. No painel de tarefas, clique em "📅 Agendar"
2. Selecione o tipo de agendamento:
   - **Diário**: Executa todos os dias no horário especificado
   - **Semanal**: Executa em dias específicos da semana
   - **Mensal**: Executa em um dia específico do mês
3. Defina o horário (formato HH:MM)
4. Clique em "Salvar"

### Usando Variáveis

1. Use a sintaxe `{{nome_variavel}}` em campos de texto
2. Ao executar, informe os valores das variáveis
3. Exemplo: Digite `{{usuario}}` em um campo de login

### Adicionando Ações Manuais

Além da gravação automática, você pode adicionar ações manualmente:

- **Click**: Clique em uma coordenada específica
- **Digitar**: Digite um texto
- **Hotkey**: Pressione uma combinação de teclas (ex: ctrl+c)
- **Wait**: Aguarde um tempo em segundos
- **Imagem**: Clique baseado em reconhecimento de imagem

### Reconhecimento de Imagem

Para usar cliques baseados em imagem:

1. Capture uma screenshot da região desejada
2. Salve como arquivo PNG na pasta `data/screenshots/`
3. Adicione uma ação do tipo "Imagem"
4. Informe o caminho do arquivo e a confiança (0.0-1.0)

## 🎯 Controle de Velocidade

| Modo | Multiplicador | Descrição |
|------|---------------|-----------|
| Normal | 1x | Velocidade de gravação |
| Rápido | 2x | 2x mais rápido |
| Turbo | 10x | 10x mais rápido |
| Instantâneo | ∞ | Sem delays |

## 📁 Estrutura do Projeto

```
rpa-lab/
├── src/
│   ├── core/              # Núcleo de automação
│   │   ├── recorder.py    # Gravador de ações
│   │   ├── player.py      # Executor de ações
│   │   ├── image_recognition.py  # OpenCV matching
│   │   ├── speed_controller.py   # Controle de velocidade
│   │   └── scheduler.py   # Agendamento
│   │
│   ├── database/          # Camada de dados
│   │   ├── models.py      # Modelos SQLAlchemy
│   │   └── db_manager.py  # Gerenciador de banco
│   │
│   ├── models/            # Modelos Pydantic
│   │   ├── task.py        # Modelo de tarefa
│   │   ├── action.py      # Modelo de ação
│   │   ├── variable.py    # Modelo de variável
│   │   ├── schedule.py    # Modelo de agendamento
│   │   └── execution_log.py  # Log de execução
│   │
│   ├── gui/               # Interface gráfica
│   │   ├── app.py         # Aplicação principal
│   │   └── main_window.py # Janela principal
│   │
│   └── utils/             # Utilitários
│       ├── config.py      # Gerenciador de configuração
│       ├── logger.py      # Sistema de logs
│       └── helpers.py     # Funções auxiliares
│
├── data/                  # Dados (criado automaticamente)
│   ├── rpa.db             # Banco de dados SQLite
│   └── screenshots/       # Screenshots capturados
│
├── logs/                  # Logs (criado automaticamente)
├── config.yaml            # Configurações
├── requirements.txt       # Dependências
└── main.py                # Ponto de entrada
```

## ⚙️ Configuração

Edite o arquivo `config.yaml` para personalizar:

```yaml
# Tema da interface (dark ou light)
app:
  theme: "dark"

# Configurações de gravação
recording:
  default_delay: 0.5
  capture_screenshots: true

# Configurações de execução
execution:
  default_speed: "normal"
  retry_on_failure: 3

# Reconhecimento de imagem
image_recognition:
  default_confidence: 0.9
```

## 🛡️ Segurança

- **FAILSAFE**: O sistema pára automaticamente se o mouse for movido para o canto superior esquerdo
- **ESC**: Pressione ESC para interromper gravações
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

## 🤝 Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📧 Contato

Para dúvidas ou sugestões, abra uma issue no repositório.

---

**RPA Lab** - Automatize suas tarefas repetitivas com facilidade! 🚀