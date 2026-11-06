"""Offline checks for optional browser setup in targeted snow refreshes."""

import importlib.util
from pathlib import Path

import pytest
from aggregator.config import STORES, StoreConfig

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location('snow_refresh_runtime', ROOT / 'scripts/snow_refresh_runtime.py')
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)


@pytest.mark.parametrize(('selection', 'expected'), [
    ('The Circle Whistler', False),
    ('Aspen Ski and Board', False),
    ('The Circle Whistler,Aspen Ski and Board', False),
    ('Evo', False),
    ('Backcountry', True),
    ('The Circle Whistler,Backcountry', True),
    ('', True),
    ('Unknown retailer', True),
    ('The Circle Whistler,Unknown retailer', True),
    ('The Circle Whistler,', True),
    (',The Circle Whistler', True),
    ('The Circle Whistler,,Aspen Ski and Board', True),
    (',', True),
    (' ', True),
    (' The Circle Whistler', True),
    ('The Circle Whistler\nBackcountry', True),
])
def test_browser_requirement_uses_actual_configured_selection(selection, expected):
    assert runtime.browser_required(selection, STORES) is expected


@pytest.mark.parametrize('store', STORES, ids=lambda store: store.name)
def test_each_configured_retailer_uses_its_browser_flag(store):
    assert runtime.browser_required(store.name, STORES) is store.use_browser


def test_browser_requirement_follows_registry_changes():
    store = StoreConfig('Changing retailer', 'example.test', use_browser=False)
    assert runtime.browser_required(store.name, [store]) is False
    store.use_browser = True
    assert runtime.browser_required(store.name, [store]) is True


def test_runtime_appends_boolean_workflow_output(monkeypatch, tmp_path, capsys):
    output = tmp_path / 'github-output'
    output.write_text('existing=value\n')
    monkeypatch.setenv('GITHUB_OUTPUT', str(output))
    monkeypatch.setenv('REFRESH_STORES', 'The Circle Whistler')

    runtime.main()

    assert output.read_text() == 'existing=value\nbrowser_required=false\n'
    assert capsys.readouterr().out == ''


def test_runtime_without_selection_keeps_browser_setup(monkeypatch, tmp_path):
    output = tmp_path / 'github-output'
    monkeypatch.setenv('GITHUB_OUTPUT', str(output))
    monkeypatch.delenv('REFRESH_STORES', raising=False)

    runtime.main()

    assert output.read_text() == 'browser_required=true\n'


def test_runtime_prints_boolean_when_workflow_output_is_absent(monkeypatch, capsys):
    monkeypatch.delenv('GITHUB_OUTPUT', raising=False)
    monkeypatch.setenv('REFRESH_STORES', 'The Circle Whistler')

    runtime.main()

    assert capsys.readouterr().out == 'browser_required=false\n'


def test_workflow_consumes_runtime_output_without_interpolating_shell_input():
    workflow = (ROOT / '.github/workflows/scrape.yml').read_text()
    decision = workflow.split('      - name: Determine scraper runtime\n')[1].split('      - name: Install Playwright Chromium\n')[0]
    install = workflow.split('      - name: Install Playwright Chromium\n')[1].split('      - name: Run scraper\n')[0]

    assert '        id: scraper-runtime\n' in decision
    assert '          REFRESH_STORES: ${{ inputs.stores }}\n' in decision
    assert '        run: python scripts/snow_refresh_runtime.py\n' in decision
    assert "        if: steps.scraper-runtime.outputs.browser_required == 'true'\n" in install
    assert '        run: playwright install chromium --with-deps\n' in install
