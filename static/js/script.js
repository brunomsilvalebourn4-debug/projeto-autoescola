document.addEventListener("DOMContentLoaded", () => {

    // =========================
    // CPF / CNPJ
    // =========================

    document.querySelectorAll('input[name="cpf"]').forEach(input => {

        input.addEventListener("input", (e) => {

            let value = e.target.value.replace(/\D/g,'');

            // CPF
            if(value.length <= 11){

                value = value.replace(/(\d{3})(\d)/, '$1.$2');
                value = value.replace(/(\d{3})(\d)/, '$1.$2');
                value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');

            }

            // CNPJ
            else {

                value = value.replace(/^(\d{2})(\d)/, '$1.$2');
                value = value.replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3');
                value = value.replace(/\.(\d{3})(\d)/, '.$1/$2');
                value = value.replace(/(\d{4})(\d)/, '$1-$2');

            }

            e.target.value = value;

        });

    });

    // =========================
    // RG
    // =========================

    document.querySelectorAll('input[name="rg"]').forEach(input => {

        input.addEventListener("input", (e) => {

            let value = e.target.value.replace(/\D/g,'');

            value = value.replace(/(\d{2})(\d)/, '$1.$2');
            value = value.replace(/(\d{3})(\d)/, '$1.$2');
            value = value.replace(/(\d{3})(\d{1})$/, '$1-$2');

            e.target.value = value;

        });

    });

    // =========================
    // TELEFONE
    // =========================

    document.querySelectorAll('input[name="telefone"]').forEach(input => {

        input.addEventListener("input", (e) => {

            let value = e.target.value.replace(/\D/g,'');

            value = value.replace(/^(\d{2})(\d)/g, '($1) $2');
            value = value.replace(/(\d)(\d{4})$/, '$1-$2');

            e.target.value = value;

        });

    });

    // =========================
    // CEP FORMATAÇÃO
    // =========================

    document.querySelectorAll('input[name="cep"]').forEach(input => {

        input.addEventListener("input", (e) => {

            let value = e.target.value.replace(/\D/g,'');

            value = value.replace(/^(\d{5})(\d)/, '$1-$2');

            e.target.value = value;

        });

    });

    // =========================
    // VALOR MONETÁRIO
    // =========================

    document.querySelectorAll('input[name="valor_venda"]').forEach(input => {

        input.addEventListener("input", (e) => {

            let value = e.target.value.replace(/\D/g,'');

            value = (parseInt(value || 0) / 100)
            .toLocaleString('pt-BR', {
                style:'currency',
                currency:'BRL'
            });

            e.target.value = value;

        });

    });

    // =========================
    // VIA CEP
    // =========================

    document.querySelectorAll('input[name="cep"]').forEach(input => {

        input.addEventListener("blur", async (e) => {

            const cep = e.target.value.replace(/\D/g,'');

            // CEP inválido
            if(cep.length !== 8){
                return;
            }

            try {

                const response = await fetch(
                    `https://viacep.com.br/ws/${cep}/json/`
                );

                const data = await response.json();

                // PREENCHER CAMPOS

                const endereco = document.querySelector('input[name="endereco"]');
                const bairro = document.querySelector('input[name="bairro"]');
                const cidade = document.querySelector('input[name="cidade"]');
                const estado = document.querySelector('input[name="estado"]');

                if(endereco){
                    endereco.value = data.logradouro || '';
                }

                if(bairro){
                    bairro.value = data.bairro || '';
                }

                if(cidade){
                    cidade.value = data.localidade || '';
                }

                if(estado){
                    estado.value = data.uf || '';
                }

            } catch (error){

                console.log("Erro ao buscar CEP");

            }

        });

    });

});