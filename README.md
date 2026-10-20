# Automação de regressão – Recruitment (OrangeHRM)

Projeto feito para a Atividade 3 do desafio de Analista de Testes.

A ideia é ter um conjunto pequeno de testes que qualquer pessoa do time consiga rodar (ou que rode sozinho numa pipeline) para avisar rápido quando o fluxo público de recrutamento quebrar depois de alguma mudança em outra parte do sistema.

## Fluxo escolhido e por quê

Escolhi o fluxo **página pública de vagas → abrir uma vaga → formulário de candidatura**.

Motivos:
- É a porta de entrada do candidato. Se essa tela quebra, a empresa simplesmente para de receber currículos, e muitas vezes ninguém percebe na hora, porque quem usa é gente de fora.
- O suporte relatou que o Recruitment volta a dar problema depois de mudanças em outras partes do sistema. Isso é típico de regressão, e regressão é exatamente o que vale a pena automatizar.
- O formulário tem várias validações (campos obrigatórios, formato de e-mail, tipo e tamanho do arquivo) que são chatas e demoradas de testar na mão toda vez.
- Não precisa de login, então dá para rodar em qualquer pipeline sem guardar credencial.

## Cenários automatizados

| # | Cenário | Tipo | O que valida |
|---|---------|------|--------------|
| 1 | Lista de vagas carrega | Positivo | A página pública exibe vagas e a vaga usada no teste está na lista |
| 2 | Apply abre o formulário da vaga certa | Positivo | Ao clicar em Apply, abre o formulário com o título da vaga selecionada |
| 3 | Candidatura válida monta o envio sem gravar | Positivo | Formulário preenchido com dados sintéticos não mostra erro e dispara o POST com os dados certos. O envio é bloqueado antes de chegar no servidor |
| 4 | Campos obrigatórios vazios | Negativo | Primeiro nome, sobrenome, e-mail e currículo mostram "Required" e nada é enviado |
| 5 | E-mail inválido (4 variações) | Negativo | `email-invalido`, `teste@`, `@example.com` e `teste example.com` mostram "Expected format: admin@example.com" |
| 6 | Currículo com extensão não permitida | Limite | Arquivo `.png` mostra "File type not allowed" |
| 7 | Currículo acima de 1 MB | Limite | Arquivo com pouco mais de 1 MB mostra "Attachment Size Exceeded" |
| 8 | Consulta no Candidates (opcional) | Positivo | Com login, a lista de candidatos carrega com as colunas esperadas. Só leitura |

O cenário 8 só roda se as variáveis `ORANGEHRM_USER` e `ORANGEHRM_PASS` estiverem definidas. Sem elas o pytest pula o teste, para não deixar senha no código.

## Como rodar

Pré-requisito: Python 3.10 ou mais novo.

```bash
python -m venv .venv
.venv\Scripts\activate          # no Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
pytest
```

Para rodar também a consulta no Candidates (PowerShell):

```powershell
$env:ORANGEHRM_USER="usuario_da_demo"
$env:ORANGEHRM_PASS="senha_da_demo"
pytest
```

Para ver o navegador abrindo durante a execução: `pytest --headed`

Obs.: no Windows, se a pasta do projeto estiver num caminho muito longo, a instalação do Playwright pode dar erro de DLL ("nome do arquivo muito grande"). Nesse caso é só criar o `.venv` num caminho mais curto.

## Versões usadas

| Ferramenta | Versão |
|------------|--------|
| Python | 3.15.0 (o CI usa 3.12) |
| Playwright (Python) | 1.64.0 |
| pytest | 9.1.1 |
| pytest-playwright | 0.10.0 |
| pytest-html | 4.2.0 |
| Navegador | Chromium (instalado pelo Playwright) |
| Sistema testado | OrangeHRM OS 5.9 (demo pública) |

Execução registrada em **20/10/2026**.

## Dados sintéticos

Todos os dados estão em `data/candidato_sintetico.json`: nome "Teste QA Automacao", e-mail `@example.com` (domínio reservado para testes) e telefone fictício. Não uso nenhum dado pessoal real.

Os arquivos de currículo (`.pdf` válido, `.png` e `.pdf` acima de 1 MB) são gerados na hora pelo `conftest.py`, numa pasta temporária. Assim não preciso versionar arquivo nenhum.

## Como evito sujar o ambiente compartilhado

A demo do OrangeHRM é usada por muita gente ao mesmo tempo, então os testes não podem criar candidaturas.

1. Tem uma trava no `conftest.py` (`bloqueia_escrita_no_ambiente`) que roda em todos os testes e bloqueia qualquer requisição que não seja GET antes de sair do navegador.
2. No cenário positivo, eu deixo o formulário disparar o envio, capturo a requisição (`POST /web/index.php/recruitment/public/applicants`) e confiro método e conteúdo (e-mail, nome e arquivo). A trava bloqueia o envio, então nada é gravado. O teste ainda confirma que a mensagem "Application Received" **não** apareceu.
3. A consulta no Candidates é só leitura. Libero apenas o POST do login.

### Se fosse preciso testar a gravação de ponta a ponta

Para provar o fluxo completo (candidatura aparecendo no Candidates), eu não faria isso na demo pública. Faria assim:

- **Ambiente isolado:** subir o OrangeHRM numa instância própria (eles têm imagem Docker oficial), com banco só para teste, recriado a cada execução da pipeline.
- **Dados identificáveis:** usar um prefixo único em cada execução (ex.: `qa-auto-<data-hora>@example.com`) para achar e limpar só o que o teste criou.
- **Limpeza:** no final do teste, excluir o candidato criado pela própria tela/API de Candidates. Como garantia extra, descartar o banco ao fim da execução.

## Evidências

- `evidencias/`: prints de cada cenário (formulário preenchido, mensagens de erro etc.).
- `relatorio/relatorio.html`: relatório do pytest com o resultado de cada teste. Abre direto no navegador.
- Quando algum teste falha, o Playwright salva print e trace em `test-results/`. O trace abre com `playwright show-trace`.

Resultado da última execução: **10 testes passaram, 1 pulado** (a consulta no Candidates, por não ter credencial definida).

## Limitações conhecidas

- **Ambiente compartilhado e instável:** a demo é pública, às vezes fica lenta e o conteúdo muda ao longo do dia. Na manhã de 20/10 a lista tinha "Software Engineer", "Senior QA Lead" e outras. À noite, essas vagas tinham sumido e no lugar apareceram várias "QA Automation Vacancy ..." criadas pela automação de outras pessoas. Os testes quebraram por isso. Corrigi fazendo o teste tentar a vaga preferida (definida no `data/candidato_sintetico.json`) e, se ela não existir mais, usar a primeira vaga disponível e registrar isso no log. Também aumentei o tempo de espera do carregamento da página.
- **O cenário positivo não prova a gravação no banco**, só que o formulário aceita os dados e envia a requisição correta. A gravação de ponta a ponta precisaria do ambiente isolado descrito acima.
- **Durante o desenvolvimento**, antes de descobrir qual era o endpoint real de envio, uma candidatura com os dados sintéticos ("Teste QA Automacao", `candidato.teste.qa@example.com`) chegou a ser enviada para a demo. Foi a partir disso que criei a trava que bloqueia qualquer escrita. A demo é resetada periodicamente pela OrangeHRM.
- **Só testei no Chromium.** Dá para incluir Firefox e WebKit com `--browser firefox --browser webkit`.
- **A mensagem de erro do Contact Number** (formato de telefone) não foi coberta.

## Como isso pode crescer

- **Rodar na pipeline:** já deixei um workflow em `.github/workflows/testes.yml` que roda os testes a cada push e guarda o relatório e as evidências como artefato.
- **Mais navegadores e mobile:** usar a emulação de dispositivos do Playwright.
- **Testes de API:** validar direto o `POST /recruitment/public/applicants` e as APIs do Candidates. É mais rápido e pega erro de regra de negócio sem depender da tela.
- **Acessibilidade:** incluir checagem com axe-core no formulário público.
- **Ambiente isolado com Docker:** para cobrir o fluxo completo (candidatura → Candidates → status) sem afetar ninguém.

## Estrutura

```
├── conftest.py              # fixtures: dados, arquivos gerados e trava de escrita
├── pytest.ini               # URL base, navegador, relatório HTML
├── requirements.txt
├── data/
│   └── candidato_sintetico.json
├── pages/                   # page objects (seletores e ações de cada tela)
│   ├── vacancies_page.py
│   └── apply_page.py
├── tests/
│   ├── test_vacancies.py
│   ├── test_application_form.py
│   └── test_candidates_consulta.py
└── .github/workflows/testes.yml
```
