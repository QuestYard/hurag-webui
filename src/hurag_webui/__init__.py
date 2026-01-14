__version__ = "0.1.0"
__author__ = "Libin, HuRAG Team"
__email__ = "154788733@qq.com"
__url__=""
__description__ = "HuRAG WebUI"

import yaml
import logging
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path.cwd() / ".webui.env")

from hurag import conf as hurag_conf
from hurag.utilities import generate_id, dict_to_namespace

# -- Global Variables --

conf = None
logger = None
org_path = hurag_conf.app.org_path

# -- Initialization --

# conf
try:
    with open(Path.cwd() / "webui-config.yaml", "r", encoding="utf-8") as f:
        conf = yaml.safe_load(f)
    conf = dict_to_namespace(conf)
    if (
        conf.mariadb.user is None
        or conf.mariadb.password is None
        or conf.mariadb.database is None
    ):
        raise ValueError(
            "Missing required configurations: mariadb.user, mariadb.password, "
            "mariadb.database must be provided."
        )
    if conf.services.ctx_size.lower() not in ["tiny", "medium", "large"]:
        conf.services.ctx_size = "large"
    conf.mariadb.host = conf.mariadb.host or "localhost"
    conf.mariadb.port = conf.mariadb.port or 3306
except ValueError as ve:
    raise ve
except Exception as e:
    raise RuntimeError(f"Config file not exists or invalid: {e}")

# logger
logger = logging.getLogger("hurag_webui")
logger.propagate = False
logger.setLevel(logging.DEBUG)
fmt = logging.Formatter("%(asctime)s [%(name)s] %(levelname)s - %(message)s")
console_handler = logging.StreamHandler()
console_handler.setFormatter(fmt)
console_handler.setLevel(logging.WARNING)
logger.addHandler(console_handler)
from logging.handlers import RotatingFileHandler
file_handler = RotatingFileHandler(
    filename=Path.cwd() / "hurag_webui.log",
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8",
)
file_handler.setFormatter(fmt)
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

__all__ = [
    "conf",
    "logger",
    "org_path",
    "hurag_conf",
    "generate_id",
]
