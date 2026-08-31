import sqlite3
from config import Config

def get_connection():
    conn = sqlite3.connect(Config.DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():

    conn = get_connection()

    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT,
        senha_hash TEXT
    )
    """)

    c.execute("""
CREATE TABLE IF NOT EXISTS clientes (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    nome TEXT,
    tipo_pessoa TEXT,

    cpf TEXT,
    rg TEXT,

    telefone TEXT,
    email TEXT,

    data_nascimento TEXT,
    vencimento_cnh TEXT,

    cep TEXT,
    endereco TEXT,
    numero TEXT,
    bairro TEXT,
    cidade TEXT,
    estado TEXT

)
""")
    
    c.execute("""
CREATE TABLE IF NOT EXISTS veiculos (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    cliente_id INTEGER,

    placa TEXT,
    renavam TEXT,

    marca_modelo TEXT,

    chassi TEXT,
    motor TEXT,

    cor TEXT,

    ano_fabricacao TEXT,
    ano_modelo TEXT,

    combustivel TEXT

)
""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS processos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        veiculo_id INTEGER,
        tipo_servico TEXT,
        valor_venda TEXT,
        nota_fiscal TEXT,
        status TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS checklist_documentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        processo_id INTEGER,
        recibo_venda INTEGER DEFAULT 0,
        cnh_socio INTEGER DEFAULT 0,
        contrato_social INTEGER DEFAULT 0,
        vistoria INTEGER DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS financeiro_lancamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_processo TEXT,
        cliente_nome TEXT,
        cpf TEXT,
        placa TEXT,
        servico TEXT,
        valor REAL,
        custo REAL,
        vencimento TEXT,
        data_pagamento TEXT,
        status TEXT,
        forma_pagamento TEXT,
        observacoes TEXT,
        usuario TEXT,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS fluxo_caixa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT,
        descricao TEXT,
        valor REAL,
        data_movimento TEXT,
        origem TEXT,
        usuario TEXT,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

       # ============================================
    # REQUERIMENTOS
    # ============================================

    c.execute("""
    CREATE TABLE IF NOT EXISTS requerimentos_modelos (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        nome TEXT,

        arquivo_modelo TEXT,

        tipo_arquivo TEXT,

        ativo INTEGER DEFAULT 1,

        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)

    # ============================================
    # ATUALIZAÇÕES AUTOMÁTICAS
    # ============================================

    try:

        c.execute("""
        ALTER TABLE clientes
        ADD COLUMN data_nascimento TEXT
        """)

    except:
        pass

    try:

        c.execute("""
        ALTER TABLE veiculos
        ADD COLUMN motor TEXT
        """)

    except:
        pass

    conn.commit()

    print("BANCO INICIALIZADO COM SUCESSO")

    conn.close()