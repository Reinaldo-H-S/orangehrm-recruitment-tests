import re

from playwright.sync_api import Page, expect

from pages.apply_page import ApplyPage
from pages.vacancies_page import VacanciesPage


def test_lista_de_vagas_carrega(page: Page):
    vacancies = VacanciesPage(page)
    vacancies.open()

    titles = vacancies.vacancy_titles()
    print(f"Vagas exibidas: {titles}")

    assert len(titles) > 0, "A página pública não exibiu nenhuma vaga"
    assert all(t for t in titles), "Existe card de vaga sem título"
    expect(vacancies.cards.get_by_role("button", name="Apply")).to_have_count(len(titles))
    page.screenshot(path="evidencias/00_lista_de_vagas.png", full_page=True)


def test_apply_abre_formulario_da_vaga_certa(page: Page, test_data):
    vacancies = VacanciesPage(page)
    vacancies.open()
    vaga = vacancies.choose_vacancy(test_data["vaga"])
    vacancies.apply_to(vaga)

    apply = ApplyPage(page)
    expect(page).to_have_url(re.compile(r"/recruitmentApply/applyVacancy/id/\d+"))
    expect(page.get_by_text(f"Apply for {vaga}")).to_be_visible()
    expect(apply.first_name).to_be_visible()
    expect(apply.resume).to_be_attached()
