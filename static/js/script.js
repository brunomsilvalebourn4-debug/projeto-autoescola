document.addEventListener("DOMContentLoaded", () => {
    const aplicarMascara = (seletor, formatar) => {
        document.querySelectorAll(seletor).forEach((input) => {
            input.addEventListener("input", (event) => {
                event.target.value = formatar(event.target.value.replace(/\D/g, ""));
            });
        });
    };

    aplicarMascara('input[name="cpf"]', (valor) => valor.slice(0, 11)
        .replace(/(\d{3})(\d)/, "$1.$2")
        .replace(/(\d{3})(\d)/, "$1.$2")
        .replace(/(\d{3})(\d{1,2})$/, "$1-$2"));

    aplicarMascara('input[name="rg"]', (valor) => valor.slice(0, 9)
        .replace(/(\d{2})(\d)/, "$1.$2")
        .replace(/(\d{3})(\d)/, "$1.$2")
        .replace(/(\d{3})(\d)$/, "$1-$2"));

    aplicarMascara('input[name="telefone"], input[name="whatsapp"]', (valor) => valor.slice(0, 11)
        .replace(/^(\d{2})(\d)/, "($1) $2")
        .replace(/(\d)(\d{4})$/, "$1-$2"));

    aplicarMascara('input[name="cep"]', (valor) => valor.slice(0, 8)
        .replace(/^(\d{5})(\d)/, "$1-$2"));
});
