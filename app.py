import json, random,string
import os
from datetime import datetime


from werkzeug.utils import secure_filename 

from flask import Flask, render_template, request,redirect, url_for, session
from modelos import Usuario, Atividade, Materia,Turma
from functools import wraps

app = Flask(__name__)

app.secret_key = 'chave_secreta'
app.permanent_session_lifetime = 3600  # 1 hora
app.config['UPLOAD_FOLDER'] = 'static/uploads'

usuarios = []
atividades = []
materias=[]
turmas=[]

# leitura dos dados dos arquivos de usuários e atividades, se existirem
# Importante: não podemos falhar a leitura de turmas caso os outros arquivos não existam.
# Ex: se materias.json não existir, isso hoje impediria turmas de carregar.
try:
    with open("usuarios.json", "r") as arquivo:
        dados = json.load(arquivo)
        usuarios = [Usuario(**usuario) for usuario in dados]
except (FileNotFoundError, json.JSONDecodeError):
    usuarios = []

try:
    with open("atividades.json", "r") as arquivo:
        dados = json.load(arquivo)
        atividades = [Atividade(**atividade) for atividade in dados]
except (FileNotFoundError, json.JSONDecodeError):
    atividades = []

try:
    with open("materias.json", "r") as arquivo:
        dados = json.load(arquivo)
        materias = [Materia(**materia) for materia in dados]
except (FileNotFoundError, json.JSONDecodeError):
    materias = []

try:
    with open("turmas.json", "r") as arquivo:
        dados = json.load(arquivo)
        turmas = []
        for turma in dados:
            # compatibilidade com dados antigos (sem aluno_ids/professor_ids)
            turma.setdefault('aluno_ids', [])
            turma.setdefault('professor_ids', [])
            turmas.append(Turma(**turma))
except (FileNotFoundError, json.JSONDecodeError):
    turmas = []


# decorador para proteger rotas que exigem autenticação
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# rota para a página inicial


@app.route("/")
@login_required
def home():
    atividades_usuario = ler_atividades_usuario()

    for atividade in atividades_usuario:
        # Nome do aluno
        aluno = next(
            (u for u in usuarios if str(u.id) == str(atividade.aluno_id)),
            None
        )
        atividade.aluno_nome = aluno.nome if aluno else "Aluno não encontrado"

        # Nome da matéria
        materia = next(
            (m for m in materias if str(m.id) == str(atividade.materia)),
            None
        )
        atividade.materia_nome = (
            materia.nome_materia if materia else "Matéria não encontrada"
        )

    return render_template(
        "index.html",
        atividades=atividades_usuario,
        materias=materias,
        turmas=turmas
    )
# rotas para login e logout

@app.route("/login")
def login():
    if not usuarios:
        usuarios.append(Usuario(
        0,
        "Administrador",
        "admin@admin.com",
        "admin123",
        "2000-01-01",
        "ADM",
        criar_prontuario(),
        None
    ))
    salvar_usuarios_json()
    return render_template("login.html", resultado=None)

@app.route("/autenticar", methods=["POST"])
def autenticar():
    prontuario = request.form.get("prontuario")
    senha = request.form.get("senha")

    for usuario in usuarios:
        if usuario.prontuario == prontuario and usuario.senha == senha:
            session.permanent = True
            session['usuario_tipo'] = usuario.tipo
            session['usuario_id'] = usuario.id
            session['usuario'] = usuario.prontuario
            session['nome_usuario'] = usuario.nome
            return redirect(url_for("home"))
    return render_template("login.html", resultado="falha")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# rotas para cadastro de usuário

@app.route("/cadastro_usuario", methods=["GET"])
def cadastro_usuario():
    return render_template("cadastro_usuario.html", resultado=None)


@app.route("/cadastro_aluno", methods=["GET"])
def cadastro_aluno():
    return render_template("cadastro_aluno.html", resultado=None, turmas=turmas)


@app.route("/listar_alunos")
@login_required
def listar_alunos():

    usuario_tipo = session.get('usuario_tipo')
    usuario_id = session.get('usuario_id')

    # ADM: lista todos os alunos
    if usuario_tipo in ['ADM']:

        alunos = [u for u in usuarios if getattr(u, 'tipo', None) == 'ALUNO']
        return render_template('listar_alunos.html', alunos=alunos)


    # ALUNO: lista apenas ele
    if usuario_tipo == 'ALUNO':
        alunos = [u for u in usuarios if str(u.id) == str(usuario_id) and getattr(u, 'tipo', None) == 'ALUNO']
        return render_template('listar_alunos.html', alunos=alunos)

    # PROFESSOR: lista alunos das turmas atendidas por suas matérias
    if usuario_tipo == 'PROFESSOR':
        professor_id = str(usuario_id)

        turma_ids_atendidas = set()
        for m in materias:
            if str(m.professor_id) == professor_id:
                turma_ids_atendidas.add(str(m.turma_id))

        alunos_ids_permitidos = set()
        for t in turmas:
            if str(t.id) in turma_ids_atendidas:
                for aid in t.aluno_ids:
                    alunos_ids_permitidos.add(str(aid))

        alunos = [u for u in usuarios if getattr(u, 'tipo', None) == 'ALUNO' and str(u.id) in alunos_ids_permitidos]
        return render_template('listar_alunos.html', alunos=alunos)

    return render_template('listar_alunos.html', alunos=[])


@app.route("/cadastro_professor", methods=["GET"])
def cadastro_professor():
    return render_template("cadastro_professor.html", resultado=None, turmas=turmas)



@app.route("/cadastro_responsável", methods=["GET"])
def cadastro_responsavel():
    return render_template("cadastro_responsavel.html", resultado=None)

@app.route("/salvar_usuario", methods=["POST"])
def salvar_usuario():
    novo_id = max([usuario.id for usuario in usuarios], default=-1) + 1

    nome = request.form.get("nome")
    senha = request.form.get("senha")
    data_nascimento = request.form.get("data_nascimento")
    tipo = request.form.get("tipo")
    turma_id = request.form.get("turma")
    responsavel_legal = request.form.get("responsavel_legal")

    # seu login autentica por prontuário+senha, então o prontuário precisa existir
    prontuario = criar_prontuario()

    # email não é enviado nos seus formulários de cadastro; manter opcional no modelo
    email = ""

    if nome and senha and data_nascimento and tipo and prontuario:
        usuarios.append(Usuario(novo_id, nome, email, senha, data_nascimento, tipo, prontuario, foto=None))
        salvar_usuarios_json()


        nascimento = datetime.strptime(data_nascimento, "%Y-%m-%d")
        hoje = datetime.today()

        idade = (hoje.year - nascimento.year - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day)))

        # Atualiza Turma com o aluno/professor ligado ao usuário recém-cadastrado.
        # (O form envia `turma`; garantimos que não duplicará IDs.)
        if turma_id:
            turma_sel = [t for t in turmas if str(t.id) == str(turma_id)]
            if turma_sel:
                turma_obj = turma_sel[0]
            if tipo == "ALUNO":
                    if str(novo_id) not in [str(aid) for aid in turma_obj.aluno_ids]:
                        turma_obj.aluno_ids.append(novo_id)
                        salvar_turmas_json()
            elif tipo == "PROFESSOR":
                    if str(novo_id) not in [str(pid) for pid in turma_obj.professor_ids]:
                        turma_obj.professor_ids.append(novo_id)
                        salvar_turmas_json()

        # após cadastrar, mostre a tela de login com sucesso
    if tipo == "ALUNO":
        if idade < 18 or responsavel_legal == "SIM":
            session["aluno_id_para_responsavel"] = novo_id
            return redirect(url_for("cadastro_responsavel"))

    return render_template("login.html", resultado="cadastrado")

    return render_template("login.html", resultado="falha")




# rotas para cadastro de atividade
@app.route("/cadastro_materia", methods=["GET"])
def cadastro_materia():
    novo_id = max([materia.id for materia in materias], default=-1) + 1
    return render_template(
        "cadastro_materia.html",
        id=novo_id,
        materia=None,
        usuarios=usuarios,
        turmas=turmas,
    )


@app.route("/salvar_materia/<int:id>",methods=["POST"])
def salvar_materia(id):
    nome_materia = request.form.get("materia")
    professor_id = request.form.get("professor_id")
    turma_id = request.form.get("turma_id")

    if nome_materia:
        if materia := [materia for materia in materias if materia.id == id]:
            materias[materias.index(materia[0])] = materia(id, nome_materia, professor_id, turma_id)
        else:
            novo_id = max([materia.id for materia in materias], default=-1) + 1
            materias.append(Materia(novo_id, nome_materia, professor_id, turma_id))
        salvar_materias_json()

        # Atualiza Turma com o(s) professor(es) ligados à matéria
        turma_sel = [t for t in turmas if str(t.id) == str(turma_id)]
        if turma_sel:
            turma_obj = turma_sel[0]
            if professor_id and str(professor_id) not in [str(pid) for pid in turma_obj.professor_ids]:
                turma_obj.professor_ids.append(professor_id)
                salvar_turmas_json()

    return redirect(url_for("home"))


@app.route("/cadastro_turma", methods=["GET"])
def cadastro_turma():
    novo_id = max([turma.id for turma in turmas], default=-1) + 1
    return render_template("cadastro_turma.html", id=novo_id, turma=None, turmas=turmas)

@app.route("/salvar_turma/<int:id>", methods=["POST"])
@login_required
def salvar_turma(id):
    nome_turma = request.form.get("nome_turma")

    if nome_turma:
        if turma := [turma for turma in turmas if turma.id == id]:
            # preserva listas existentes
            turmas[turmas.index(turma[0])] = Turma(id, nome_turma, turma[0].aluno_ids, turma[0].professor_ids)
        else:
            novo_id = max([turma.id for turma in turmas], default=-1) + 1
            turmas.append(Turma(novo_id, nome_turma, [], []))

        salvar_turmas_json()
    return redirect(url_for("home"))
   
@app.route("/cadastro_atividade", methods=["GET"])
def cadastro_atividade():
    # Somente ADM e PROFESSOR podem cadastrar atividades.
    usuario_tipo = session.get('usuario_tipo')
    if usuario_tipo not in ['ADM','PROFESSOR']:
        return redirect(url_for("home"))

    novo_id = max([atividade.id for atividade in atividades], default=-1) + 1

    # Lista de alunos permitidos para exibir no select.
    usuarios_alunos_permitidos = []
    if usuario_tipo in ['ADM']:
        usuarios_alunos_permitidos = [u for u in usuarios if getattr(u, 'tipo', None) == 'ALUNO']
    else:
        professor_id = str(session.get('usuario_id'))
        turma_ids_atendidas = set()
        for m in materias:
            if str(m.professor_id) == professor_id:
                turma_ids_atendidas.add(str(m.turma_id))

        alunos_ids_permitidos = set()
        for t in turmas:
            if str(t.id) in turma_ids_atendidas:
                for aid in t.aluno_ids:
                    alunos_ids_permitidos.add(str(aid))

        usuarios_alunos_permitidos = [
            u for u in usuarios
            if getattr(u, 'tipo', None) == 'ALUNO' and str(u.id) in alunos_ids_permitidos
        ]

    return render_template(
        "cadastro_atividade.html",
        id=novo_id,
        atividade=None,
        atividades=atividades,
        materias=materias,
        usuarios=usuarios_alunos_permitidos,
    )



@app.route("/salvar_atividade/<int:id>", methods=["POST"])
@login_required
def salvar_atividade(id):
    materia = request.form.get("nome_materia")
    tipoativ = request.form.get("tipoativ")
    nota = request.form.get("nota")
    data = request.form.get("data")

    if materia and tipoativ and nota and data:
        # ADM/PROFESSOR escolhem o aluno no formulário.
        # (ALUNO é bloqueado no GET /cadastro_atividade, mas mantemos proteção aqui.)
        usuario_tipo = session.get('usuario_tipo')
        if usuario_tipo in ['ADM', 'ADMIN', 'PROFESSOR']:
            aluno_id = request.form.get('nome_aluno')
        else:
            aluno_id = session['usuario_id']

        if not aluno_id:
            return redirect(url_for("home"))

        if atividade := [atividade for atividade in atividades if atividade.id == id]:
            atividades[atividades.index(atividade[0])] = Atividade(id, materia, tipoativ, nota, data, None, aluno_id)
        else:
            novo_id = max([atividade.id for atividade in atividades], default=-1) + 1
            atividades.append(Atividade(novo_id, materia, tipoativ, nota, data, None, aluno_id))

        # Atualiza Turma com o aluno via matéria (o form envia materia.id em `nome_materia`)
        materia_id = str(materia)


        materias_sel = [m for m in materias if str(m.id) == materia_id]
        if materias_sel:
            for m in materias_sel:
                turma_id = m.turma_id
                turma_sel = [t for t in turmas if str(t.id) == str(turma_id)]
                if turma_sel and str(aluno_id) not in [str(aid) for aid in turma_sel[0].aluno_ids]:
                    turma_sel[0].aluno_ids.append(aluno_id)
            salvar_turmas_json()

        salvar_atividades_json()


    return redirect(url_for("home"))


@app.route("/editar/<int:id>")
def exibir_edicao(id):
    # Somente ALUNO (o próprio) e ADM podem editar.
    usuario_tipo = session.get('usuario_tipo')
    usuario_id = str(session.get('usuario_id'))

    if usuario_tipo == 'ADM':
        atividade = [a for a in atividades if a.id == id]
    else:
        atividade = [a for a in atividades if a.id == id and str(a.aluno_id) == usuario_id]

    if atividade:
        return render_template("cadastro_atividade.html", atividade=atividade[0], id=id, resultado=None)
    return redirect(url_for("home"))


@app.route("/excluir_atividade/<int:id>")
def excluir_atividade(id):
    # Somente ALUNO (o próprio) e ADM podem excluir.
    usuario_tipo = session.get('usuario_tipo')
    usuario_id = str(session.get('usuario_id'))

    if usuario_tipo == 'ADM':
        atividade = [a for a in atividades if a.id == id]
    else:
        atividade = [a for a in atividades if a.id == id and str(a.aluno_id) == usuario_id]

    if atividade:
        atividades.remove(atividade[0])
        salvar_atividades_json()
    return redirect(url_for("home"))



@app.route("/perfil")
@login_required
def perfil():
    usuario = [usuario for usuario in usuarios if usuario.id == session.get('usuario_id')]
    return render_template("perfil.html", usuario=usuario[0] if usuario else None)

@app.route("/atualizar_perfil", methods=["POST"])
def atualizar_perfil():
    nome = request.form.get("nome")
    email = request.form.get("email")
    data_nascimento = request.form.get("data_nascimento")
    genero = request.form.get("genero")
    foto = upload_imagem()

    if nome and email and data_nascimento and genero:
        if usuario := [usuario for usuario in usuarios if usuario.id == session.get('usuario_id')]:
            if foto is None:
                foto = usuario[0].foto
            usuario_atualizado = Usuario(usuario[0].id, nome, email, usuario[0].senha, data_nascimento, genero, foto)
            usuarios[usuarios.index(usuario[0])] = usuario_atualizado
            session['nome_usuario'] = usuario_atualizado.nome
            salvar_usuarios_json()
            return render_template("perfil.html", usuario=usuario_atualizado, resultado="atualizado")
    return redirect(url_for("home"))

def upload_imagem():
    arquivo = request.files.get("foto")
    
    if arquivo:
        nome_seguro = secure_filename(arquivo.filename)
        caminho = os.path.join("static/uploads", nome_seguro)
        arquivo.save(caminho)
        return caminho.replace('\\', '/')
    return None


# funções auxiliares para leitura e escrita de arquivos JSON

# ler as atividades do usuário logado (com controle de permissão)
def ler_atividades_usuario():
    try:
        with open("atividades.json", "r") as arquivo:
            dados = json.load(arquivo)

        usuario_id = session.get('usuario_id')
        usuario_tipo = session.get('usuario_tipo')

        if usuario_tipo == 'ADM':
            return [Atividade(**atividade) for atividade in dados]

        if usuario_tipo == 'ALUNO':
            return [Atividade(**atividade) for atividade in dados if str(atividade.get('aluno_id')) == str(usuario_id)]

        # Para PROFESSOR e RESPONSAVEL
        # Observação: este projeto modela:
        # - Turma.aluno_ids / professor_ids
        # - Matéria.professor_id / turma_id
        # - Atividade.aluno_id (aluno)
        # Não há, atualmente, vínculo explícito de RESPONSAVEL->ALUNO nos JSONs. Então, RESPONSAVEL
        # será tratado como "não autorizado" (retorna lista vazia), a menos que você implemente este vínculo.
        if usuario_tipo not in ['PROFESSOR', 'RESPONSAVEL']:
            return []

        if usuario_tipo == 'RESPONSAVEL':
           return []
        # PROFESSOR: descobre as turmas atendidas por suas matérias e filtra pelos alunos destas turmas
        professor_id = str(usuario_id)
        turma_ids_atendidas = set()
        for m in materias:
            if str(m.professor_id) == professor_id:
                turma_ids_atendidas.add(str(m.turma_id))

        aluno_ids_permitidos = set()
        for t in turmas:
            if str(t.id) in turma_ids_atendidas:
                for aid in t.aluno_ids:
                    aluno_ids_permitidos.add(str(aid))

        # Retorna atividades cujo aluno_id esteja entre os alunos permitidos
        return [
            Atividade(**atividade)
            for atividade in dados
            if str(atividade.get('aluno_id')) in aluno_ids_permitidos
        ]

    except FileNotFoundError:
        return []


# salvar os usuários no arquivo JSON
def salvar_usuarios_json():
    with open("usuarios.json", "w") as arquivo:
        json.dump([usuario.to_dict() for usuario in usuarios], arquivo)

# salvar as atividades no arquivo JSON
def salvar_atividades_json():
    with open("atividades.json", "w") as arquivo:
        json.dump([atividade.to_dict() for atividade in atividades], arquivo)

def salvar_materias_json():
    with open("materias.json","w") as arquivo:
        json.dump([materia.to_dict() for materia in materias], arquivo)

def salvar_turmas_json():
    with open("turmas.json","w") as arquivo:
        json.dump([turma.to_dict() for turma in turmas], arquivo)

def criar_prontuario():
   
    letras = ''.join(random.choices(string.ascii_uppercase, k=3))
    numeros = ''.join(random.choices(string.digits, k=7))
    return letras + numeros

