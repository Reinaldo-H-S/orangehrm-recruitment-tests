from pathlib import Path

from playwright.sync_api import Page


class ApplyPage:
    """Formulário público de candidatura de uma vaga."""

    def __init__(self, page: Page):
        self.page = page
        self.title = page.locator("h5, .orangehrm-card-container .oxd-text--h5").first
        self.first_name = page.locator("input[name='firstName']")
        self.middle_name = page.locator("input[name='middleName']")
        self.last_name = page.locator("input[name='lastName']")
        self.email = page.locator("input[name='email']")
        self.contact_number = page.locator("input[name='contactNumber']")
        self.resume = page.locator("input[name='resume']")
        self.keywords = page.locator("input[name='keywords']")
        self.notes = page.locator("textarea[name='comment']")
        self.consent = page.locator("input[name='consentToKeepData']")
        self.submit_button = page.get_by_role("button", name="Submit")
        self.error_messages = page.locator(".oxd-input-field-error-message")

    def fill_form(self, candidate: dict, resume_file: Path | None = None):
        self.first_name.fill(candidate["first_name"])
        self.middle_name.fill(candidate.get("middle_name", ""))
        self.last_name.fill(candidate["last_name"])
        self.email.fill(candidate["email"])
        self.contact_number.fill(candidate.get("contact_number", ""))
        self.keywords.fill(candidate.get("keywords", ""))
        self.notes.fill(candidate.get("notes", ""))
        if resume_file:
            self.resume.set_input_files(resume_file)
        if candidate.get("consent"):
            # o checkbox real fica escondido atrás do componente visual do OrangeHRM
            self.consent.check(force=True)

    def submit(self):
        self.submit_button.click()

    def error_for(self, field_label: str):
        """Retorna a mensagem de erro exibida embaixo de um campo, pelo texto do label."""
        group = self.page.locator(".oxd-input-group").filter(
            has=self.page.locator("label", has_text=field_label)
        )
        return group.locator(".oxd-input-field-error-message")
