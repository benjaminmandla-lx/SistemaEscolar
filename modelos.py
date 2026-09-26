from datetime import date
from SAN import db,bcrypt


# ============================================================
# TABELA DE ASSOCIAÇÃO: ALUNOS <-> TURMAS
# ============================================================

aluno_turma = db.Table('aluno_turma',
    db.Column('aluno_id',db.Integer,db.ForeignKey('usuarios.id'),primary_key=True),
    db.Column('turma_id',db.Integer, db.ForeignKey('turmas.id'),primary_key=True))


# ============================================================
# TABELA DE ASSOCIAÇÃO: PROFESSORES <-> TURMAS
# ============================================================

professor_turma = db.Table('professor_turma',
    db.Column('professor_id',db.Integer,db.ForeignKey('usuarios.id'),primary_key=True),
    db.Column('turma_id',db.Integer,db.ForeignKey('turmas.id'),primary_key=True))

# ============================================================
# TABELA DE ASSOCIAÇÃO: RESPONSÁVEIS <-> ALUNOS
# ============================================================

responsavel_aluno = db.Table('responsavel_aluno',
    db.Column('responsavel_id', db.Integer,
              db.ForeignKey('usuarios.id'), primary_key=True),
    db.Column('aluno_id', db.Integer,
              db.ForeignKey('usuarios.id'), primary_key=True)
)


# ============================================================
# USUARIO
# ============================================================

class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    data_nascimento = db.Column(db.Date, nullable=True)
    tipo = db.Column(db.String(20), nullable=False)
    prontuario = db.Column(db.String(30), unique=True, nullable=True)
    foto = db.Column(db.String(200), nullable=True)

    @property
    def senha_criptografada(self):
        return self.senha

    @senha_criptografada.setter
    def senha_criptografada(self, senha_texto):
        self.senha = bcrypt.generate_password_hash(senha_texto).decode('utf-8')

    def verificar_senha(self, senha_texto):
        return bcrypt.check_password_hash(self.senha, senha_texto)

    # --------------------------------------------------------
    # RELACIONAMENTOS
    # --------------------------------------------------------
    alunos_responsavel = db.relationship(
        'Usuario',
        secondary=responsavel_aluno,
        primaryjoin=lambda: Usuario.id == responsavel_aluno.c.responsavel_id,
        secondaryjoin=lambda: Usuario.id == responsavel_aluno.c.aluno_id,
        backref=db.backref('responsaveis_aluno', lazy='dynamic'),
        lazy='dynamic'
    )
    # Turmas em que o usuário é professor
    turmas_professor = db.relationship('Turma',secondary=professor_turma,back_populates='professores',lazy='dynamic')

    # Turmas em que o usuário é aluno
    turmas_aluno = db.relationship('Turma',secondary=aluno_turma,back_populates='alunos',lazy='dynamic')

    # Matérias ministradas pelo professor
    materias = db.relationship('Materia',back_populates='professor',foreign_keys='Materia.professor_id')

    # Atividades criadas pelo professor
    atividades_professor = db.relationship('Atividade',back_populates='professor',foreign_keys='Atividade.professor_id')

    # Atividades do aluno
    atividades_aluno = db.relationship('Atividade',back_populates='aluno',foreign_keys='Atividade.aluno_id')

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "senha": self.senha,
            "data_nascimento": (self.data_nascimento.isoformat() if self.data_nascimento else None),
            "tipo": self.tipo,
            "prontuario": self.prontuario,
            "foto": self.foto}


# ============================================================
# TURMA
# ============================================================

class Turma(db.Model):
    __tablename__ = 'turmas'
    
    id = db.Column(db.Integer,primary_key=True)
    nome_turma = db.Column( db.String(100),nullable=False)

    # --------------------------------------------------------
    # ALUNOS DA TURMA
    # --------------------------------------------------------

    alunos = db.relationship('Usuario',secondary=aluno_turma,back_populates='turmas_aluno',lazy='dynamic')

    # --------------------------------------------------------
    # PROFESSORES DA TURMA
    # --------------------------------------------------------

    professores = db.relationship('Usuario',secondary=professor_turma,back_populates='turmas_professor',lazy='dynamic')

    # --------------------------------------------------------
    # MATÉRIAS DA TURMA
    # --------------------------------------------------------

    materias = db.relationship('Materia',back_populates='turma', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            "id": self.id,
            "nome_turma": self.nome_turma,
            "aluno_ids": [aluno.id for aluno in self.alunos.all()],
            "professor_ids": [professor.id for professor in self.professores.all()]}


# ============================================================
# MATERIA
# ============================================================

class Materia(db.Model):
    __tablename__ = 'materias'

    id = db.Column(db.Integer,primary_key=True)
    nome_materia = db.Column(db.String(100),nullable=False)
    professor_id = db.Column(db.Integer,db.ForeignKey('usuarios.id'),nullable=False)
    turma_id = db.Column(db.Integer,db.ForeignKey('turmas.id'),nullable=False)


    # --------------------------------------------------------
    # PROFESSOR
    # --------------------------------------------------------

    professor = db.relationship('Usuario',back_populates='materias',foreign_keys=[professor_id])


    # --------------------------------------------------------
    # TURMA
    # --------------------------------------------------------

    turma = db.relationship('Turma',back_populates='materias')


    # --------------------------------------------------------
    # ATIVIDADES
    # --------------------------------------------------------

    atividades = db.relationship('Atividade',back_populates='materia',cascade='all, delete-orphan')


    def to_dict(self):
        return {
            "id": self.id,
            "nome_materia": self.nome_materia,
            "professor_id": self.professor_id,
            "turma_id": self.turma_id}


# ============================================================
# ATIVIDADE
# ============================================================

class Atividade(db.Model):
    __tablename__ = 'atividades'

    id = db.Column(db.Integer,primary_key=True)
    materia_id = db.Column(db.Integer,db.ForeignKey('materias.id'),nullable=False)
    tipoativ = db.Column(db.String(100),nullable=False)
    nota = db.Column(db.Float,nullable=True)
    data = db.Column(db.Date,nullable=False,default=date.today)
    professor_id = db.Column(db.Integer,db.ForeignKey('usuarios.id'),nullable=False)
    aluno_id = db.Column(db.Integer,db.ForeignKey('usuarios.id'),nullable=False)

    # --------------------------------------------------------
    # MATÉRIA
    # --------------------------------------------------------

    materia = db.relationship('Materia',back_populates='atividades')


    # --------------------------------------------------------
    # PROFESSOR
    # --------------------------------------------------------

    professor = db.relationship('Usuario',back_populates='atividades_professor',foreign_keys=[professor_id])


    # --------------------------------------------------------
    # ALUNO
    # --------------------------------------------------------

    aluno = db.relationship('Usuario',back_populates='atividades_aluno',foreign_keys=[aluno_id])


    def to_dict(self):
        return {
            "id": self.id,
            "materia_id": self.materia_id,
            "tipoativ": self.tipoativ,
            "nota": self.nota,
            "data": (self.data.isoformat() if self.data else None),
            "professor_id": self.professor_id,
            "aluno_id": self.aluno_id}
