# 📦 Gerar Executável — RPA Lab

## Pré-requisitos

```bash
pip install -r requirements.txt
pip install pyinstaller
```

---

## Gerar o `.exe`

```bash
python -m PyInstaller rpa_lab.spec --clean
```

O executável será gerado em:

```
dist/RPA-Lab.exe
```

> As pastas `dist/data/` e `dist/logs/` são criadas automaticamente na primeira execução, ao lado do `.exe`.

---

## Rebuild rápido (sem limpar cache)

```bash
python -m PyInstaller rpa_lab.spec
```

---

## Limpar arquivos temporários

```powershell
# PowerShell
Remove-Item -Recurse -Force build, dist
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\pyinstaller"
```

```cmd
:: CMD
rmdir /s /q build dist
rmdir /s /q "%LOCALAPPDATA%\pyinstaller"
```

---

## Personalizar

Edite `rpa_lab.spec` conforme necessário:

| Opção | Descrição |
|---|---|
| `name='RPA-Lab'` | Nome do `.exe` |
| `console=False` | `True` para exibir terminal (útil para debug) |
| `icon=None` | Caminho para um `.ico` personalizado |

---

## ⚠️ Avisos durante a build (inofensivos)

- `Hidden import 'pyyaml' not found` — o pacote usa o nome `yaml` internamente.
- `Hidden import 'python_dotenv' not found` — o pacote usa o nome `dotenv`.
- Avisos de `MySQLdb`, `psycopg2` — o projeto usa apenas SQLite.
