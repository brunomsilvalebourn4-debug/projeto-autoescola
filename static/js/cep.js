(function (global) {
    "use strict";

    class CepError extends Error {
        constructor(code, message) {
            super(message);
            this.name = "CepError";
            this.code = code;
        }
    }

    function normalizarCep(cep) {
        return String(cep || "").replace(/\D/g, "");
    }

    async function consultarCep(cep, options = {}) {
        const cepNormalizado = normalizarCep(cep);
        if (cepNormalizado.length !== 8) {
            throw new CepError("CEP_INVALIDO", "Informe um CEP com 8 números.");
        }

        const fetchFn = options.fetchFn || global.fetch;
        const timeoutMs = options.timeoutMs || 5000;
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), timeoutMs);

        try {
            const response = await fetchFn(`https://viacep.com.br/ws/${cepNormalizado}/json/`, {
                signal: controller.signal,
                headers: { Accept: "application/json" },
            });
            if (!response.ok) {
                throw new CepError("FALHA_HTTP", "Não foi possível consultar o CEP agora.");
            }
            const data = await response.json();
            if (data.erro) {
                throw new CepError("CEP_NAO_ENCONTRADO", "CEP não encontrado. Preencha o endereço manualmente.");
            }
            return {
                cep: cepNormalizado,
                endereco: data.logradouro || "",
                bairro: data.bairro || "",
                cidade: data.localidade || "",
                uf: data.uf || "",
            };
        } catch (error) {
            if (error instanceof CepError) throw error;
            if (error && error.name === "AbortError") {
                throw new CepError("TIMEOUT", "A consulta demorou demais. Preencha o endereço manualmente.");
            }
            throw new CepError("API_INDISPONIVEL", "Serviço de CEP indisponível. Preencha o endereço manualmente.");
        } finally {
            clearTimeout(timeout);
        }
    }

    const api = { CepError, normalizarCep, consultarCep };
    global.CepService = api;
    if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof globalThis !== "undefined" ? globalThis : window);

if (typeof document !== "undefined") document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("[data-cep-form]");
    if (!form || !globalThis.CepService) return;

    const cepInput = form.querySelector('[name="cep"]');
    const button = form.querySelector("[data-buscar-cep]");
    const status = form.querySelector("[data-cep-status]");
    const campos = {
        endereco: form.querySelector('[name="endereco"]'),
        bairro: form.querySelector('[name="bairro"]'),
        cidade: form.querySelector('[name="cidade"]'),
        uf: form.querySelector('[name="uf"]'),
    };

    function informar(message, type = "info") {
        status.textContent = message;
        status.className = `mt-2 text-sm ${type === "error" ? "text-red-700" : "text-slate-600"}`;
    }

    async function buscar() {
        button.disabled = true;
        button.setAttribute("aria-busy", "true");
        informar("Consultando CEP...");
        try {
            const endereco = await globalThis.CepService.consultarCep(cepInput.value);
            Object.entries(campos).forEach(([nome, campo]) => {
                if (campo && endereco[nome]) campo.value = endereco[nome];
            });
            informar("Endereço encontrado. Confira os dados antes de salvar.");
        } catch (error) {
            informar(error.message || "Não foi possível consultar o CEP. Preencha manualmente.", "error");
        } finally {
            button.disabled = false;
            button.removeAttribute("aria-busy");
        }
    }

    button.addEventListener("click", buscar);
    cepInput.addEventListener("blur", (event) => {
        if (event.relatedTarget !== button && globalThis.CepService.normalizarCep(cepInput.value).length === 8) buscar();
    });
});
