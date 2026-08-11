"""
Merkezi loglama yapılandırması. Diğer modüller:

    from log_ayarlari import logger_al
    log = logger_al(__name__)
    log.info("...")
    log.warning("...")
    log.error("...", exc_info=True)

şeklinde kullanır. Konsola VE 'uygulama.log' dosyasına aynı anda yazar.
"""

import logging
import sys

_KURULUM_YAPILDI = False


def _kok_loglayiciyi_kur():
    global _KURULUM_YAPILDI
    if _KURULUM_YAPILDI:
        return

    kok = logging.getLogger("bist_analiz")
    kok.setLevel(logging.INFO)

    bicim = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    dosya_handler = logging.FileHandler("uygulama.log", encoding="utf-8")
    dosya_handler.setFormatter(bicim)

    konsol_handler = logging.StreamHandler(sys.stdout)
    konsol_handler.setFormatter(bicim)

    kok.addHandler(dosya_handler)
    kok.addHandler(konsol_handler)
    kok.propagate = False

    _KURULUM_YAPILDI = True


def logger_al(modul_adi):
    """Verilen modül adına özel bir logger döner (örn. logger_al(__name__))."""
    _kok_loglayiciyi_kur()
    return logging.getLogger(f"bist_analiz.{modul_adi}")
