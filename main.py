#!/usr/bin/env python3
"""
RPA Lab - Sistema de Automação de Processos Robóticos

Ponto de entrada principal da aplicação.
"""
import sys
import traceback
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def _get_exe_dir() -> Path:
    """Retorna o diretório do executável (funciona tanto em .exe quanto em script)."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def _write_crash_log(error: str) -> None:
    """Escreve um log de crash no diretório do executável."""
    try:
        crash_log = _get_exe_dir() / "crash.log"
        with open(crash_log, "w", encoding="utf-8") as f:
            f.write(error)
    except Exception:
        pass


def main():
    """Main entry point for RPA Lab."""
    try:
        from src.gui.app import App
        from src.utils.logger import logger

        logger.info("Starting RPA Lab...")

        app = App()
        app.run()

    except ImportError as e:
        msg = f"Erro ao importar módulos: {e}\n\n{traceback.format_exc()}"
        _write_crash_log(msg)
        # Tenta exibir via messagebox se tkinter disponível
        try:
            import tkinter.messagebox as mb
            mb.showerror("Erro de Importação", msg[:500])
        except Exception:
            pass
        sys.exit(1)

    except Exception as e:
        msg = f"Erro ao iniciar a aplicação: {e}\n\n{traceback.format_exc()}"
        _write_crash_log(msg)
        try:
            import tkinter.messagebox as mb
            mb.showerror("Erro Fatal", msg[:500])
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
