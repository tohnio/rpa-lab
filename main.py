#!/usr/bin/env python3
"""
RPA Lab - Sistema de Automação de Processos Robóticos

Ponto de entrada principal da aplicação.
"""
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def main():
    """Main entry point for RPA Lab."""
    try:
        from src.gui.app import App
        from src.utils.logger import logger
        
        logger.info("Starting RPA Lab...")
        
        app = App()
        app.run()
        
    except ImportError as e:
        print(f"Erro ao importar módulos: {e}")
        print("\nCertifique-se de instalar as dependências:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Erro ao iniciar a aplicação: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()