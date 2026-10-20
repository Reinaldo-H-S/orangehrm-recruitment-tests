from playwright.sync_api import Page, expect


class VacanciesPage:
    """Página pública com a lista de vagas abertas (não precisa de login)."""

    PATH = "/web/index.php/recruitmentApply/jobs.html"

    def __init__(self, page: Page):
        self.page = page
        self.cards = page.locator(".orangehrm-vacancy-card-header")

    def open(self):
        # a demo pública às vezes demora para terminar o "load"; basta o DOM e os cards aparecerem
        self.page.goto(self.PATH, wait_until="domcontentloaded", timeout=60_000)
        expect(self.cards.first).to_be_visible(timeout=30_000)

    def vacancy_titles(self) -> list[str]:
        return [t.strip() for t in self.cards.locator(".oxd-text--card-title").all_inner_texts()]

    def choose_vacancy(self, preferred: str) -> str:
        """
        Usa a vaga preferida se ela existir. Como a demo é compartilhada e as vagas mudam,
        se a preferida sumir eu pego a primeira vaga disponível em vez de quebrar o teste.
        """
        titles = self.vacancy_titles()
        if preferred in titles:
            return preferred
        print(f"Vaga '{preferred}' não está mais na demo. Usando '{titles[0]}'. Vagas atuais: {titles}")
        return titles[0]

    def apply_to(self, title: str):
        card = self.cards.filter(has=self.page.get_by_text(title, exact=True)).first
        card.get_by_role("button", name="Apply").click()
