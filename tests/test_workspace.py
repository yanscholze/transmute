import json

import pytest

from app.core.catalog import discover, rules_path, verify_rules, workspace_config
from app.core.exporters.writer import export
from app.core.importers.reader import inspect
from app.core.mapping import suggest
from app.core.session import process
from app.storage.local import LocalStore
from app.storage.workspace import import_model, initialize, save_config, save_rule_revision, set_brand
from tests.conftest import ROOT


def test_whitelabel_folder_upload_custom_rules(tmp_path, make_xlsx, options):
    root = initialize(ROOT, tmp_path / "state")
    config = workspace_config(root)
    config.update(models_dir=str(tmp_path / "sem-modelos"), recognize_original_names=False)
    save_config(root, config)
    path = make_xlsx(["Nome", "Código interno"], [], "layout_especial.xlsx")
    uploaded = import_model(root, path)
    layouts = discover(root)
    assert len(layouts) == 1 and layouts[0].family == "generic" and uploaded != path
    profile = {"max_total_rows": 10000, "enabled_modules": [], "rules": [{"id": "NOME", "field": "Nome", "operation": "required"}]}
    save_rule_revision(root, "# Regras da empresa sintética\nNome é obrigatório.", profile)
    verify_rules(root)
    assert rules_path(root).read_text().startswith("# Regras da empresa")
    sourcepath = make_xlsx(["Nome", "Código interno"], [["Pessoa sintética", "000001"]], "recebido.xlsx")
    source = inspect(sourcepath, header_row=1)
    session = process(root, tmp_path, source, layouts[0], suggest(source, layouts[0]), options)
    try:
        assert session.stats()["errors"] == 0
        out = export([session], tmp_path)
        assert list(out.glob("*.xlsx"))
        save_rule_revision(root, "# Nova regra", profile)
        with pytest.raises(ValueError, match="mudaram"):
            export([session], tmp_path)
    finally:
        session.close()
    assert path.is_file()
    set_brand(root, "Marca Sintética", "#284B80")
    assert workspace_config(root)["brand"] == "Marca Sintética"


def test_declarative_validation_and_no_default_identifiers(tmp_path):
    from app.core.rules.declarative import apply, validate_profile
    profile = {"max_total_rows": 10000, "enabled_modules": [], "rules": [
        {"id": "A", "field": "Nome", "operation": "required"},
        {"id": "B", "field": "Status", "operation": "default", "value": "Ativo"},
        {"id": "C", "field": "Valor", "operation": "decimal"},
        {"id": "D", "field": "Data", "operation": "date", "input_format": "%Y-%m-%d"}]}
    validate_profile(profile)
    values = {"Nome": "", "Status": "", "Valor": "1.234,567", "Data": "2026-10-22"}
    issues, changes = apply(values, "generic", profile)
    assert issues[0].code == "A" and values["Valor"] == "1234,567" and values["Data"] == "22/10/2026"
    assert len(changes) == 3
    profile["rules"] = [{"id": "INVENTAR", "field": "CPF/CNPJ", "operation": "default", "value": "00000000191"}]
    with pytest.raises(ValueError, match="identificadores"):
        validate_profile(profile)


def test_local_store_only_minimal_history_and_profiles(tmp_path):
    store = LocalStore(tmp_path)
    store.record("Clientes", {"read": 1}, "Processado")
    assert "00000000191" not in store.path.read_bytes().decode("latin-1")
    store.save_profile("Exemplo", "fingerprint", {"Nome": "Razão Social / Nome"})
    assert store.profiles("fingerprint")[0][3]["Nome"] == "Razão Social / Nome"
    store.delete_profile(store.profiles()[0][0])
    assert not store.profiles()
    with pytest.raises(ValueError):
        store.set_setting("api_key", "synthetic")
    store.clear_history()
    assert not store.history()


def test_report_copy_to_selected_partial_directory(convert, layout, tmp_path):
    session = convert(layout("veiculos"), ["descricao"], [["Sintético"]])
    folder = export([session], tmp_path / "Tratadas", diagnostics_destination=tmp_path / "Parciais" / "V1")
    diag = tmp_path / "Parciais" / "V1" / folder.name
    assert (diag / "resumo.txt").is_file() and not list(diag.glob("*.xlsx"))
    assert json.loads((diag / "relatorio.json").read_text())["datasets"][0]["statistics"]["read"] == 1


def test_portable_branded_library_uses_relative_sources(tmp_path, make_xlsx, options):
    import shutil
    from app.core.catalog import digest
    bundle = tmp_path / "bundle"
    models = bundle / "#PLANILHAS DE BASE" / "Empresa"
    models.mkdir(parents=True)
    template = make_xlsx(["Nome", "Código"], [], "modelo_customizado.xlsx")
    shutil.copy2(template, models / template.name)
    (bundle / "INSTRUCOES_CONVERSOES.md").write_text("# Regras\nNome obrigatório.")
    profile = {"max_total_rows": 10000, "source_sha256": digest(bundle / "INSTRUCOES_CONVERSOES.md"), "enabled_modules": [], "rules": [{"id": "NOME", "field": "Nome", "operation": "required"}]}
    (bundle / "regras_perfil.json").write_text(json.dumps(profile))
    relative = "#PLANILHAS DE BASE/Empresa/" + template.name
    logo = bundle / "marca" / "logo.png"
    logo.parent.mkdir()
    logo.write_bytes(b"synthetic-preset-path-only")
    (bundle / "library_preset.json").write_text(json.dumps({"brand": "Empresa Sintética", "primary_color": "#284B80", "recognize_original_names": False, "families": {relative: "generic"}, "logo_path": "marca/logo.png", "logo_size": 67, "logo_opacity": 12}))
    root = initialize(bundle, tmp_path / "state")
    assert workspace_config(root)["brand"] == "Empresa Sintética"
    assert workspace_config(root)["logo_path"] == str(logo)
    assert workspace_config(root)["logo_size"] == 67
    assert workspace_config(root)["logo_opacity"] == 12
    layouts = discover(root)
    assert len(layouts) == 1 and layouts[0].family == "generic"
    source = inspect(make_xlsx(["Nome", "Código"], [["Dado sintético", "0001"]], "entrada.xlsx"), header_row=1)
    session = process(root, tmp_path, source, layouts[0], suggest(source, layouts[0]), options)
    try:
        assert session.stats()["errors"] == 0
        assert next(session.rows())["values"]["Código"] == "0001"
    finally:
        session.close()
