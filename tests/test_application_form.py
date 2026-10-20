"""
Testes do formulário público de candidatura.

Importante: a demo do OrangeHRM é compartilhada. Para não poluir o ambiente,
o cenário positivo intercepta o envio (POST /recruitment/public/applicants) e
bloqueia a requisição antes de chegar no servidor. Assim dá para validar que o
formulário aceitou os dados e montou o envio certo, sem criar candidato de verdade.
"""
import re

import pytest
from playwright.sync_api import Page, expect

from conftest import SUBMIT_PATH
from pages.apply_page import ApplyPage
from pages.vacancies_page import VacanciesPage


@pytest.fixture
def apply_page(page: Page, test_data) -> ApplyPage:
    vacancies = VacanciesPage(page)
    vacancies.open()
    vacancies.apply_to(vacancies.choose_vacancy(test_data["vaga"]))
    apply = ApplyPage(page)
    expect(apply.first_name).to_be_visible()
    return apply


def test_candidatura_valida_monta_envio_sem_gravar(apply_page: ApplyPage, page: Page, test_data, files,
                                                  bloqueia_escrita_no_ambiente):
    candidate = test_data["candidato"]
    apply_page.fill_form(candidate, resume_file=files["valid"])
    page.screenshot(path="evidencias/01_formulario_preenchido.png", full_page=True)

    expect(apply_page.error_messages).to_have_count(0)

    # o envio é capturado aqui e bloqueado pela trava do conftest (não chega no servidor)
    with page.expect_request(lambda r: SUBMIT_PATH in r.url) as submit_info:
        apply_page.submit()
    request = submit_info.value

    assert request.method == "POST"
    # como o envio foi bloqueado, a confirmação "Application Received" não pode aparecer
    expect(page.get_by_text("Application Received")).not_to_be_visible()
    assert any(SUBMIT_PATH in r for r in bloqueia_escrita_no_ambiente), "O envio não passou pela trava!"

    body = (request.post_data_buffer or b"").decode("latin-1")
    assert candidate["email"] in body
    assert candidate["first_name"] in body
    assert "curriculo_teste.pdf" in body


def test_campos_obrigatorios_vazios(apply_page: ApplyPage, page: Page):
    apply_page.submit()

    # Full Name (first e last), Email e Resume são obrigatórios
    expect(apply_page.error_messages.filter(has_text="Required")).to_have_count(4)
    expect(apply_page.error_for("Email")).to_have_text("Required")
    expect(apply_page.error_for("Resume")).to_have_text("Required")
    # continua na mesma tela, nada foi enviado
    expect(page).to_have_url(re.compile(r"/recruitmentApply/applyVacancy/id/\d+"))
    page.screenshot(path="evidencias/02_campos_obrigatorios.png", full_page=True)


@pytest.mark.parametrize("email_invalido", ["email-invalido", "teste@", "@example.com", "teste example.com"])
def test_email_invalido(apply_page: ApplyPage, page: Page, test_data, files, email_invalido):
    candidate = dict(test_data["candidato"], email=email_invalido)
    apply_page.fill_form(candidate, resume_file=files["valid"])
    apply_page.submit()

    expect(apply_page.error_for("Email")).to_have_text("Expected format: admin@example.com")
    page.screenshot(path=f"evidencias/03_email_invalido_{email_invalido.replace('@', 'at').replace(' ', '_')}.png")


def test_curriculo_com_extensao_nao_permitida(apply_page: ApplyPage, page: Page, test_data, files):
    apply_page.fill_form(test_data["candidato"], resume_file=files["not_allowed"])
    apply_page.submit()

    expect(apply_page.error_for("Resume")).to_have_text("File type not allowed")
    page.screenshot(path="evidencias/04_extensao_nao_permitida.png", full_page=True)


def test_curriculo_acima_de_1mb(apply_page: ApplyPage, page: Page, test_data, files):
    apply_page.fill_form(test_data["candidato"], resume_file=files["too_big"])
    apply_page.submit()

    expect(apply_page.error_for("Resume")).to_have_text("Attachment Size Exceeded")
    page.screenshot(path="evidencias/05_arquivo_acima_1mb.png", full_page=True)
