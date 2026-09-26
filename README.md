# Sistema Acadêmico de Notas (SAN)

Sistema web desenvolvido em **Python com Flask** para gerenciamento acadêmico de alunos, professores, responsáveis, turmas, matérias, atividades e notas.

O projeto utiliza **SQLite** como banco de dados e **SQLAlchemy** para o mapeamento objeto-relacional. As senhas dos usuários são armazenadas com hash utilizando **Flask-Bcrypt**.

## Funcionalidades

- Login e logout de usuários.
- Controle de acesso por tipo de usuário:
  - Administrador (ADM)
  - Professor
  - Aluno
  - Responsável
- Cadastro e gerenciamento de usuários.
- Cadastro de alunos, professores e responsáveis.
- Associação de responsáveis aos alunos.
- Cadastro e gerenciamento de turmas.
- Associação de alunos e professores às turmas.
- Cadastro e gerenciamento de matérias.
- Associação de matérias a professores e turmas.
- Cadastro, edição e exclusão de atividades.
- Registro de notas e datas das atividades.
- Perfil do usuário e atualização de dados.
- Dashboard com informações acadêmicas.
- Estatísticas e gráficos de desempenho.
- Quadro de líderes.
- Sistema de conquistas.
- Upload de foto de perfil.
- APIs internas para carregamento de dados do dashboard e estatísticas.

## Tecnologias utilizadas

- **Python**
- **Flask**
- **Flask-SQLAlchemy**
- **Flask-Bcrypt**
- **SQLAlchemy**
- **SQLite**
- **Jinja2**
- **HTML5**
- **CSS3**
- **JavaScript**
- **Bootstrap Icons** (utilizado nas páginas/templates)

## Estrutura do projeto

```text
SAN/
├── instance/
│   └── san.db
│
├── SAN/
│   ├── __init__.py
│   ├── app.py
│   ├── modelos.py
│   ├── rotas.py
│   ├── teste.py
│   │
│   ├── Templates/
│   │   ├── base.html
│   │   ├── cadastro_aluno.html
│   │   ├── cadastro_atividade.html
│   │   ├── cadastro_materia.html
│   │   ├── cadastro_professor.html
│   │   ├── cadastro_responsavel.html
│   │   ├── cadastro_turma.html
│   │   ├── cadastro_usuario.html
│   │   ├── conquistas.html
│   │   ├── dashboard.html
│   │   ├── estatisticas.html
│   │   ├── index.html
│   │   ├── listar_alunos.html
│   │   ├── login.html
│   │   ├── modal_excluir.html
│   │   ├── navbar.html
│   │   ├── perfil.html
│   │   └── quadro_lideres.html
│   │
│   └── static/
│       ├── estilos.css
│       ├── js/
│       │   ├── dashboard.js
│       │   ├── graficos.js
│       │   └── scripts.js
│       ├── img/
│       │   └── default-user.png
│       └── uploads/
│
└── requirements.txt
```

> Os diretórios `__pycache__` e arquivos `.pyc` não são necessários para executar o projeto e podem ser removidos do repositório.

## Requisitos

Antes de executar o sistema, tenha instalado:

- Python 3.10 ou superior
- pip

A versão utilizada no desenvolvimento pode ser conferida pelo ambiente Python do projeto.

## Instalação

### 1. Clonar ou extrair o projeto

Abra o terminal na pasta do projeto.

### 2. Criar um ambiente virtual

No Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

No Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

## Executando o sistema

A aplicação Flask é criada em `SAN/__init__.py`.

Na pasta raiz do projeto, execute:

### Windows

```bash
python -m flask --app SAN run
```

### Linux/macOS

```bash
python3 -m flask --app SAN run
```

Por padrão, o Flask disponibiliza o sistema em:

```text
http://127.0.0.1:5000
```

Para permitir acesso pela rede local:

```bash
python -m flask --app SAN run --host=0.0.0.0
```

## Banco de dados

O sistema utiliza **SQLite**.

O banco é configurado no projeto por meio do SQLAlchemy e é criado automaticamente quando a aplicação é inicializada, através de:

```python
with app.app_context():
    db.create_all()
```

O arquivo de banco utilizado pelo projeto é:

```text
instance/san.db
```

O banco existente pode ser mantido para preservar os dados atuais. Em uma instalação nova, caso o banco ainda não exista, as tabelas são criadas pela aplicação.

### Principais tabelas

- `usuarios`
- `turmas`
- `materias`
- `atividades`
- `aluno_turma`
- `professor_turma`
- `responsavel_aluno`

## Modelos

### Usuario

Armazena informações dos usuários do sistema, como:

- Nome
- E-mail
- Senha criptografada
- Data de nascimento
- Tipo de usuário
- Prontuário
- Foto

As senhas não são armazenadas em texto puro. O projeto utiliza `Flask-Bcrypt` para gerar e verificar os hashes.

### Turma

Representa as turmas cadastradas e possui relacionamentos com:

- Alunos
- Professores
- Matérias

### Materia

Representa uma disciplina/matéria e possui relação com:

- Professor
- Turma
- Atividades

### Atividade

Representa uma atividade acadêmica e registra:

- Matéria
- Tipo da atividade
- Nota
- Data
- Professor
- Aluno

## Perfis de acesso

O sistema trabalha com diferentes tipos de usuários:

| Tipo | Função geral |
|---|---|
| `ADM` | Administração do sistema |
| `PROFESSOR` | Gerenciamento de atividades e acompanhamento dos alunos de suas turmas |
| `ALUNO` | Visualização de informações e desempenho acadêmico |
| `RESPONSAVEL` | Acompanhamento dos alunos vinculados |

As permissões são verificadas pelas rotas e pela sessão do usuário.

## Sistema de conquistas

A rota `/conquistas` calcula informações relacionadas às atividades realizadas pelo usuário e apresenta as conquistas disponíveis no painel.

## Estatísticas

O sistema possui endpoints para fornecer dados utilizados pelos gráficos e estatísticas, incluindo:

```text
/api/notas_por_atividade
/api/atividades_por_materia
/api/dados_dashboard
```

## Segurança

O projeto utiliza:

- Hash de senha com `Flask-Bcrypt`.
- Sessões do Flask para autenticação.
- Controle de acesso baseado no tipo de usuário.
- `secure_filename` para tratamento de nomes de arquivos enviados.
- SQLAlchemy para acesso ao banco de dados.

### Importante para produção

A chave abaixo está definida diretamente no código:

```python
app.secret_key = 'chave_secreta'
```

Em um ambiente real, ela deve ser substituída por uma variável de ambiente ou outro mecanismo seguro de configuração.

Também é recomendável utilizar:

- `DEBUG=False`
- Uma chave secreta forte e aleatória.
- Configurações de produção do Flask.
- Um servidor WSGI apropriado.

## Rotas principais

| Rota | Finalidade |
|---|---|
| `/` | Página inicial/dashboard |
| `/login` | Tela de login |
| `/logout` | Encerrar sessão |
| `/cadastro_usuario` | Cadastro de usuário |
| `/cadastro_aluno` | Cadastro de aluno |
| `/listar_alunos` | Listagem de alunos |
| `/cadastro_professor` | Cadastro de professor |
| `/cadastro_responsavel` | Cadastro de responsável |
| `/cadastro_turma` | Cadastro de turma |
| `/cadastro_materia` | Cadastro de matéria |
| `/cadastro_atividade` | Cadastro de atividade |
| `/perfil` | Perfil do usuário |
| `/estatisticas` | Estatísticas acadêmicas |
| `/quadro_lideres` | Quadro de líderes |
| `/conquistas` | Sistema de conquistas |

## Observações

- O diretório `static/uploads` é utilizado para armazenar arquivos enviados pelo sistema, como fotos.
- O arquivo `SAN/app.py` contém uma estrutura de aplicação Flask separada da aplicação principal inicializada em `SAN/__init__.py`. A execução recomendada deste projeto utiliza o pacote `SAN` com `flask --app SAN run`.
- O arquivo `SAN/teste.py` contém classes utilizadas para testes/estudos e não é necessário para a execução principal do sistema.

## Autores

Projeto acadêmico desenvolvido para fins de estudo e prática de desenvolvimento web com Python, Flask e bancos de dados relacionais.
