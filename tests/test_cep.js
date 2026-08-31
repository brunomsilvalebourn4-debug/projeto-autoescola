const test = require("node:test");
const assert = require("node:assert/strict");
const { consultarCep, normalizarCep } = require("../static/js/cep.js");

test("normaliza e consulta CEP válido", async () => {
    const result = await consultarCep("01001-000", {
        fetchFn: async (url) => {
            assert.equal(url, "https://viacep.com.br/ws/01001000/json/");
            return { ok: true, json: async () => ({ logradouro: "Praça da Sé", bairro: "Sé", localidade: "São Paulo", uf: "SP" }) };
        },
    });
    assert.equal(normalizarCep("01001-000"), "01001000");
    assert.equal(result.cidade, "São Paulo");
});

test("rejeita CEP com tamanho inválido sem chamar a API", async () => {
    let called = false;
    await assert.rejects(() => consultarCep("123", { fetchFn: async () => { called = true; } }), { code: "CEP_INVALIDO" });
    assert.equal(called, false);
});

test("trata CEP inexistente", async () => {
    await assert.rejects(() => consultarCep("01001000", { fetchFn: async () => ({ ok: true, json: async () => ({ erro: true }) }) }), { code: "CEP_NAO_ENCONTRADO" });
});

test("trata falha HTTP e indisponibilidade", async () => {
    await assert.rejects(() => consultarCep("01001000", { fetchFn: async () => ({ ok: false }) }), { code: "FALHA_HTTP" });
    await assert.rejects(() => consultarCep("01001000", { fetchFn: async () => { throw new TypeError("offline"); } }), { code: "API_INDISPONIVEL" });
});

test("trata timeout", async () => {
    await assert.rejects(() => consultarCep("01001000", {
        timeoutMs: 1,
        fetchFn: (_url, options) => new Promise((_resolve, reject) => options.signal.addEventListener("abort", () => reject(Object.assign(new Error(), { name: "AbortError" })))),
    }), { code: "TIMEOUT" });
});
