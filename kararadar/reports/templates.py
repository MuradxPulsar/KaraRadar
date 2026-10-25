"""Language templates and CERT email template."""

STRINGS = {
    "az": {
        "title": "KaraRadar hesabatı",
        "disclaimer": "Bu avtomatik ilkin qiymətləndirmədir, insan yoxlaması tələb olunur.",
        "verdict_label": "Qərar",
        "score_label": "Xal",
        "signals_title": "NİYƏ?",
        "whitelist_note": "Rəsmi domain — avtomatik istisna (heç vaxt şübhəli sayılmır).",
        "no_brand": "Brend uyğunluğu: tapılmadı (neytral).",
        "advice": "rəsmi kanalla yoxla",
        "cert_email_subject": "Şübhəli domain bildirişi — KaraRadar",
    },
    "en": {
        "title": "KaraRadar report",
        "disclaimer": "This is an automated preliminary assessment; human review is required.",
        "verdict_label": "Verdict",
        "score_label": "Score",
        "signals_title": "WHY?",
        "whitelist_note": "Official domain — automatically excluded (never flagged).",
        "no_brand": "Brand match: not found (neutral).",
        "advice": "verify via official channel",
        "cert_email_subject": "Suspicious domain notice — KaraRadar",
    },
}

CERT_EMAIL_TEMPLATE = """To: info@cert.gov.az
Subject: {subject}

Hörmətli CERT komandası,

Aşağıdakı domain Azərbaycan brendlərinə bənzəyən şəkildə qeydə alınmış
ola bilər. Zəhmət olmasa yoxlayasınız.

Domain: {domain}
Verdict: {verdict}
Score: {score}

Signals:
{signals}

Bu avtomatik ilkin qiymətləndirmədir, insan yoxlaması tələb olunur.

Hörmətlə,
KaraRadar
"""

def cert_email(domain, verdict, score, signals):
    sig_text = "\n".join(f"- {s.get('signal')}: {s.get('detail')} (weight {s.get('weight')})"
                        for s in (signals or []))
    return CERT_EMAIL_TEMPLATE.format(subject=STRINGS["az"]["cert_email_subject"],
                                     domain=domain, verdict=verdict,
                                     score=score, signals=sig_text or "-")