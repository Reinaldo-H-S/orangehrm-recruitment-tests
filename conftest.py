import json
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent / "data"
(Path(__file__).parent / "evidencias").mkdir(exist_ok=True)


# endpoint que recebe a candidatura (descoberto inspecionando a rede no navegador)
SUBMIT_PATH = "/recruitment/public/applicants"


@pytest.fixture(autouse=True)
def bloqueia_escrita_no_ambiente(page):
    """
    Trava de segurança: a demo é compartilhada, então nenhum teste pode gravar dados.
    Qualquer requisição que não seja GET é bloqueada antes de sair do navegador e fica
    registrada na lista, para o teste conferir o que tentou ser enviado.
    """
    bloqueadas = []

    def guard(route):
        if route.request.method in ("GET", "HEAD", "OPTIONS"):
            route.continue_()
        else:
            bloqueadas.append(f"{route.request.method} {route.request.url}")
            route.abort()

    page.route("**/*", guard)
    yield bloqueadas


@pytest.fixture(scope="session")
def test_data():
    with open(DATA_DIR / "candidato_sintetico.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def files(tmp_path_factory):
    """Arquivos de currículo gerados na hora, só com conteúdo fictício."""
    folder = tmp_path_factory.mktemp("arquivos")

    valid_pdf = folder / "curriculo_teste.pdf"
    valid_pdf.write_bytes(
        b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
    )

    not_allowed = folder / "curriculo_teste.png"
    not_allowed.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 100)

    too_big = folder / "curriculo_grande.pdf"
    too_big.write_bytes(b"%PDF-1.4\n" + b"0" * (1024 * 1024 + 10))  # pouco acima de 1MB

    return {"valid": valid_pdf, "not_allowed": not_allowed, "too_big": too_big}
