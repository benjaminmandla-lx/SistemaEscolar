
import os
import random
import string
from datetime import datetime, date

from functools import wraps

from flask import (render_template,request,redirect,url_for,jsonify,session)
from sqlalchemy import func
from werkzeug.utils import secure_filename

from SAN import app, db
from SAN.modelos import (
    Usuario,
    Atividade,
    Materia,
    Turma
)


# ============================================================
# DECORADOR PARA PROTEGER ROTAS
# ============================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('login'))

        return f(*args, **kwargs)

    return decorated_function


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/")
@login_required
def home():
    return render_template("dashboard.html")


@app.route("/api/dados_dashboard")
@login_required
def api_dados_dashboard():

    usuario_id = session.get("usuario_id")
    usuario_tipo = session.get("usuario_tipo")

    # --------------------------------------------------------
    # Define quais atividades o usuário pode visualizar
    # --------------------------------------------------------

    if usuario_tipo == "ALUNO":

        atividades = Atividade.query.filter_by(
            aluno_id=usuario_id
        ).order_by(
            Atividade.data.asc()
        ).all()

    elif usuario_tipo == "PROFESSOR":

        professor = Usuario.query.get(usuario_id)

        if not professor:
            return jsonify({
                "media_geral": 0,
                "total_atividades": 0,
                "total_materias": 0,
                "notas_por_data": [],
                "atividades_por_materia": {},
                "recentes": []
            })

        alunos_ids = set()

        for turma in professor.turmas_professor.all():

            for aluno in turma.alunos.all():
                alunos_ids.add(aluno.id)

        if alunos_ids:

            atividades = Atividade.query.filter(
                Atividade.aluno_id.in_(alunos_ids)
            ).order_by(
                Atividade.data.asc()
            ).all()

        else:
            atividades = []

    elif usuario_tipo == "ADM":

        atividades = Atividade.query.order_by(
            Atividade.data.asc()
        ).all()
    elif usuario_tipo == "RESPONSAVEL":

        responsavel = Usuario.query.get(usuario_id)

        if not responsavel:
            atividades = []
        else:
            alunos_ids = [a.id for a in responsavel.alunos_responsavel.all()]

            if alunos_ids:
                atividades = Atividade.query.filter(
                    Atividade.aluno_id.in_(alunos_ids)
                ).order_by(
                    Atividade.data.asc()
                ).all()
            else:
                atividades = []
    else:

        atividades = []

    # --------------------------------------------------------
    # Média geral
    # --------------------------------------------------------

    notas = [
        float(a.nota)
        for a in atividades
        if a.nota is not None
    ]

    if notas:
        media_geral = sum(notas) / len(notas)
    else:
        media_geral = 0

    # --------------------------------------------------------
    # Total de atividades
    # --------------------------------------------------------

    total_atividades = len(atividades)

    # --------------------------------------------------------
    # Total de matérias
    # --------------------------------------------------------

    materias_ids = set()

    for atividade in atividades:

        if atividade.materia_id:
            materias_ids.add(atividade.materia_id)

    total_materias = len(materias_ids)

    # --------------------------------------------------------
    # Notas por atividade
    # --------------------------------------------------------

    notas_por_data = []

    for atividade in atividades:

        notas_por_data.append({
            "data": (
                atividade.data.strftime("%Y-%m-%d")
                if atividade.data
                else None
            ),
            "nota": float(
                atividade.nota
                if atividade.nota is not None
                else 0
            ),
            "atividade": atividade.tipoativ,
            "materia": (
                atividade.materia.nome_materia
                if atividade.materia
                else "Sem matéria"
            )
        })

    # --------------------------------------------------------
    # Atividades por matéria
    # --------------------------------------------------------

    atividades_por_materia = {}

    for atividade in atividades:

        if atividade.materia:

            nome_materia = atividade.materia.nome_materia

        else:

            nome_materia = "Sem matéria"

        if nome_materia not in atividades_por_materia:
            atividades_por_materia[nome_materia] = 0

        atividades_por_materia[nome_materia] += 1

    # --------------------------------------------------------
    # Últimas atividades
    # --------------------------------------------------------

    recentes = sorted(
        atividades,
        key=lambda a: a.data if a.data else date.min,
        reverse=True
    )[:5]

    lista_recentes = []

    for atividade in recentes:

        lista_recentes.append({
            "data": (
                atividade.data.strftime("%d/%m/%Y")
                if atividade.data
                else "-"
            ),

            "atividade": atividade.tipoativ,

            "materia": (
                atividade.materia.nome_materia
                if atividade.materia
                else "Sem matéria"
            ),

            "nota": (
                float(atividade.nota)
                if atividade.nota is not None
                else None
            )
        })

    # --------------------------------------------------------
    # Retorno JSON
    # --------------------------------------------------------

    return jsonify({

        "media_geral": round(media_geral, 2),

        "total_atividades": total_atividades,

        "total_materias": total_materias,

        "notas_por_data": notas_por_data,

        "atividades_por_materia": atividades_por_materia,

        "recentes": lista_recentes
    })


# ============================================================
# LOGIN
# ============================================================

@app.route("/login")
def login():

    # Cria o administrador automaticamente caso não exista
    administrador = Usuario.query.filter_by(tipo="ADM").first()

    if administrador is None:

        administrador = Usuario(
            nome="Administrador",
            email="admin@admin.com",
            data_nascimento=date(2000, 1, 1),
            tipo="ADM",
            prontuario="ADMIN",
            foto=None
        )
        administrador.senha_criptografada = "admin123"
        db.session.add(administrador)
        db.session.commit()

    return render_template(
        "login.html",
        resultado=None
    )


# ============================================================
# AUTENTICAÇÃO
# ============================================================

@app.route("/autenticar", methods=["POST"])
def autenticar():

    prontuario = request.form.get("prontuario")
    senha = request.form.get("senha")

    usuario = Usuario.query.filter_by(
        prontuario=prontuario,
    ).first()

    if usuario and usuario.verificar_senha(senha):

        session.permanent = True

        session["usuario_tipo"] = usuario.tipo
        session["usuario_id"] = usuario.id
        session["usuario"] = usuario.prontuario
        session["nome_usuario"] = usuario.nome

        return redirect(url_for("home"))

    return render_template(
        "login.html",
        resultado="falha"
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ============================================================
# CADASTRO DE USUÁRIO
# ============================================================

@app.route("/cadastro_usuario", methods=["GET"])
def cadastro_usuario():

    return render_template(
        "cadastro_usuario.html",
        resultado=None
    )


# ============================================================
# CADASTRO DE ALUNO
# ============================================================

@app.route("/cadastro_aluno", methods=["GET"])
def cadastro_aluno():

    turmas = Turma.query.all()

    return render_template(
        "cadastro_aluno.html",
        resultado=None,
        turmas=turmas
    )


# ============================================================
# LISTAR ALUNOS
# ============================================================

@app.route("/listar_alunos")
@login_required
def listar_alunos():

    usuario_tipo = session.get("usuario_tipo")
    usuario_id = session.get("usuario_id")

    # --------------------------------------------------------
    # ADM
    # --------------------------------------------------------

    if usuario_tipo == "ADM":

        alunos = Usuario.query.filter_by(
            tipo="ALUNO"
        ).all()

        return render_template(
            "listar_alunos.html",
            alunos=alunos
        )

    # --------------------------------------------------------
    # ALUNO
    # --------------------------------------------------------

    if usuario_tipo == "ALUNO":

        aluno = Usuario.query.filter_by(
            id=usuario_id,
            tipo="ALUNO"
        ).first()

        alunos = [aluno] if aluno else []

        return render_template(
            "listar_alunos.html",
            alunos=alunos
        )

    # --------------------------------------------------------
    # PROFESSOR
    # --------------------------------------------------------

    if usuario_tipo == "PROFESSOR":

        professor = Usuario.query.get(usuario_id)

        if not professor:
            return render_template(
                "listar_alunos.html",
                alunos=[]
            )

        # Turmas atendidas pelo professor
        turmas_professor = professor.turmas_professor.all()

        alunos_ids = set()

        for turma in turmas_professor:

            for aluno in turma.alunos.all():
                alunos_ids.add(aluno.id)

        alunos = Usuario.query.filter(
            Usuario.tipo == "ALUNO",
            Usuario.id.in_(alunos_ids)
        ).all() if alunos_ids else []

        return render_template(
            "listar_alunos.html",
            alunos=alunos
        )

    return render_template(
        "listar_alunos.html",
        alunos=[]
    )


# ============================================================
# CADASTRO DE PROFESSOR
# ============================================================

@app.route("/cadastro_professor", methods=["GET"])
def cadastro_professor():

    turmas = Turma.query.all()

    return render_template(
        "cadastro_professor.html",
        resultado=None,
        turmas=turmas
    )


# ============================================================
# CADASTRO DE RESPONSÁVEL
# ============================================================

@app.route("/cadastro_responsavel", methods=["GET"])
def cadastro_responsavel():
    aluno_id = session.get("aluno_id_para_responsavel")

    aluno = None
    if aluno_id:
        aluno = Usuario.query.filter_by(id=aluno_id, tipo="ALUNO").first()

    return render_template(
        "cadastro_responsavel.html",
        resultado=None,
        aluno=aluno
    )


# ============================================================
# SALVAR USUÁRIO
# ============================================================

@app.route("/salvar_usuario", methods=["POST"])
def salvar_usuario():

    nome = request.form.get("nome")
    senha = request.form.get("senha")
    data_nascimento = request.form.get("data_nascimento")
    tipo = request.form.get("tipo")
    turma_id = request.form.get("turma")
    responsavel_legal = request.form.get("responsavel_legal")

    prontuario = criar_prontuario()

    # O formulário atual não envia e-mail
    email = gerar_email(nome, tipo, prontuario)

    if not nome or not senha or not data_nascimento or not tipo:
        return render_template(
            "dashboard.html",
            resultado="falha"
        )

    # --------------------------------------------------------
    # Converte a data para date
    # --------------------------------------------------------

    try:

        data_nascimento_obj = datetime.strptime(
            data_nascimento,
            "%Y-%m-%d"
        ).date()

    except ValueError:

        return render_template(
            "dashboard.html",
            resultado="falha"
        )

    # --------------------------------------------------------
    # Calcula idade
    # --------------------------------------------------------

    hoje = date.today()

    idade = (
        hoje.year
        - data_nascimento_obj.year
        - (
            (hoje.month, hoje.day)
            < (
                data_nascimento_obj.month,
                data_nascimento_obj.day
            )
        )
    )

    # --------------------------------------------------------
    # Cria usuário
    # --------------------------------------------------------

    novo_usuario = Usuario(
    nome=nome,
    email=email,
    data_nascimento=data_nascimento_obj,
    tipo=tipo,
    prontuario=prontuario,
    foto=None)
    novo_usuario.senha_criptografada = senha   # ✅ agora criptografa
    db.session.add(novo_usuario)
    db.session.flush()

    # Flush para obter o ID antes do commit
    db.session.flush()

    # --------------------------------------------------------
    # Relaciona usuário com turma
    # --------------------------------------------------------

    if turma_id:

        turma = Turma.query.get(int(turma_id))

        if turma:

            if tipo == "ALUNO":

                if novo_usuario not in turma.alunos.all():
                    turma.alunos.append(novo_usuario)

            elif tipo == "PROFESSOR":

                if novo_usuario not in turma.professores.all():
                    turma.professores.append(novo_usuario)

    db.session.commit()

    # --------------------------------------------------------
    # Cadastro de responsável
    # --------------------------------------------------------

    if tipo == "ALUNO":

        if idade < 18 or responsavel_legal == "SIM":

            session["aluno_id_para_responsavel"] = novo_usuario.id

            return redirect(
                url_for("cadastro_responsavel")
            )

    return render_template(
        "dashboard.html",
        resultado="cadastrado"
    )

@app.route("/salvar_responsavel", methods=["POST"])
def salvar_responsavel():

    nome = request.form.get("nome")
    senha = request.form.get("senha")
    data_nascimento = request.form.get("data_nascimento")
    email = request.form.get("email")
    # tipo vem do form, mas ignoramos — é sempre RESPONSAVEL

    aluno_id = session.get("aluno_id_para_responsavel")

    if not nome or not senha or not data_nascimento:
        return render_template(
            "cadastro_responsavel.html",
            resultado="falha",
            aluno=Usuario.query.get(aluno_id) if aluno_id else None
        )

    try:
        data_nascimento_obj = datetime.strptime(
            data_nascimento, "%Y-%m-%d"
        ).date()
    except ValueError:
        return render_template(
            "cadastro_responsavel.html",
            resultado="falha",
            aluno=Usuario.query.get(aluno_id) if aluno_id else None
        )

    # --------------------------------------------------------
    # Gera prontuário e e-mail se não vierem do form
    # --------------------------------------------------------
    prontuario = criar_prontuario()

    if not email:
        email = gerar_email(nome, "RESPONSAVEL", prontuario)

    # Evita duplicidade de e-mail (o form não tem campo de email, mas garantimos)
    if Usuario.query.filter_by(email=email).first():
        return render_template(
            "cadastro_responsavel.html",
            resultado="email_existe",
            aluno=Usuario.query.get(aluno_id) if aluno_id else None
        )

    # --------------------------------------------------------
    # Cria o responsável (SENHA CRIPTOGRAFADA!)
    # --------------------------------------------------------
    responsavel = Usuario(
        nome=nome,
        email=email,
        data_nascimento=data_nascimento_obj,
        tipo="RESPONSAVEL",
        prontuario=prontuario,
        foto=None
    )
    responsavel.senha_criptografada = senha   # ✅ passa pelo setter

    db.session.add(responsavel)
    db.session.flush()   # garante id antes de vincular

    # --------------------------------------------------------
    # Vincula ao aluno, se houver
    # --------------------------------------------------------
    if aluno_id:
        aluno = Usuario.query.filter_by(id=aluno_id, tipo="ALUNO").first()

        if aluno and aluno not in responsavel.alunos_responsavel.all():
            responsavel.alunos_responsavel.append(aluno)

    db.session.commit()

    # Limpa a sessão do fluxo de cadastro
    session.pop("aluno_id_para_responsavel", None)

    return render_template(
        "dashboard.html",
        resultado="cadastrado"
    )
# ============================================================
# CADASTRO DE MATÉRIA
# ============================================================

@app.route("/cadastro_materia", methods=["GET"])
def cadastro_materia():

    materias = Materia.query.all()
    usuarios = Usuario.query.all()
    turmas = Turma.query.all()

    return render_template(
        "cadastro_materia.html",
        id=0,
        materia=None,
        materias=materias,
        usuarios=usuarios,
        turmas=turmas
    )


# ============================================================
# SALVAR MATÉRIA
# ============================================================

@app.route("/salvar_materia/<int:id>", methods=["POST"])
@login_required
def salvar_materia(id):

    nome_materia = request.form.get("materia")
    professor_id = request.form.get("professor_id")
    turma_id = request.form.get("turma_id")

    if not nome_materia:
        return redirect(url_for("home"))

    # --------------------------------------------------------
    # EDITAR
    # --------------------------------------------------------

    if id > 0:

        materia = Materia.query.get(id)

        if not materia:
            return redirect(url_for("home"))

        materia.nome_materia = nome_materia

        if professor_id:
            materia.professor_id = int(professor_id)

        if turma_id:
            materia.turma_id = int(turma_id)

    # --------------------------------------------------------
    # CRIAR
    # --------------------------------------------------------

    else:

        if not professor_id or not turma_id:
            return redirect(url_for("home"))

        materia = Materia(
            nome_materia=nome_materia,
            professor_id=int(professor_id),
            turma_id=int(turma_id)
        )

        db.session.add(materia)

    # --------------------------------------------------------
    # RELACIONA PROFESSOR À TURMA
    # --------------------------------------------------------

    if professor_id and turma_id:

        professor = Usuario.query.get(int(professor_id))
        turma = Turma.query.get(int(turma_id))

        if professor and turma:

            if professor not in turma.professores.all():
                turma.professores.append(professor)

    db.session.commit()

    return redirect(url_for("home"))


# ============================================================
# CADASTRO DE TURMA
# ============================================================

@app.route("/cadastro_turma", methods=["GET"])
def cadastro_turma():

    turmas = Turma.query.all()

    return render_template(
        "cadastro_turma.html",
        id=0,
        turma=None,
        turmas=turmas
    )


# ============================================================
# SALVAR TURMA
# ============================================================

@app.route("/salvar_turma/<int:id>", methods=["POST"])
@login_required
def salvar_turma(id):

    nome_turma = request.form.get("nome_turma")

    if not nome_turma:
        return redirect(url_for("home"))

    nome_turma = nome_turma.strip()

    # --------------------------------------------------------
    # VERIFICA SE JÁ EXISTE
    # --------------------------------------------------------

    turma_existente = Turma.query.filter(
        Turma.nome_turma == nome_turma,
        Turma.id != id
    ).first()

    if turma_existente:
        turmas = Turma.query.all()

        return render_template(
            "cadastro_turma.html",
            id=id,
            turma=None,
            turmas=turmas,
            resultado="turma_existe"
        )

    # --------------------------------------------------------
    # EDITAR
    # --------------------------------------------------------

    if id > 0:

        turma = Turma.query.get(id)

        if not turma:
            return redirect(url_for("home"))

        turma.nome_turma = nome_turma

    # --------------------------------------------------------
    # CRIAR
    # --------------------------------------------------------

    else:

        turma = Turma(
            nome_turma=nome_turma
        )

        db.session.add(turma)

    # --------------------------------------------------------
    # SALVAR NO BANCO
    # --------------------------------------------------------

    db.session.commit()

    return redirect(url_for("home"))


# ============================================================
# CADASTRO DE ATIVIDADE
# ============================================================

@app.route("/cadastro_atividade", methods=["GET"])
@login_required
def cadastro_atividade():

    usuario_tipo = session.get("usuario_tipo")

    # Somente ADM e PROFESSOR
    if usuario_tipo not in ["ADM", "PROFESSOR"]:
        return redirect(
            url_for("home")
        )

    materias = Materia.query.all()

    # --------------------------------------------------------
    # ADM pode selecionar qualquer aluno
    # --------------------------------------------------------

    if usuario_tipo == "ADM":

        usuarios_alunos_permitidos = Usuario.query.filter_by(
            tipo="ALUNO"
        ).all()

    # --------------------------------------------------------
    # Professor só vê alunos de suas turmas
    # --------------------------------------------------------

    else:

        professor = Usuario.query.get(
            session.get("usuario_id")
        )

        alunos_ids = set()

        if professor:

            turmas_professor = (
                professor.turmas_professor.all()
            )

            for turma in turmas_professor:

                for aluno in turma.alunos.all():
                    alunos_ids.add(aluno.id)

        if alunos_ids:

            usuarios_alunos_permitidos = Usuario.query.filter(
                Usuario.tipo == "ALUNO",
                Usuario.id.in_(alunos_ids)
            ).all()

        else:

            usuarios_alunos_permitidos = []

    return render_template(
        "cadastro_atividade.html",
        id=0,
        atividade=None,
        atividades=Atividade.query.all(),
        materias=materias,
        usuarios=usuarios_alunos_permitidos
    )


# ============================================================
# SALVAR ATIVIDADE
# ============================================================

@app.route("/salvar_atividade/<int:id>", methods=["POST"])
@login_required
def salvar_atividade(id):

    materia_id = request.form.get(
        "nome_materia"
    )

    tipoativ = request.form.get(
        "tipoativ"
    )

    nota = request.form.get(
        "nota"
    )

    data = request.form.get(
        "data"
    )

    usuario_tipo = session.get(
        "usuario_tipo"
    )

    # --------------------------------------------------------
    # Verificação dos campos
    # --------------------------------------------------------

    if not materia_id or not tipoativ or not nota or not data:
        return redirect(
            url_for("home")
        )

    # --------------------------------------------------------
    # Define o aluno
    # --------------------------------------------------------

    if usuario_tipo in [
        "ADM",
        "ADMIN",
        "PROFESSOR"
    ]:

        aluno_id = request.form.get(
            "nome_aluno"
        )

    else:

        aluno_id = session.get(
            "usuario_id"
        )

    if not aluno_id:
        return redirect(
            url_for("home")
        )

    # --------------------------------------------------------
    # Converte valores
    # --------------------------------------------------------

    try:

        materia_id = int(materia_id)
        aluno_id = int(aluno_id)

        nota = float(nota)

        data_obj = datetime.strptime(
            data,
            "%Y-%m-%d"
        ).date()

    except (ValueError, TypeError):

        return redirect(
            url_for("home")
        )

    # --------------------------------------------------------
    # Busca matéria
    # --------------------------------------------------------

    materia = Materia.query.get(
        materia_id
    )

    if not materia:
        return redirect(
            url_for("home")
        )

    # --------------------------------------------------------
    # Busca aluno
    # --------------------------------------------------------

    aluno = Usuario.query.filter_by(
        id=aluno_id,
        tipo="ALUNO"
    ).first()

    if not aluno:
        return redirect(
            url_for("home")
        )

    # --------------------------------------------------------
    # Define professor
    # --------------------------------------------------------

    if usuario_tipo == "PROFESSOR":

        professor_id = session.get(
            "usuario_id"
        )

    else:

        professor_id = materia.professor_id

    # --------------------------------------------------------
    # Edição
    # --------------------------------------------------------

    if id > 0:

        atividade = Atividade.query.get(
            id
        )

        if atividade:

            atividade.materia_id = materia_id
            atividade.tipoativ = tipoativ
            atividade.nota = nota
            atividade.data = data_obj
            atividade.professor_id = professor_id
            atividade.aluno_id = aluno_id

        else:

            atividade = Atividade(
                materia_id=materia_id,
                tipoativ=tipoativ,
                nota=nota,
                data=data_obj,
                professor_id=professor_id,
                aluno_id=aluno_id
            )

            db.session.add(atividade)

    # --------------------------------------------------------
    # Cadastro
    # --------------------------------------------------------

    else:

        atividade = Atividade(
            materia_id=materia_id,
            tipoativ=tipoativ,
            nota=nota,
            data=data_obj,
            professor_id=professor_id,
            aluno_id=aluno_id
        )

        db.session.add(atividade)

    # --------------------------------------------------------
    # Garante que o aluno esteja na turma da matéria
    # --------------------------------------------------------

    turma = materia.turma

    if turma:

        if aluno not in turma.alunos.all():
            turma.alunos.append(aluno)

    db.session.commit()

    return redirect(
        url_for("home")
    )


# ============================================================
# EDITAR ATIVIDADE
# ============================================================

@app.route("/editar/<int:id>")
@login_required
def exibir_edicao(id):

    usuario_tipo = session.get(
        "usuario_tipo"
    )

    usuario_id = session.get(
        "usuario_id"
    )

    atividade = Atividade.query.get(
        id
    )

    if not atividade:
        return redirect(
            url_for("home")
        )

    # --------------------------------------------------------
    # ADM pode editar qualquer atividade
    # --------------------------------------------------------

    if usuario_tipo == "ADM":

        permitido = True

    # --------------------------------------------------------
    # ALUNO só pode editar a própria atividade
    # --------------------------------------------------------

    elif usuario_tipo == "ALUNO":

        permitido = (
            atividade.aluno_id == usuario_id
        )

    else:

        permitido = False

    if permitido:

        return render_template(
            "cadastro_atividade.html",
            atividade=atividade,
            id=id,
            resultado=None,
            materias=Materia.query.all(),
            usuarios=Usuario.query.filter_by(
                tipo="ALUNO"
            ).all()
        )

    return redirect(
        url_for("home")
    )


# ============================================================
# EXCLUIR ATIVIDADE
# ============================================================

@app.route("/excluir_atividade/<int:id>")
@login_required
def excluir_atividade(id):

    usuario_tipo = session.get(
        "usuario_tipo"
    )

    usuario_id = session.get(
        "usuario_id"
    )

    atividade = Atividade.query.get(
        id
    )

    if not atividade:
        return redirect(
            url_for("home")
        )

    # --------------------------------------------------------
    # ADM pode excluir qualquer atividade
    # --------------------------------------------------------

    if usuario_tipo == "ADM":

        permitido = True

    # --------------------------------------------------------
    # ALUNO só pode excluir a própria atividade
    # --------------------------------------------------------

    elif usuario_tipo == "ALUNO":

        permitido = (
            atividade.aluno_id == usuario_id
        )

    else:

        permitido = False

    if permitido:

        db.session.delete(
            atividade
        )

        db.session.commit()

    return redirect(
        url_for("home")
    )


# ============================================================
# PERFIL
# ============================================================

@app.route("/perfil")
@login_required
def perfil():

    usuario = Usuario.query.get(
        session.get("usuario_id")
    )

    return render_template(
        "perfil.html",
        usuario=usuario
    )


# ============================================================
# ATUALIZAR PERFIL
# ============================================================

@app.route("/atualizar_perfil", methods=["POST"])
@login_required
def atualizar_perfil():

    nome = request.form.get(
        "nome"
    )

    email = request.form.get(
        "email"
    )

    data_nascimento = request.form.get(
        "data_nascimento"
    )

    genero = request.form.get(
        "genero"
    )

    foto = upload_imagem()

    usuario = Usuario.query.get(
        session.get("usuario_id")
    )

    if not usuario:
        return redirect(
            url_for("home")
        )

    if nome and email and data_nascimento and genero:

        try:

            data_nascimento_obj = datetime.strptime(
                data_nascimento,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            return redirect(
                url_for("home")
            )

        usuario.nome = nome
        usuario.email = email
        usuario.data_nascimento = data_nascimento_obj

        # Mantém o campo genero somente se existir no modelo
        if hasattr(usuario, "genero"):
            usuario.genero = genero

        if foto is not None:
            usuario.foto = foto

        db.session.commit()

        session["nome_usuario"] = usuario.nome

        return render_template(
            "perfil.html",
            usuario=usuario,
            resultado="atualizado"
        )

    return redirect(
        url_for("home")
    )


# ============================================================
# UPLOAD DE IMAGEM
# ============================================================

def upload_imagem():
    arquivo = request.files.get("foto")
    
    if arquivo:
        nome_seguro = secure_filename(arquivo.filename)
        caminho = os.path.join("SAN/static/uploads", nome_seguro)
        arquivo.save(caminho)
        caminho =caminho.replace('\\', '/')
        caminho = caminho.replace('SAN/', '')
        return caminho
    return None


# ============================================================
# LER ATIVIDADES DO USUÁRIO LOGADO
# ============================================================

def ler_atividades_usuario():

    usuario_id = session.get(
        "usuario_id"
    )

    usuario_tipo = session.get(
        "usuario_tipo"
    )

    # --------------------------------------------------------
    # ADM
    # --------------------------------------------------------

    if usuario_tipo == "ADM":

        return Atividade.query.order_by(
            Atividade.data.desc()
        ).all()

    # --------------------------------------------------------
    # ALUNO
    # --------------------------------------------------------

    if usuario_tipo == "ALUNO":

        return Atividade.query.filter_by(
            aluno_id=usuario_id
        ).order_by(
            Atividade.data.desc()
        ).all()

    # --------------------------------------------------------
    # RESPONSÁVEL
    # --------------------------------------------------------

    if usuario_tipo == "RESPONSAVEL":

        responsavel = Usuario.query.get(usuario_id)

        if not responsavel:
            return []

        alunos_ids = [a.id for a in responsavel.alunos_responsavel.all()]

        if not alunos_ids:
            return []

        return Atividade.query.filter(
            Atividade.aluno_id.in_(alunos_ids)
        ).order_by(
            Atividade.data.desc()
        ).all()

    # --------------------------------------------------------
    # PROFESSOR
    # --------------------------------------------------------

    if usuario_tipo == "PROFESSOR":

        professor = Usuario.query.get(
            usuario_id
        )

        if not professor:
            return []

        # Descobre as turmas do professorF
        turmas_professor = (
            professor.turmas_professor.all()
        )

        alunos_ids = set()

        for turma in turmas_professor:

            for aluno in turma.alunos.all():

                alunos_ids.add(
                    aluno.id
                )

        if not alunos_ids:
            return []

        return Atividade.query.filter(
            Atividade.aluno_id.in_(
                alunos_ids
            )
        ).order_by(
            Atividade.data.desc()
        ).all()

    return []

# ============================================================
# ESTATÍSTICAS
# ============================================================

@app.route("/estatisticas")
@login_required
def estatisticas():

    return render_template(
        "estatisticas.html"
    )


# ============================================================
# API - NOTAS POR ATIVIDADE
# ============================================================

@app.route("/api/notas_por_atividade")
@login_required
def api_notas_por_atividade():

    usuario_id = session.get("usuario_id")
    usuario_tipo = session.get("usuario_tipo")

    # --------------------------------------------------------
    # ALUNO
    # --------------------------------------------------------

    if usuario_tipo == "ALUNO":

        atividades = Atividade.query.filter_by(
            aluno_id=usuario_id
        ).order_by(
            Atividade.data.asc()
        ).all()

    # --------------------------------------------------------
    # PROFESSOR
    # --------------------------------------------------------

    elif usuario_tipo == "PROFESSOR":

        professor = Usuario.query.get(
            usuario_id
        )

        if not professor:
            return jsonify([])

        turmas = professor.turmas_professor.all()

        alunos_ids = set()

        for turma in turmas:

            for aluno in turma.alunos.all():
                alunos_ids.add(aluno.id)

        if not alunos_ids:
            return jsonify([])

        atividades = Atividade.query.filter(
            Atividade.aluno_id.in_(alunos_ids)
        ).order_by(
            Atividade.data.asc()
        ).all()

    # --------------------------------------------------------
    # ADM
    # --------------------------------------------------------

    elif usuario_tipo == "ADM":

        atividades = Atividade.query.order_by(
            Atividade.data.asc()
        ).all()
    elif usuario_tipo == "RESPONSAVEL":

        responsavel = Usuario.query.get(usuario_id)

        if not responsavel:
            atividades = []
        else:
            alunos_ids = [a.id for a in responsavel.alunos_responsavel.all()]

            if alunos_ids:
                atividades = Atividade.query.filter(
                    Atividade.aluno_id.in_(alunos_ids)
                ).order_by(
                    Atividade.data.asc()
                ).all()
            else:
                atividades = []
    else:

        atividades = []

    # --------------------------------------------------------
    # Monta o JSON
    # --------------------------------------------------------

    dados_grafico = []

    for atividade in atividades:

        dados_grafico.append({
            "data": (
                atividade.data.strftime("%Y-%m-%d")
                if atividade.data
                else None
            ),

            "atividade": atividade.tipoativ,

            "nota": float(
                atividade.nota
                if atividade.nota is not None
                else 0
            ),

            "materia": (
                atividade.materia.nome_materia
                if atividade.materia
                else "Sem matéria"
            ),

            "aluno": (
                atividade.aluno.nome
                if atividade.aluno
                else "Aluno não encontrado"
            )
        })

    return jsonify(
        dados_grafico
    )


# ============================================================
# API - ATIVIDADES POR MATÉRIA
# ============================================================

@app.route("/api/atividades_por_materia")
@login_required
def api_atividades_por_materia():

    usuario_id = session.get("usuario_id")
    usuario_tipo = session.get("usuario_tipo")

    # --------------------------------------------------------
    # ALUNO
    # --------------------------------------------------------

    if usuario_tipo == "ALUNO":

        resultados = db.session.query(
            Materia.nome_materia,
            func.count(Atividade.id).label("total")
        ).join(
            Atividade,
            Atividade.materia_id == Materia.id
        ).filter(
            Atividade.aluno_id == usuario_id
        ).group_by(
            Materia.id,
            Materia.nome_materia
        ).all()

    # --------------------------------------------------------
    # PROFESSOR
    # --------------------------------------------------------

    elif usuario_tipo == "PROFESSOR":

        professor = Usuario.query.get(
            usuario_id
        )

        if not professor:
            return jsonify({})

        turmas = professor.turmas_professor.all()

        alunos_ids = set()

        for turma in turmas:

            for aluno in turma.alunos.all():
                alunos_ids.add(aluno.id)

        if not alunos_ids:
            return jsonify({})

        resultados = db.session.query(
            Materia.nome_materia,
            func.count(Atividade.id).label("total")
        ).join(
            Atividade,
            Atividade.materia_id == Materia.id
        ).filter(
            Atividade.aluno_id.in_(alunos_ids)
        ).group_by(
            Materia.id,
            Materia.nome_materia
        ).all()

    # --------------------------------------------------------
    # ADM
    # --------------------------------------------------------

    elif usuario_tipo == "ADM":

        resultados = db.session.query(
            Materia.nome_materia,
            func.count(Atividade.id).label("total")
        ).join(
            Atividade,
            Atividade.materia_id == Materia.id
        ).group_by(
            Materia.id,
            Materia.nome_materia
        ).all()
    elif usuario_tipo == "RESPONSAVEL":

        responsavel = Usuario.query.get(usuario_id)

        if not responsavel:
            return jsonify({})

        alunos_ids = [a.id for a in responsavel.alunos_responsavel.all()]

        if not alunos_ids:
            return jsonify({})

        resultados = db.session.query(
            Materia.nome_materia,
            func.count(Atividade.id).label("total")
        ).join(
            Atividade, Atividade.materia_id == Materia.id
        ).filter(
            Atividade.aluno_id.in_(alunos_ids)
        ).group_by(
            Materia.id, Materia.nome_materia
        ).all()
    else:

        resultados = []

    # --------------------------------------------------------
    # Converte para JSON
    # --------------------------------------------------------

    dados_agrupados = {
        resultado.nome_materia: resultado.total
        for resultado in resultados
    }

    return jsonify(
        dados_agrupados
    )


# ============================================================
# CRIAR PRONTUÁRIO
# ============================================================

def criar_prontuario():

    # Tenta gerar um prontuário único
    while True:

        letras = ''.join(
            random.choices(
                string.ascii_uppercase,
                k=3
            )
        )

        numeros = ''.join(
            random.choices(
                string.digits,
                k=7
            )
        )

        prontuario = letras + numeros

        existente = Usuario.query.filter_by(
            prontuario=prontuario
        ).first()

        if existente is None:
            return prontuario

def gerar_email(nome: str, tipo: str, prontuario: str) -> str:
    """
    Gera um email institucional para professores e alunos.
    - Professores: nome.sobrenome@prof.ifsp.edu.br
    - Alunos: prontuario@aluno.ifsp.edu.br
    """
    nome = nome.strip().lower().replace(" ", ".")
    
    if tipo.upper() == "PROFESSOR":
        email = f"{nome}@prof.ifsp.edu.br"
    elif tipo.upper() == "ALUNO":
        email = f"{prontuario.lower()}@aluno.ifsp.edu.br"
    elif tipo.upper() == "RESPONSAVEL":
        email = f"{prontuario.lower()}@responsavel.ifsp.edu.br"
    else:
        raise ValueError("Tipo de usuário inválido. Use 'PROFESSOR', 'ALUNO' ou 'RESPONSAVEL'.")
    
    return email

# ============================================================
# QUADRO DE LÍDERES
# ============================================================

@app.route("/quadro_lideres")
@login_required
def quadro_lideres():

    # Busca somente alunos que possuem atividades/notas
    ranking = db.session.query(
        Usuario,
        func.avg(Atividade.nota).label("media"),
        func.count(Atividade.id).label("total_atividades")
    ).join(
        Atividade,
        Usuario.id == Atividade.aluno_id
    ).filter(
        Usuario.tipo == "ALUNO",
        Atividade.nota.isnot(None)
    ).group_by(
        Usuario.id
    ).order_by(
        func.avg(Atividade.nota).desc()
    ).all()

    return render_template(
        "quadro_lideres.html",
        ranking=ranking
    )

# ============================================================
# Conquistas
# ============================================================
    
@app.route("/conquistas")
@login_required
def conquistas():
    usuario_id = session.get("usuario_id")

    usuario_atual = Usuario.query.get(usuario_id)

    # Conta quantas atividades o aluno possui em cada matéria
    resultados = db.session.query(
        Atividade.materia_id,
        func.count(Atividade.id).label("total")
    ).filter(
        Atividade.aluno_id == usuario_id
    ).group_by(
        Atividade.materia_id
    ).all()

    conquistas_por_materia = []

    for resultado in resultados:

        materia = Materia.query.get(resultado.materia_id)

        if not materia:
            continue

        total = resultado.total
        nome_materia = materia.nome_materia

        # -----------------------------
        # DEFINIÇÃO DO NÍVEL
        # -----------------------------

        if total < 5:
            nivel_atual = "Iniciante"
            badge_ativo = "badge_initial"
            proximo_badge = "Bronze"
            atividades_restantes = 5 - total
            progresso = (total / 5) * 100

        elif total < 10:
            nivel_atual = "Bronze"
            badge_ativo = "badge_bronze"
            proximo_badge = "Prata"
            atividades_restantes = 10 - total
            progresso = ((total - 5) / 5) * 100

        elif total < 15:
            nivel_atual = "Prata"
            badge_ativo = "badge_silver"
            proximo_badge = "Ouro"
            atividades_restantes = 15 - total
            progresso = ((total - 10) / 5) * 100

        elif total < 20:
            nivel_atual = "Ouro"
            badge_ativo = "badge_gold"
            proximo_badge = "Platino"
            atividades_restantes = 20 - total
            progresso = ((total - 15) / 5) * 100

        else:
            nivel_atual = "Platino"
            badge_ativo = "badge_platinum"
            proximo_badge = None
            atividades_restantes = 0
            progresso = 100

        conquistas_por_materia.append({
            "materia": nome_materia,
            "total": total,
            "nivel": nivel_atual,
            "badge": badge_ativo,
            "proximo": proximo_badge,
            "restantes": atividades_restantes,
            "progresso": int(progresso)
        })

    return render_template(
        "conquistas.html",
        usuario=usuario_atual,
        conquistas=conquistas_por_materia
    )