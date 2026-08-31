import argparse
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import Config
from models.processo_habilitacao import ETAPAS_PADRAO


def dias_uteis(inicio, quantidade):
    atual = inicio
    encontrados = []
    while len(encontrados) < quantidade:
        if atual.weekday() < 5:
            encontrados.append(atual)
        atual += timedelta(days=1)
    return encontrados


def gerar_banco(caminho):
    destino = Path(caminho).resolve()
    banco_real = Path(Config.DB_NAME).resolve()
    if destino == banco_real:
        raise ValueError("O gerador se recusa a utilizar o banco real da aplicação.")
    if destino.exists():
        raise FileExistsError("O banco de desenvolvimento já existe. Informe um caminho novo.")
    destino.parent.mkdir(parents=True, exist_ok=True)
    schema = (PROJECT_ROOT / "database" / "schema.sql").read_text(encoding="utf-8")
    connection = sqlite3.connect(destino)
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        connection.executescript(schema)
        alunos = [(f"Aluno Teste {n:03d}", f"{n:011d}", f"119{n:08d}", "B", "ATIVO") for n in range(1, 101)]
        connection.executemany("INSERT INTO alunos(nome_completo,cpf,telefone,categoria_cnh,status) VALUES(?,?,?,?,?)", alunos)
        instrutores = [(f"Instrutor {n:02d}", f"8{n:010d}", f"118{n:08d}", "08:00", "18:00") for n in range(1, 11)]
        connection.executemany("INSERT INTO instrutores(nome,cpf,telefone,horario_inicio,horario_fim) VALUES(?,?,?,?,?)", instrutores)
        connection.executemany("INSERT INTO instrutor_categorias VALUES(?, 'B')", ((n,) for n in range(1, 11)))
        connection.executemany("INSERT INTO instrutor_disponibilidade VALUES(?, ?)", ((instrutor, dia) for instrutor in range(1, 11) for dia in range(5)))
        veiculos = [(f"TST{n % 10}A{n:02d}", "Marca Teste", f"Modelo {n:02d}", 2025, "B", "AUTOMOVEL") for n in range(1, 11)]
        connection.executemany("INSERT INTO veiculos(placa,marca,modelo,ano,categoria,tipo) VALUES(?,?,?,?,?,?)", veiculos)

        hoje = date.today()
        for aluno_id in range(1, 101):
            status = "CONCLUIDO" if aluno_id <= 20 else "EM_ANDAMENTO"
            conclusao = hoje.isoformat() if status == "CONCLUIDO" else None
            processo_id = connection.execute("INSERT INTO processos_habilitacao(aluno_id,categoria,status,data_inicio,data_conclusao,resultado) VALUES(?,?,?,?,?,?)", (aluno_id,"B",status,(hoje-timedelta(days=60)).isoformat(),conclusao,"APROVADO" if aluno_id <= 15 else "REPROVADO" if aluno_id <= 20 else None)).lastrowid
            concluidas = 8 if status == "CONCLUIDO" else 1 + aluno_id % 6
            connection.executemany("INSERT INTO etapas_processo(processo_id,codigo,nome,ordem,status,data_inicio,data_conclusao) VALUES(?,?,?,?,?,?,?)", ((processo_id,codigo,nome,ordem,"CONCLUIDO" if ordem <= concluidas else "EM_ANDAMENTO" if ordem == concluidas + 1 else "NAO_INICIADO",hoje.isoformat() if ordem <= concluidas + 1 else None,hoje.isoformat() if ordem <= concluidas else None) for codigo,nome,ordem in ETAPAS_PADRAO))

        aulas = []
        for indice_dia, dia in enumerate(dias_uteis(hoje, 20)):
            for slot, (inicio, fim) in enumerate((("08:00", "08:50"), ("09:00", "09:50"))):
                for instrutor_id in range(1, 11):
                    aluno_id = (indice_dia * 20 + slot * 10 + instrutor_id - 1) % 100 + 1
                    situacao = "REALIZADA" if dia < hoje else "AGENDADA"
                    aulas.append((aluno_id,instrutor_id,instrutor_id,dia.isoformat(),inicio,fim,"B",situacao))
        connection.executemany("INSERT INTO aulas(aluno_id,instrutor_id,veiculo_id,data,horario_inicio,horario_fim,categoria,situacao) VALUES(?,?,?,?,?,?,?,?)", aulas)
        connection.commit()
        return {"alunos": 100, "instrutores": 10, "veiculos": 10, "processos": 100, "etapas": 800, "aulas": len(aulas)}
    except Exception:
        connection.rollback()
        connection.close()
        destino.unlink(missing_ok=True)
        raise
    finally:
        if connection:
            connection.close()


def main():
    parser = argparse.ArgumentParser(description="Gera dados isolados para desenvolvimento e testes de carga.")
    parser.add_argument("--database", required=True, help="Caminho de um NOVO banco SQLite de desenvolvimento.")
    args = parser.parse_args()
    totais = gerar_banco(args.database)
    print("Banco de desenvolvimento criado:", totais)


if __name__ == "__main__":
    main()
