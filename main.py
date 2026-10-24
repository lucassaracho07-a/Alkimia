import logging

from app.log import setup_logging
from app.ui.login import LoginWindow

logger = logging.getLogger("alkimia")


def main() -> None:
    setup_logging()
    logger.info("ALKIMIA iniciando")
    LoginWindow().mainloop()
    logger.info("ALKIMIA finalizado")


if __name__ == "__main__":
    main()
