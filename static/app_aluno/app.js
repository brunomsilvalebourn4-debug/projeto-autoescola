/* Minhas Aulas — app do aluno (somente consulta). */
(function () {
  "use strict";

  const API = "/api/aluno";
  const CHAVE_TOKEN = "minhasAulas.token";
  const VERSAO = "1.0.0";
  const INTERVALO_ATUALIZACAO = 60000;
  const MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"];
  const MESES_CURTOS = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"];
  const DIAS = ["Domingo", "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado"];
  const DIAS_CURTOS = ["D", "S", "T", "Q", "Q", "S", "S"];
  const ROTULOS = {
    agendada: "Agendada",
    em_andamento: "Em andamento",
    realizada: "Realizada",
    falta: "Falta",
    cancelada: "Cancelada",
    reagendada: "Reagendada",
    aguardando_registro: "Aguardando registro"
  };
  const STATUS_ALUNO = { ATIVO: "Ativo", INATIVO: "Inativo", PROCESSO_CONCLUIDO: "Processo concluído", CANCELADO: "Cancelado" };
  const ROTAS = ["inicio", "aulas", "calendario", "perfil"];

  const ICONES = {
    inicio: '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/><path d="M9.5 21v-6h5v6"/>',
    aulas: '<rect x="3" y="4" width="18" height="17" rx="3"/><path d="M8 9h8M8 13h8M8 17h5"/>',
    calendario: '<rect x="3" y="5" width="18" height="16" rx="3"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    perfil: '<circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/>',
    atualizar: '<path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 4v7h-7"/>',
    dir: '<path d="m9 6 6 6-6 6"/>',
    esq: '<path d="m15 6-6 6 6 6"/>',
    check: '<path d="m5 12 5 5 9-10"/>',
    fechar: '<path d="M6 6l12 12M18 6 6 18"/>',
    olho: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    olhoFechado: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><path d="M3 3l18 18"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
    relogio: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    sair: '<path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3"/><path d="M10 17l-5-5 5-5M5 12h11"/>',
    alerta: '<path d="M12 3 2 20h20L12 3z"/><path d="M12 10v4M12 17h.01"/>'
  };

  const estado = {
    token: lerToken(),
    resumo: null,
    aulas: null,
    perfil: null,
    erroCarga: null,
    carregando: false,
    ultimaCarga: 0,
    rota: "inicio",
    abaAulas: "proximas",
    calMes: null,
    calDia: null,
    modoAuth: "login",
    avisoAuth: "",
    sheetAberta: false,
    sheetInterna: false,
    focoAnterior: null
  };

  const raiz = document.getElementById("app");
  const raizSheet = document.getElementById("sheet-root");
  const elToast = document.getElementById("toast");

  // ---------- utilitários ----------

  function esc(valor) {
    return String(valor === null || valor === undefined ? "" : valor).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function icone(nome) {
    return '<svg class="i" viewBox="0 0 24 24" aria-hidden="true" focusable="false">' + ICONES[nome] + "</svg>";
  }

  function lerToken() {
    try { return window.localStorage.getItem(CHAVE_TOKEN); } catch (e) { return null; }
  }

  function gravarToken(token) {
    try {
      if (token) window.localStorage.setItem(CHAVE_TOKEN, token);
      else window.localStorage.removeItem(CHAVE_TOKEN);
    } catch (e) { /* armazenamento indisponível: a sessão dura enquanto a página estiver aberta */ }
  }

  function parseData(iso) {
    const partes = iso.split("-").map(Number);
    return new Date(partes[0], partes[1] - 1, partes[2]);
  }

  function isoLocal(data) {
    const m = String(data.getMonth() + 1).padStart(2, "0");
    const d = String(data.getDate()).padStart(2, "0");
    return data.getFullYear() + "-" + m + "-" + d;
  }

  function diasAte(iso) {
    return Math.round((parseData(iso) - parseData(isoLocal(new Date()))) / 86400000);
  }

  function relativo(aula) {
    if (aula.status === "em_andamento") return "Agora";
    const dias = diasAte(aula.data);
    if (dias <= 0) return "Hoje";
    if (dias === 1) return "Amanhã";
    return "Em " + dias + " dias";
  }

  function horario(aula) { return aula.horario_inicio + " – " + aula.horario_fim; }
  function veiculo(aula) { return [aula.veiculo.marca, aula.veiculo.modelo].filter(Boolean).join(" "); }
  function plural(n, singular, pluralTexto) { return n + " " + (n === 1 ? singular : pluralTexto); }

  function todasAulas() {
    if (!estado.aulas) return [];
    return estado.aulas.proximas.concat(estado.aulas.realizadas, estado.aulas.outras);
  }

  function toast(texto) {
    elToast.textContent = texto;
    elToast.hidden = false;
    clearTimeout(toast.timer);
    toast.timer = setTimeout(function () { elToast.hidden = true; }, 2800);
  }

  // ---------- API ----------

  async function api(caminho, opcoes) {
    opcoes = opcoes || {};
    const cabecalhos = { Accept: "application/json" };
    if (opcoes.corpo) cabecalhos["Content-Type"] = "application/json";
    if (estado.token && !opcoes.publico) cabecalhos.Authorization = "Bearer " + estado.token;
    let resposta;
    try {
      resposta = await fetch(API + caminho, {
        method: opcoes.metodo || "GET",
        headers: cabecalhos,
        body: opcoes.corpo ? JSON.stringify(opcoes.corpo) : undefined,
        cache: "no-store",
        credentials: "omit"
      });
    } catch (e) {
      const falha = new Error("Sem conexão com a internet.");
      falha.offline = true;
      throw falha;
    }
    if (resposta.status === 204) return null;
    let dados = null;
    try { dados = await resposta.json(); } catch (e) { dados = null; }
    if (resposta.status === 401 && !opcoes.publico) {
      encerrarLocal("Sua sessão expirou. Entre novamente.");
      const falha = new Error("Sessão expirada.");
      falha.sessao = true;
      throw falha;
    }
    if (!resposta.ok) {
      const falha = new Error((dados && dados.erro) || "Não foi possível concluir. Tente novamente.");
      falha.status = resposta.status;
      throw falha;
    }
    return dados;
  }

  async function carregar(manual) {
    if (!estado.token || estado.carregando) return;
    estado.carregando = true;
    marcarAtualizando(true);
    try {
      const respostas = await Promise.all([api("/resumo"), api("/aulas")]);
      estado.resumo = respostas[0];
      estado.aulas = respostas[1];
      estado.erroCarga = null;
      estado.ultimaCarga = Date.now();
      if (!estado.calMes) iniciarCalendario();
      render(false);
      if (manual) toast("Aulas atualizadas");
    } catch (e) {
      if (!e.sessao) {
        if (!estado.resumo) {
          estado.erroCarga = e.message;
          render(false);
        } else {
          toast(e.offline ? "Sem conexão. Mostrando os últimos dados carregados." : e.message);
        }
      }
    } finally {
      estado.carregando = false;
      marcarAtualizando(false);
    }
  }

  async function carregarPerfil() {
    if (estado.carregandoPerfil) return;
    estado.carregandoPerfil = true;
    try {
      estado.perfil = await api("/perfil");
      if (estado.rota === "perfil") render(false);
    } catch (e) {
      if (!e.sessao) toast(e.message);
    } finally {
      estado.carregandoPerfil = false;
    }
  }

  function marcarAtualizando(ativo) {
    document.querySelectorAll('[data-acao="atualizar"]').forEach(function (botao) {
      botao.classList.toggle("girando", ativo);
      botao.disabled = ativo;
    });
  }

  function encerrarLocal(aviso) {
    gravarToken(null);
    estado.token = null;
    estado.resumo = estado.aulas = estado.perfil = null;
    estado.calMes = estado.calDia = null;
    estado.erroCarga = null;
    estado.modoAuth = "login";
    estado.avisoAuth = aviso || "";
    fecharSheet(false);
    if (location.hash) history.replaceState(null, "", location.pathname);
    render(true);
  }

  // ---------- telas: autenticação ----------

  function campoSenha(id, nome, autocomplete, rotulo, dica) {
    return '<div class="field"><label for="' + id + '">' + rotulo + "</label>" +
      '<div class="control"><input id="' + id + '" name="' + nome + '" type="password" autocomplete="' + autocomplete + '" required minlength="' + (nome === "senha" && autocomplete === "current-password" ? 1 : 8) + '" maxlength="128">' +
      '<button type="button" class="icon-btn toggle" data-acao="mostrar-senha" data-alvo="' + id + '" aria-label="Mostrar senha" aria-pressed="false">' + icone("olho") + "</button></div>" +
      (dica ? '<p class="hint">' + dica + "</p>" : "") + "</div>";
  }

  function campoCpf() {
    return '<div class="field"><label for="cpf">CPF</label><input id="cpf" name="cpf" inputmode="numeric" autocomplete="username" placeholder="000.000.000-00" maxlength="14" required data-mascara="cpf"></div>';
  }

  function telaAuth() {
    const aviso = estado.avisoAuth;
    const alerta = '<div class="alert" role="alert"' + (aviso ? "" : " hidden") + ">" + esc(aviso) + "</div>";
    const marca = '<div class="brand"><img src="/static/app_aluno/icon.svg" alt=""><h1>Minhas Aulas</h1><p>Acompanhe suas aulas da autoescola</p></div>';
    if (estado.modoAuth === "ativar") {
      return '<main class="auth fade-in">' + marca +
        '<h2 class="auth-title">Primeiro acesso</h2><p class="auth-sub">Use o código entregue pela autoescola para criar sua senha. O mesmo caminho serve para redefinir a senha.</p>' +
        '<form class="form" data-form="ativar" novalidate>' + alerta + campoCpf() +
        '<div class="field"><label for="codigo">Código de acesso</label><input id="codigo" name="codigo" class="code" autocomplete="one-time-code" autocapitalize="characters" spellcheck="false" placeholder="ABCD-1234" maxlength="9" required></div>' +
        campoSenha("senha", "senha", "new-password", "Crie uma senha", "Mínimo de 8 caracteres.") +
        campoSenha("confirmacao", "confirmacao", "new-password", "Confirme a senha", "") +
        '<button class="btn primary" type="submit">Criar senha e entrar</button></form>' +
        '<button class="btn link" type="button" data-acao="modo-auth" data-valor="login">Já tenho senha</button></main>';
    }
    return '<main class="auth fade-in">' + marca +
      '<form class="form" data-form="login" novalidate>' + alerta + campoCpf() +
      campoSenha("senha", "senha", "current-password", "Senha", "") +
      '<button class="btn primary" type="submit">Entrar</button></form>' +
      '<button class="btn link" type="button" data-acao="modo-auth" data-valor="ativar">Primeiro acesso ou esqueci minha senha</button>' +
      '<p class="auth-foot">Somente consulta. Agendamentos e alterações são feitos pela autoescola.</p></main>';
  }

  async function enviarAuth(form) {
    const modo = form.getAttribute("data-form");
    const dados = Object.fromEntries(new FormData(form).entries());
    const alerta = form.querySelector(".alert");
    const botao = form.querySelector('button[type="submit"]');
    const mostrarErro = function (texto) {
      alerta.textContent = texto;
      alerta.hidden = false;
    };
    const cpf = (dados.cpf || "").replace(/\D/g, "");
    if (cpf.length !== 11) return mostrarErro("Informe um CPF com 11 dígitos.");
    if (modo === "login" && !dados.senha) return mostrarErro("Informe sua senha.");
    if (modo === "ativar") {
      if ((dados.codigo || "").replace(/[^A-Za-z0-9]/g, "").length !== 8) return mostrarErro("Informe o código de 8 caracteres entregue pela autoescola.");
      if ((dados.senha || "").length < 8) return mostrarErro("A senha deve ter pelo menos 8 caracteres.");
      if (dados.senha !== dados.confirmacao) return mostrarErro("As senhas não conferem.");
    }
    const textoOriginal = botao.textContent;
    botao.disabled = true;
    botao.textContent = "Aguarde…";
    alerta.hidden = true;
    try {
      const corpo = modo === "login"
        ? { cpf: cpf, senha: dados.senha }
        : { cpf: cpf, codigo: dados.codigo, senha: dados.senha, confirmacao: dados.confirmacao };
      const resposta = await api(modo === "login" ? "/login" : "/ativar", { metodo: "POST", corpo: corpo, publico: true });
      estado.token = resposta.token;
      estado.avisoAuth = "";
      gravarToken(resposta.token);
      history.replaceState(null, "", "#/inicio");
      estado.rota = "inicio";
      render(true);
      carregar(false);
    } catch (e) {
      mostrarErro(e.message);
      botao.disabled = false;
      botao.textContent = textoOriginal;
    }
  }

  // ---------- telas: aplicativo ----------

  function botaoAtualizar() {
    return '<button class="icon-btn" type="button" data-acao="atualizar" aria-label="Atualizar aulas">' + icone("atualizar") + "</button>";
  }

  function textoAtualizado() {
    if (!estado.ultimaCarga) return "";
    const d = new Date(estado.ultimaCarga);
    return "Atualizado às " + String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0") + " · dados da autoescola";
  }

  function cartaoProxima(aula) {
    const d = parseData(aula.data);
    const placa = aula.veiculo.placa ? '<span class="plate">' + esc(aula.veiculo.placa) + "</span>" : "";
    const detalhes = ["Categoria " + esc(aula.categoria)];
    if (aula.duracao_minutos) detalhes.push(aula.duracao_minutos + " min");
    return '<a class="hero" href="#/aula/' + aula.id + '">' +
      '<div class="hero-top"><span class="pill">' + icone("relogio") + "PRÓXIMA AULA</span>" +
      '<span class="hero-rel' + (aula.status === "em_andamento" ? " agora" : "") + '">' + relativo(aula) + "</span></div>" +
      '<p class="hero-date">' + d.getDate() + " " + MESES_CURTOS[d.getMonth()] + " • " + esc((aula.dia_semana || DIAS[d.getDay()]).toUpperCase()) + "</p>" +
      '<p class="hero-time">' + esc(aula.horario_inicio) + " <span>–</span> " + esc(aula.horario_fim) + "</p>" +
      '<div class="hero-grid"><div><span class="lbl">Instrutor</span><strong>' + esc(aula.instrutor.nome) + "</strong></div>" +
      '<div><span class="lbl">Veículo</span><strong>' + esc(veiculo(aula)) + "</strong>" + placa + "</div></div>" +
      '<div class="hero-foot"><span>' + detalhes.join(" · ") + "</span><span>Detalhes" + icone("dir") + "</span></div></a>";
  }

  function semProxima() {
    return '<section class="card empty-hero"><div class="empty-icon">' + icone("calendario") + "</div>" +
      '<h2>Nenhuma aula agendada</h2>' +
      '<p class="muted">Quando a autoescola agendar sua próxima aula, ela aparecerá aqui.</p></section>';
  }

  function cartaoProgresso(c) {
    if (!c.na_grade) {
      return '<section class="card"><p class="muted">Nenhuma aula registrada até o momento.</p>' + notas(c) + "</section>";
    }
    return '<section class="card" aria-labelledby="progresso-titulo">' +
      '<div class="progress-head"><h2 id="progresso-titulo">Progresso</h2><span class="progress-pct">' + c.percentual + "%</span></div>" +
      '<p class="progress-big">' + c.realizadas + "<small> / " + c.na_grade + " realizadas</small></p>" +
      '<div class="bar" role="progressbar" aria-label="Aulas realizadas" aria-valuemin="0" aria-valuemax="100" aria-valuenow="' + c.percentual + '"><i data-largura="' + c.percentual + '"></i></div>' +
      '<div class="stats">' +
      '<div class="stat"><b>' + c.na_grade + "</b><span>Na grade</span></div>" +
      '<div class="stat ok"><b>' + c.realizadas + "</b><span>Realizadas</span></div>" +
      '<div class="stat pri"><b>' + c.restantes + "</b><span>Restantes</span></div></div>" +
      notas(c) + "</section>";
  }

  function notas(c) {
    const itens = [];
    if (c.aguardando_registro) itens.push([icone("relogio"), plural(c.aguardando_registro, "aula aguardando registro da autoescola", "aulas aguardando registro da autoescola")]);
    if (c.faltas) itens.push([icone("alerta"), plural(c.faltas, "falta registrada", "faltas registradas")]);
    if (c.canceladas || c.reagendadas) itens.push([icone("info"), plural(c.canceladas + c.reagendadas, "aula cancelada ou reagendada", "aulas canceladas ou reagendadas")]);
    if (!itens.length) return "";
    return '<div class="notes">' + itens.map(function (n) { return '<p class="note">' + n[0] + esc(n[1]) + "</p>"; }).join("") + "</div>";
  }

  function telaInicio() {
    const r = estado.resumo;
    const agora = new Date();
    const hoje = DIAS[agora.getDay()] + ", " + agora.getDate() + " de " + MESES[agora.getMonth()];
    return '<header class="topbar"><div><p class="eyebrow">' + esc(hoje) + "</p><h1>Olá, " + esc(r.aluno.primeiro_nome) + " 👋</h1></div>" + botaoAtualizar() + "</header>" +
      (r.proxima_aula ? cartaoProxima(r.proxima_aula) : semProxima()) +
      '<h2 class="section-title">Minhas aulas</h2>' + cartaoProgresso(r.contagem) +
      '<p class="updated">' + textoAtualizado() + "</p>";
  }

  function itemAula(aula, tipo) {
    const d = parseData(aula.data);
    const classeData = tipo === "realizadas" ? " realizada" : tipo === "outras" ? " outra" : "";
    const check = tipo === "realizadas" ? '<span class="check">' + icone("check") + "</span>" : "";
    const lateral = aula.status === "agendada" || aula.status === "realizada"
      ? icone("dir")
      : '<span class="chip ' + aula.status + '">' + ROTULOS[aula.status] + "</span>";
    const placa = aula.veiculo.placa ? " · " + esc(aula.veiculo.placa) : "";
    const rotuloAcessivel = ROTULOS[aula.status] + ", " + (aula.dia_semana || "") + " " + d.getDate() + " de " + MESES[d.getMonth()];
    return '<li><a class="lesson" href="#/aula/' + aula.id + '" aria-label="' + esc(rotuloAcessivel + ", " + horario(aula) + ", " + aula.instrutor.nome + ", " + veiculo(aula)) + '">' +
      '<div class="datebox' + classeData + '"><b>' + d.getDate() + "</b><span>" + MESES_CURTOS[d.getMonth()] + "</span>" + check + "</div>" +
      '<div class="lesson-info"><p class="lesson-time">' + esc(horario(aula)) + "</p>" +
      '<p class="lesson-line">' + esc(aula.instrutor.nome) + "</p>" +
      '<p class="lesson-line sub">' + esc(veiculo(aula)) + placa + "</p></div>" + lateral + "</a></li>";
  }

  function listaAgrupada(aulas, tipo) {
    let html = "";
    let mesAtual = "";
    aulas.forEach(function (aula) {
      const d = parseData(aula.data);
      const chave = MESES[d.getMonth()] + " de " + d.getFullYear();
      if (chave !== mesAtual) {
        if (mesAtual) html += "</ul>";
        html += '<h3 class="month">' + chave + '</h3><ul class="lessons">';
        mesAtual = chave;
      }
      html += itemAula(aula, tipo);
    });
    return html + (mesAtual ? "</ul>" : "");
  }

  function vazioAulas(tipo) {
    const textos = {
      proximas: ["Nenhuma aula agendada", "Quando a autoescola agendar novas aulas, elas aparecerão aqui."],
      realizadas: ["Nenhuma aula realizada ainda", "Suas aulas concluídas ficarão registradas aqui."],
      outras: ["Nada por aqui", "Faltas, cancelamentos e reagendamentos aparecem aqui."]
    }[tipo];
    return '<div class="empty"><div class="empty-icon">' + icone("aulas") + "</div><h2>" + textos[0] + "</h2><p>" + textos[1] + "</p></div>";
  }

  function telaAulas() {
    const a = estado.aulas;
    const abas = [["proximas", "Próximas"], ["realizadas", "Realizadas"]];
    if (a.outras.length) abas.push(["outras", "Outras"]);
    if (!abas.some(function (aba) { return aba[0] === estado.abaAulas; })) estado.abaAulas = "proximas";
    const botoes = abas.map(function (aba) {
      const selecionada = aba[0] === estado.abaAulas;
      return '<button type="button" role="tab" id="aba-' + aba[0] + '" aria-controls="painel-aulas" aria-selected="' + selecionada + '" tabindex="' + (selecionada ? 0 : -1) + '" data-acao="aba" data-valor="' + aba[0] + '">' +
        aba[1] + '<span class="count">' + a[aba[0]].length + "</span></button>";
    }).join("");
    const lista = a[estado.abaAulas];
    return '<header class="topbar"><div><h1>Minhas aulas</h1></div>' + botaoAtualizar() + "</header>" +
      '<div class="segmented" role="tablist" aria-label="Filtrar aulas">' + botoes + "</div>" +
      '<div id="painel-aulas" role="tabpanel" aria-labelledby="aba-' + estado.abaAulas + '">' +
      (lista.length ? listaAgrupada(lista, estado.abaAulas) : vazioAulas(estado.abaAulas)) + "</div>";
  }

  function iniciarCalendario() {
    const proxima = estado.resumo && estado.resumo.proxima_aula;
    const referencia = proxima ? parseData(proxima.data) : new Date();
    estado.calMes = new Date(referencia.getFullYear(), referencia.getMonth(), 1);
    estado.calDia = isoLocal(referencia);
  }

  function aulasPorDia() {
    const mapa = {};
    todasAulas().forEach(function (aula) { (mapa[aula.data] = mapa[aula.data] || []).push(aula); });
    Object.keys(mapa).forEach(function (dia) {
      mapa[dia].sort(function (x, y) { return x.horario_inicio.localeCompare(y.horario_inicio); });
    });
    return mapa;
  }

  function classePonto(status) {
    if (status === "realizada") return "dot realizada";
    if (status === "agendada" || status === "em_andamento") return "dot";
    return "dot outra";
  }

  function telaCalendario() {
    if (!estado.calMes) iniciarCalendario();
    const mapa = aulasPorDia();
    const mes = estado.calMes;
    const inicio = new Date(mes.getFullYear(), mes.getMonth(), 1 - mes.getDay());
    const diasNoMes = new Date(mes.getFullYear(), mes.getMonth() + 1, 0).getDate();
    const celulas = Math.ceil((mes.getDay() + diasNoMes) / 7) * 7;
    const hoje = isoLocal(new Date());
    let grade = DIAS_CURTOS.map(function (d, i) { return '<div class="cal-wd" aria-hidden="true" title="' + DIAS[i] + '">' + d + "</div>"; }).join("");
    for (let n = 0; n < celulas; n++) {
      const dia = new Date(inicio.getFullYear(), inicio.getMonth(), inicio.getDate() + n);
      const iso = isoLocal(dia);
      const aulas = mapa[iso] || [];
      const classes = ["cal-day"];
      if (dia.getMonth() !== mes.getMonth()) classes.push("fora");
      if (iso === hoje) classes.push("hoje");
      if (aulas.length) classes.push("tem");
      const pontos = aulas.slice(0, 3).map(function (a) { return '<span class="' + classePonto(a.status) + '"></span>'; }).join("");
      const rotulo = dia.getDate() + " de " + MESES[dia.getMonth()] + (aulas.length ? ", " + plural(aulas.length, "aula", "aulas") : ", sem aulas");
      grade += '<button type="button" class="' + classes.join(" ") + '" data-acao="dia" data-valor="' + iso + '" aria-pressed="' + (iso === estado.calDia) + '" aria-label="' + rotulo + '">' +
        dia.getDate() + '<span class="dots" aria-hidden="true">' + pontos + "</span></button>";
    }
    const selecionado = parseData(estado.calDia);
    const aulasDia = mapa[estado.calDia] || [];
    const cartoes = aulasDia.length ? aulasDia.map(function (a) {
      return '<a class="card day-card" href="#/aula/' + a.id + '"><div class="dc-time"><span>' + esc(horario(a)) + '</span><span class="chip ' + a.status + '">' + ROTULOS[a.status] + "</span></div>" +
        '<dl class="kv"><div><dt>Instrutor</dt><dd>' + esc(a.instrutor.nome) + "</dd></div><div><dt>Veículo</dt><dd>" + esc(veiculo(a)) + "</dd></div></dl></a>";
    }).join("") : '<div class="card muted">Nenhuma aula neste dia.</div>';
    return '<header class="topbar"><div><h1>Calendário</h1></div>' + botaoAtualizar() + "</header>" +
      '<section class="card"><div class="cal-head"><h2 aria-live="polite">' + MESES[mes.getMonth()].charAt(0).toUpperCase() + MESES[mes.getMonth()].slice(1) + " de " + mes.getFullYear() + "</h2>" +
      '<div class="nav"><button type="button" class="icon-btn" data-acao="mes" data-valor="-1" aria-label="Mês anterior">' + icone("esq") + "</button>" +
      '<button type="button" class="icon-btn" data-acao="mes" data-valor="1" aria-label="Próximo mês">' + icone("dir") + "</button></div></div>" +
      '<div class="cal-grid">' + grade + "</div>" +
      '<div class="legend" aria-hidden="true"><span><i class="dot"></i>Agendada</span><span><i class="dot realizada"></i>Realizada</span><span><i class="dot outra"></i>Outras</span></div></section>' +
      '<div class="day-title"><p>' + DIAS[selecionado.getDay()] + "</p><h2>" + selecionado.getDate() + " de " + MESES[selecionado.getMonth()] + "</h2></div>" + cartoes;
  }

  function telaPerfil() {
    const p = estado.perfil;
    if (!p) {
      carregarPerfil();
      return '<header class="topbar"><div><h1>Perfil</h1></div></header><div class="splash-inline"><span class="spinner" aria-hidden="true"></span></div>';
    }
    const iniciais = p.nome.split(/\s+/).filter(Boolean);
    const sigla = (iniciais[0][0] + (iniciais.length > 1 ? iniciais[iniciais.length - 1][0] : "")).toUpperCase();
    return '<header class="topbar"><div><h1>Perfil</h1></div></header><div class="stack">' +
      '<section class="card"><div class="profile-head"><div class="avatar" aria-hidden="true">' + esc(sigla) + "</div>" +
      "<div><h2>" + esc(p.nome) + '</h2><p class="muted">Categoria ' + esc(p.categoria_cnh) + "</p></div></div>" +
      '<dl class="rows"><div><dt>CPF</dt><dd>' + esc(p.cpf) + "</dd></div>" +
      "<div><dt>E-mail</dt><dd>" + esc(p.email || "—") + "</dd></div>" +
      "<div><dt>Situação</dt><dd>" + esc(STATUS_ALUNO[p.status] || p.status) + "</dd></div></dl></section>" +
      '<section class="card info">' + icone("info") + "<p>Este aplicativo é somente para consulta. Para agendar, remarcar ou cancelar aulas, ou corrigir seus dados, fale com a autoescola.</p></section>" +
      '<button type="button" class="btn ghost" data-acao="sair">' + icone("sair") + "Sair</button></div>" +
      '<p class="version">Minhas Aulas · versão ' + VERSAO + "</p>";
  }

  function telaErro() {
    return '<main class="screen"><div class="empty"><div class="empty-icon">' + icone("alerta") + "</div><h2>Não foi possível carregar</h2><p>" + esc(estado.erroCarga) + "</p></div>" +
      '<button type="button" class="btn primary" data-acao="tentar">Tentar novamente</button></main>';
  }

  function barraInferior() {
    const itens = [["inicio", "Início"], ["aulas", "Aulas"], ["calendario", "Calendário"], ["perfil", "Perfil"]];
    return '<nav class="tabbar" aria-label="Navegação principal"><ul>' + itens.map(function (item) {
      const atual = item[0] === estado.rota ? ' aria-current="page"' : "";
      return '<li><a href="#/' + item[0] + '"' + atual + ">" + icone(item[0]) + "<span>" + item[1] + "</span></a></li>";
    }).join("") + "</ul></nav>";
  }

  function render(animar) {
    if (!estado.token) {
      raiz.innerHTML = telaAuth();
      return;
    }
    if (!estado.resumo) {
      raiz.innerHTML = estado.erroCarga ? telaErro() : '<div class="splash" role="status"><span class="spinner" aria-hidden="true"></span><span class="sr-only">Carregando suas aulas</span></div>';
      return;
    }
    const telas = { inicio: telaInicio, aulas: telaAulas, calendario: telaCalendario, perfil: telaPerfil };
    raiz.innerHTML = '<main class="screen' + (animar ? " fade-in" : "") + '" id="conteudo">' + telas[estado.rota]() + "</main>" + barraInferior();
    raiz.querySelectorAll("[data-largura]").forEach(function (barra) {
      requestAnimationFrame(function () { barra.style.width = Math.max(0, Math.min(100, Number(barra.getAttribute("data-largura")))) + "%"; });
    });
    marcarAtualizando(estado.carregando);
  }

  // ---------- detalhes da aula ----------

  function conteudoSheet(aula) {
    if (!aula) return '<div class="splash-inline"><span class="spinner" aria-hidden="true"></span></div>';
    const d = parseData(aula.data);
    const itens = [
      ["Instrutor", esc(aula.instrutor.nome)],
      ["Veículo", esc(veiculo(aula))],
      ["Placa", aula.veiculo.placa ? '<span class="plate">' + esc(aula.veiculo.placa) + "</span>" : "—"],
      ["Categoria", esc(aula.categoria)]
    ];
    return '<div class="sheet-head"><span class="chip ' + aula.status + '">' + ROTULOS[aula.status] + "</span>" +
      '<button type="button" class="icon-btn" data-acao="fechar-sheet" aria-label="Fechar">' + icone("fechar") + "</button></div>" +
      '<p class="eyebrow">' + esc(aula.dia_semana || DIAS[d.getDay()]) + "</p>" +
      '<h2 id="sheet-titulo">' + d.getDate() + " de " + MESES[d.getMonth()] + " de " + d.getFullYear() + "</h2>" +
      '<p class="sheet-time">' + esc(horario(aula)) + (aula.duracao_minutos ? " · " + aula.duracao_minutos + " min" : "") + "</p>" +
      '<dl class="kv">' + itens.map(function (i) { return "<div><dt>" + i[0] + "</dt><dd>" + i[1] + "</dd></div>"; }).join("") + "</dl>" +
      '<div class="info readonly">' + icone("info") + "<p>Somente consulta. Para alterar esta aula, fale com a autoescola.</p></div>";
  }

  function mostrarSheet(aula) {
    if (!estado.sheetAberta) {
      estado.focoAnterior = document.activeElement;
      raizSheet.innerHTML = '<div class="backdrop" data-acao="fechar-sheet"></div>' +
        '<section class="sheet" role="dialog" aria-modal="true" aria-labelledby="sheet-titulo" tabindex="-1"><div class="grabber" aria-hidden="true"></div><div class="sheet-corpo"></div></section>';
      document.body.style.overflow = "hidden";
      estado.sheetAberta = true;
    }
    raizSheet.querySelector(".sheet-corpo").innerHTML = conteudoSheet(aula);
    raizSheet.querySelector(".sheet").focus();
  }

  async function abrirAula(id) {
    const local = todasAulas().find(function (a) { return a.id === id; }) || null;
    mostrarSheet(local);
    try {
      const atual = await api("/aulas/" + id);
      if (estado.sheetAberta) mostrarSheet(atual);
    } catch (e) {
      if (e.sessao) return;
      if (!local) {
        fecharSheet(true);
        toast(e.status === 404 ? "Aula não encontrada." : e.message);
      }
    }
  }

  function fecharSheet(navegar) {
    if (!estado.sheetAberta) return;
    raizSheet.innerHTML = "";
    document.body.style.overflow = "";
    estado.sheetAberta = false;
    if (navegar) {
      if (estado.sheetInterna) history.back();
      else history.replaceState(null, "", "#/" + estado.rota);
    }
    estado.sheetInterna = false;
    if (estado.focoAnterior && document.contains(estado.focoAnterior)) estado.focoAnterior.focus();
  }

  // ---------- navegação ----------

  function lerRota() {
    const partes = location.hash.replace(/^#\/?/, "").split("/");
    return { nome: partes[0] || "inicio", id: partes[1] ? Number(partes[1]) : null };
  }

  function aoMudarRota() {
    if (!estado.token) return;
    const rota = lerRota();
    if (rota.nome === "aula" && rota.id) {
      if (!estado.sheetAberta) abrirAula(rota.id);
      return;
    }
    if (estado.sheetAberta) fecharSheet(false);
    const nova = ROTAS.indexOf(rota.nome) >= 0 ? rota.nome : "inicio";
    const mudou = nova !== estado.rota;
    estado.rota = nova;
    render(mudou);
    if (mudou) window.scrollTo(0, 0);
  }

  // ---------- eventos ----------

  document.addEventListener("click", function (evento) {
    const link = evento.target.closest('a[href^="#/aula/"]');
    if (link) estado.sheetInterna = true;
    const alvo = evento.target.closest("[data-acao]");
    if (!alvo) return;
    const acao = alvo.getAttribute("data-acao");
    const valor = alvo.getAttribute("data-valor");
    if (acao === "atualizar") carregar(true);
    else if (acao === "tentar") { estado.erroCarga = null; render(false); carregar(false); }
    else if (acao === "aba") { estado.abaAulas = valor; render(false); focar('[data-acao="aba"][data-valor="' + valor + '"]'); }
    else if (acao === "mes") {
      estado.calMes = new Date(estado.calMes.getFullYear(), estado.calMes.getMonth() + Number(valor), 1);
      render(false);
      focar('[data-acao="mes"][data-valor="' + valor + '"]');
    } else if (acao === "dia") {
      const d = parseData(valor);
      estado.calDia = valor;
      estado.calMes = new Date(d.getFullYear(), d.getMonth(), 1);
      render(false);
      focar('[data-acao="dia"][data-valor="' + valor + '"]');
    } else if (acao === "fechar-sheet") fecharSheet(true);
    else if (acao === "sair") {
      api("/logout", { metodo: "POST" }).catch(function () { return null; }).then(function () { encerrarLocal(""); });
    } else if (acao === "modo-auth") {
      estado.modoAuth = valor;
      estado.avisoAuth = "";
      render(true);
      focar("#cpf");
    } else if (acao === "mostrar-senha") {
      const campo = document.getElementById(alvo.getAttribute("data-alvo"));
      const visivel = campo.type === "password";
      campo.type = visivel ? "text" : "password";
      alvo.setAttribute("aria-pressed", String(visivel));
      alvo.setAttribute("aria-label", visivel ? "Ocultar senha" : "Mostrar senha");
      alvo.innerHTML = icone(visivel ? "olhoFechado" : "olho");
    }
  });

  document.addEventListener("keydown", function (evento) {
    if (evento.key === "Escape" && estado.sheetAberta) fecharSheet(true);
    const aba = evento.target.closest && evento.target.closest('[role="tab"]');
    if (aba && (evento.key === "ArrowRight" || evento.key === "ArrowLeft")) {
      const abas = Array.from(document.querySelectorAll('[role="tab"]'));
      const proxima = abas[(abas.indexOf(aba) + (evento.key === "ArrowRight" ? 1 : -1) + abas.length) % abas.length];
      proxima.click();
    }
  });

  document.addEventListener("submit", function (evento) {
    const form = evento.target.closest("[data-form]");
    if (!form) return;
    evento.preventDefault();
    enviarAuth(form);
  });

  document.addEventListener("input", function (evento) {
    const campo = evento.target;
    if (campo.getAttribute && campo.getAttribute("data-mascara") === "cpf") {
      const d = campo.value.replace(/\D/g, "").slice(0, 11);
      campo.value = d.replace(/^(\d{3})(\d)/, "$1.$2").replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3").replace(/\.(\d{3})(\d{1,2})$/, ".$1-$2");
    } else if (campo.id === "codigo") {
      const c = campo.value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 8);
      campo.value = c.length > 4 ? c.slice(0, 4) + "-" + c.slice(4) : c;
    }
  });

  function focar(seletor) {
    const el = document.querySelector(seletor);
    if (el) el.focus();
  }

  window.addEventListener("hashchange", aoMudarRota);

  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "visible" && estado.token && Date.now() - estado.ultimaCarga > 30000) carregar(false);
  });

  setInterval(function () {
    if (document.visibilityState === "visible" && estado.token && !estado.sheetAberta && Date.now() - estado.ultimaCarga > INTERVALO_ATUALIZACAO) carregar(false);
  }, 15000);

  window.addEventListener("online", function () { if (estado.token) carregar(false); });

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("/app/sw.js", { scope: "/app/" }).catch(function () { return null; });
    });
  }

  // ---------- início ----------

  const rotaInicial = lerRota();
  estado.rota = ROTAS.indexOf(rotaInicial.nome) >= 0 ? rotaInicial.nome : "inicio";
  render(true);
  if (estado.token) {
    carregar(false).then(function () {
      if (rotaInicial.nome === "aula" && rotaInicial.id && estado.resumo) abrirAula(rotaInicial.id);
    });
  }
})();
