"""
Consulta no módulo Candidates (área interna, precisa de login).

Só leitura: o teste não cria, edita nem exclui nada. As credenciais NÃO ficam no
código; são lidas das variáveis de ambiente ORANGEHRM_USER e ORANGEHRM_PASS.
Sem elas o teste é pulado.
"""
import os
import re

import pytest
from playwright.sync_api import Page, expect

USER = os.getenv("ORANGEHRM_USER")
PASSWORD = os.getenv("ORANGEHRM_PASS")

pytestmark = pytest.mark.skipif(
    not (USER and PASSWORD),
    reason="Defina ORANGEHRM_USER e ORANGEHRM_PASS para rodar a consulta no Candidates",
)


@pytest.fixture
def libera_login(page: Page):
    # a trava do conftest bloqueia todo POST; aqui liberamos só o POST do login
    page.route("**/auth/validate", lambda route: route.continue_())


def test_lista_de_candidatos_carrega(page: Page, libera_login):
    page.goto("/web/index.php/auth/login", wait_until="domcontentloaded", timeout=60_000)
    page.get_by_placeholder("Username").fill(USER)
    page.get_by_placeholder("Password").fill(PASSWORD)
    page.get_by_role("button", name="Login").click()
    expect(page).to_have_url(re.compile(r"/dashboard"), timeout=30_000)

    page.goto("/web/index.php/recruitment/viewCandidates", wait_until="domcontentloaded")
    expect(page.get_by_role("heading", name="Candidates")).to_be_visible(timeout=30_000)

    expect(page.get_by_role("columnheader").first).to_be_visible(timeout=30_000)
    headers = page.get_by_role("columnheader").all_inner_texts()
    for coluna in ["Vacancy", "Candidate", "Hiring Manager", "Date of Application", "Status"]:
        assert any(coluna in h for h in headers), f"Coluna '{coluna}' não encontrada em {headers}"

    page.screenshot(path="evidencias/06_candidates_consulta.png", full_page=True)
