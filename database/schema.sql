PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS instrutores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cpf TEXT NOT NULL UNIQUE,
    telefone TEXT NOT NULL,
    email TEXT,
    horario_inicio TEXT NOT NULL,
    horario_fim TEXT NOT NULL,
    ativo INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1)),
    observacoes TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (horario_inicio < horario_fim)
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
    senha_hash TEXT NOT NULL,
    perfil TEXT NOT NULL CHECK (perfil IN ('ADMINISTRADOR', 'ATENDENTE', 'INSTRUTOR')),
    instrutor_id INTEGER,
    ativo INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1)),
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (instrutor_id) REFERENCES instrutores(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS alunos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_completo TEXT NOT NULL,
    cpf TEXT NOT NULL UNIQUE,
    rg TEXT,
    data_nascimento TEXT,
    telefone TEXT NOT NULL,
    whatsapp TEXT,
    email TEXT,
    cep TEXT,
    endereco TEXT,
    numero TEXT,
    complemento TEXT,
    bairro TEXT,
    cidade TEXT,
    uf TEXT,
    categoria_cnh TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ATIVO' CHECK (status IN ('ATIVO', 'INATIVO', 'PROCESSO_CONCLUIDO', 'CANCELADO')),
    observacoes TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS instrutor_categorias (
    instrutor_id INTEGER NOT NULL,
    categoria TEXT NOT NULL,
    PRIMARY KEY (instrutor_id, categoria),
    FOREIGN KEY (instrutor_id) REFERENCES instrutores(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS instrutor_disponibilidade (
    instrutor_id INTEGER NOT NULL,
    dia_semana INTEGER NOT NULL CHECK (dia_semana BETWEEN 0 AND 6),
    PRIMARY KEY (instrutor_id, dia_semana),
    FOREIGN KEY (instrutor_id) REFERENCES instrutores(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS veiculos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    placa TEXT NOT NULL COLLATE NOCASE UNIQUE,
    marca TEXT NOT NULL,
    modelo TEXT NOT NULL,
    ano INTEGER,
    categoria TEXT NOT NULL,
    tipo TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'DISPONIVEL' CHECK (status IN ('DISPONIVEL', 'EM_AULA', 'MANUTENCAO', 'INATIVO')),
    observacoes TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (ano IS NULL OR ano BETWEEN 1900 AND 2200)
);

CREATE TABLE IF NOT EXISTS processos_habilitacao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aluno_id INTEGER NOT NULL,
    categoria TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'EM_ANDAMENTO' CHECK (status IN ('EM_ANDAMENTO', 'CONCLUIDO', 'CANCELADO')),
    resultado TEXT CHECK (resultado IS NULL OR resultado IN ('APROVADO', 'REPROVADO')),
    data_inicio TEXT NOT NULL,
    data_conclusao TEXT,
    observacoes TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (aluno_id) REFERENCES alunos(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS etapas_processo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    processo_id INTEGER NOT NULL,
    codigo TEXT NOT NULL,
    nome TEXT NOT NULL,
    ordem INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'NAO_INICIADO' CHECK (status IN ('NAO_INICIADO', 'EM_ANDAMENTO', 'PENDENTE', 'CONCLUIDO')),
    data_inicio TEXT,
    data_conclusao TEXT,
    observacoes TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (processo_id, codigo),
    UNIQUE (processo_id, ordem),
    FOREIGN KEY (processo_id) REFERENCES processos_habilitacao(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS aulas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aluno_id INTEGER NOT NULL,
    instrutor_id INTEGER NOT NULL,
    veiculo_id INTEGER NOT NULL,
    data TEXT NOT NULL,
    horario_inicio TEXT NOT NULL,
    horario_fim TEXT NOT NULL,
    categoria TEXT NOT NULL,
    situacao TEXT NOT NULL DEFAULT 'AGENDADA' CHECK (situacao IN ('AGENDADA', 'REALIZADA', 'CANCELADA', 'REAGENDADA', 'FALTA')),
    observacoes TEXT,
    criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (aluno_id) REFERENCES alunos(id) ON DELETE RESTRICT,
    FOREIGN KEY (instrutor_id) REFERENCES instrutores(id) ON DELETE RESTRICT,
    FOREIGN KEY (veiculo_id) REFERENCES veiculos(id) ON DELETE RESTRICT,
    CHECK (horario_inicio < horario_fim)
);

CREATE TABLE IF NOT EXISTS configuracoes (
    chave TEXT PRIMARY KEY,
    valor TEXT NOT NULL,
    descricao TEXT,
    atualizado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS schema_version (
    versao INTEGER PRIMARY KEY,
    aplicado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO schema_version (versao) VALUES (1);
INSERT OR IGNORE INTO configuracoes (chave, valor, descricao)
VALUES ('duracao_aula_minutos', '50', 'Duração padrão de uma aula em minutos');

CREATE INDEX IF NOT EXISTS idx_alunos_nome ON alunos(nome_completo);
CREATE INDEX IF NOT EXISTS idx_alunos_status ON alunos(status);
CREATE INDEX IF NOT EXISTS idx_instrutores_nome ON instrutores(nome);
CREATE INDEX IF NOT EXISTS idx_instrutores_ativo ON instrutores(ativo);
CREATE INDEX IF NOT EXISTS idx_veiculos_status ON veiculos(status);
CREATE INDEX IF NOT EXISTS idx_processos_aluno ON processos_habilitacao(aluno_id);
CREATE INDEX IF NOT EXISTS idx_processos_status ON processos_habilitacao(status);
CREATE INDEX IF NOT EXISTS idx_etapas_processo ON etapas_processo(processo_id, ordem);
CREATE INDEX IF NOT EXISTS idx_aulas_data ON aulas(data);
CREATE INDEX IF NOT EXISTS idx_aulas_aluno_horario ON aulas(aluno_id, data, horario_inicio, horario_fim);
CREATE INDEX IF NOT EXISTS idx_aulas_instrutor_horario ON aulas(instrutor_id, data, horario_inicio, horario_fim);
CREATE INDEX IF NOT EXISTS idx_aulas_veiculo_horario ON aulas(veiculo_id, data, horario_inicio, horario_fim);
CREATE INDEX IF NOT EXISTS idx_aulas_situacao ON aulas(situacao);
