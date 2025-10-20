"""
İstatistik Sistemi
==================

Bu modül, duygu istatistik sorgularını (today/all ve isteğe bağlı emotion filtresi)
`data/` altındaki kalıcı dosyaları okuyarak hesaplar ve doğal dilde özet üretir.

Güvenlik/sağlamlık notları:
- Dosya okuma try/except ile korunur.
- Kullanıcı mesajı regex ile güvenli biçimde ayrıştırılır (komut enjekte edilmez).
- Hatalarda kullanıcıya sade ve zararsız bir mesaj döner.
"""

from __future__ import annotations

import os
import json
import re
from typing import Any, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path


# Veri dizini ve dosyalar
DATA_DIR = Path(__file__).parent / "data"
CHAT_HISTORY_FILE = DATA_DIR / "chat_history.txt"
MOOD_COUNTER_FILE = DATA_DIR / "mood_counter.txt"


class StatisticSystem:
    """Duygu istatistik sistemi - dosyalardan okuyup özet üretir."""

    def __init__(self) -> None:
        # Desteklenen duygular (Emotion sistemi ile uyumlu)
        self.allowed_moods = [
            "Mutlu", "Üzgün", "Öfkeli", "Şaşkın", "Utangaç",
            "Endişeli", "Yorgun", "Gururlu", "Çaresiz", "Flörtöz"
        ]

    # -------------------------- Yardımcılar -------------------------- #
    def _normalize_emotion(self, name: str | None) -> Optional[str]:
        if not name:
            return None
        n = str(name).strip().lower()
        for m in self.allowed_moods:
            if m.lower() == n:
                return m
        return None

    def _detect_period_and_emotion(self, user_message: str) -> Tuple[str, Optional[str]]:
        """Mesajdan period (today/all) ve isteğe bağlı emotion’u çıkartır.
        Basit bir regex/keyword yaklaşımı; gerekirse LLM üstünden geliştirilebilir.
        """
        t = (user_message or "").lower()

        # period
        period = "today" if any(k in t for k in ["bugün", "today", "günlük"]) else "all"

        # emotion (desteklenenlerden biri geçiyorsa al)
        detected_emotion: Optional[str] = None
        for m in self.allowed_moods:
            if m.lower() in t:
                detected_emotion = m
                break

        # get_emotion_stats(...) düz metin döndüyse parametreleri yakala (opsiyonel)
        try:
            m1 = re.search(r'get_emotion_stats\(\s*emotion\s*=\s*"([^"]+)"\s*(?:,\s*period\s*=\s*"(today|all)")?\s*\)', t, re.IGNORECASE)
            m2 = re.search(r'get_emotion_stats\(\s*period\s*=\s*"(today|all)"\s*(?:,\s*emotion\s*=\s*"([^"]+)")?\s*\)', t, re.IGNORECASE)
            if m1:
                detected_emotion = self._normalize_emotion(m1.group(1)) or detected_emotion
                period = (m1.group(2) or period) if len(m1.groups()) >= 2 else period
            elif m2:
                period = m2.group(1) or period
                e2 = m2.group(2) if len(m2.groups()) >= 2 else None
                if e2:
                    detected_emotion = self._normalize_emotion(e2) or detected_emotion
        except Exception:
            pass

        return period, detected_emotion

    # -------------------------- Hesaplama --------------------------- #
    def _read_persisted_counts(self) -> Dict[str, int]:
        """mood_counter.txt içindeki tüm zamanlar sayacını oku (yoksa boş)."""
        try:
            if MOOD_COUNTER_FILE.exists():
                raw = MOOD_COUNTER_FILE.read_text(encoding="utf-8").strip() or "{}"
                data = json.loads(raw)
                if isinstance(data, dict):
                    return {str(k): int(v) for k, v in data.items()}
        except Exception:
            pass
        return {m: 0 for m in self.allowed_moods}

    def _read_today_counts_from_chat_history(self) -> Dict[str, int]:
        """chat_history.txt içinden sadece bugün tarihli satırlardan duygu say.
        Not: emotion_system JSON formatına göre kaba çıkarım yapar.
        """
        counts: Dict[str, int] = {m: 0 for m in self.allowed_moods}
        today_str = datetime.now().strftime("%Y-%m-%d")
        try:
            if CHAT_HISTORY_FILE.exists():
                for line in CHAT_HISTORY_FILE.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    obj = json.loads(line)
                    ts = str(obj.get("timestamp", ""))
                    if not ts.startswith(today_str):
                        continue
                    resp = str(obj.get("response", ""))
                    try:
                        data = json.loads(resp)
                    except Exception:
                        data = None
                    if isinstance(data, dict):
                        for key in ["kullanici_ruh_hali", "ilk_ruh_hali", "ikinci_ruh_hali"]:
                            val = str(data.get(key, "")).strip()
                            if val in counts:
                                counts[val] += 1
        except Exception:
            pass
        return counts

    def compute_stats(self, period: str = "all", emotion: Optional[str] = None) -> Dict[str, Any]:
        """İstatistik hesapla ve özet üret."""
        period_norm = (period or "all").lower()
        if period_norm not in ("all", "today"):
            period_norm = "all"

        if period_norm == "today":
            counts = self._read_today_counts_from_chat_history()
        else:
            counts = self._read_persisted_counts()

        # İsteğe bağlı tek duygu filtresi
        emo_norm = self._normalize_emotion(emotion)
        if emo_norm:
            only = counts.get(emo_norm, 0)
            summary = f"{emo_norm} duygu {only} kez kaydedildi"
            return {"counts": counts, "summary": summary, "period": period_norm, "emotion": emo_norm}

        # Genel özet
        parts = [f"{cnt} kez {m.lower()}" for m, cnt in counts.items() if cnt > 0]
        summary = ", ".join(parts) if parts else "Henüz duygu kaydı yok"
        return {"counts": counts, "summary": summary, "period": period_norm}

    # -------------------------- Dış API ----------------------------- #
    def answer(self, user_message: str) -> Dict[str, Any]:
        """Kullanıcı mesajını yorumla ve istatistik cevabı üret."""
        try:
            period, emotion = self._detect_period_and_emotion(user_message or "")
            result = self.compute_stats(period=period, emotion=emotion)
            return {"stats": True, "response": result.get("summary", ""), **result}
        except Exception as e:
            return {"stats": True, "response": f"İstatistik hesaplanamadı: {e}"}


