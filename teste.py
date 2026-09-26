
class Pessoa:
    def __init__(self,prontuario,senha,nome,email,cpf):
        self.prontuario=prontuario
        self.senha=senha
        self.nome=nome
        self.email=email
        self.cpf=cpf
    @classmethod
    def apresentar():
        print(f"Prontuário: {self.prontuario} \n Nome: {self.nome} \n E-mail: {self.email} \n CPF: {self.cpf}")

class Servidor(Pessoa):
    def __init__(self,setor,cargo,salario,jornadatrabalho):
        self.setor=setor
        self.cargo=cargo
        self.salario=salario
        self.jornadatrabalho=jornadatrabalho
    @classmethod
    def enviar_mensagem():
        input("Digite uma mensagem:")
        print("Mensagem enviada!")

class Disciplina:
    def __init__(self,id,curso,sigla,nome,turno):
        self.id=id
        self.curso=curso
        self.sigla=sigla
        self.nome=nome
        self.turno=turno

class Professor(Servidor,Disciplina):
    def __init__(self,disciplinas=[]):
        self.disciplinas=disciplinas

class TAE(Pessoa,Servidor):
    def __init__(self, horascapacitacao,cursos=[]):
        self.horascapacitacao=horascapacitacao
        self.cursos=cursos

class Discente(Pessoa):
    def __init__(self,boletim,ira):
        self.boletim=boletim
        self.ira=ira
    @classmethod
    def apresentar_discente():
        super().__init__()
        super().apresentar()
        print(f"Boletim: {self.boletim} \n IRA: {self.ira}")

<option value="Matematica" {% if atividade.materias == 'Matematica' %}selected{% endif %}>Matematica</option>
                    <option value="Lingua Portuguesa" {% if atividade.materia == 'Lingua Portuguesa' %}selected{% endif %}>Lingua Portuguesa</option>
                    <option value="Historia" {% if atividade.materia == 'Historia' %}selected{% endif %}>Historia</option>
                    <option value="Geografia" {% if atividade.materia == 'Geografia' %}selected{% endif %}>Geografia</option>
                    <option value="Fisica" {% if atividade.materia == 'Fisica' %}selected{% endif %}>Fisica</option>
                    <option value="Quimica" {% if atividade.materia == 'Quimica' %}selected{% endif %}>Quimica</option>
                    <option value="Biologia" {% if atividade.materia == 'Biologia' %}selected{% endif %}>Biologia</option>