import os
import json
import urllib.request
import urllib.error
import uuid
from flask import Flask, request, jsonify
from google import genai

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_OPERATOR_CHAT_ID = os.environ.get("TELEGRAM_OPERATOR_CHAT_ID")

# Operator javoblarini sayt mijoziga bog'lash uchun vaqtinchalik xotira.
# Productionda Redis/Postgres ishlatish yaxshiroq.
OPERATOR_CLIENT_MESSAGES = {}
TELEGRAM_MESSAGE_CLIENTS = {}


DLKIP_CONTEXT = """
Вы — официальный бот-оператор компании DLKIP Electronics.

DLKIP Electronics работает в области промышленной автоматизации,
КИПиА, датчиков, реле, контроллеров, источников питания,
электронных и электротехнических устройств.

Основные направления:
- промышленная автоматизация
- КИПиА
- датчики
- реле и защитные устройства
- контроллеры
- источники питания
- электронное и электротехническое оборудование

MPR-62 — реле комплексной защиты трехфазных электродвигателей.

Известные характеристики:
- 3×380/400 В
- 0.5–999 А
- PT100
- RS-485 Modbus RTU
- OLED-дисплей
- релейные выходы

Контакты:
Заместитель директора — Ислам Нигматов
Телефон: +998 90 000 37 79

Руководитель отдела продаж — Шавкат Халиков
Телефон: +998 92 001 33 82
E-mail: dlkipworker03@gmail.com

Разработка дизайна чат-бота — Solihov Muhammadali
Телефон: +998 94 072 80 98

Разработка дизайна сайта — Solihov Muhammadali
Телефон: +998 94 072 80 98

Telegram-бот: @DlkipElectronics_bot
Telegram оператора: @Islam_Nigmatov
Telegram компании: @dlmanokip
Instagram: dlkip_electronics
YouTube: DLKIP
Сайт: dlkip.uz

Правила:
- Не придумывайте цены, наличие или технические характеристики.
- Если точной информации нет — сообщите об этом.
- Для коммерческих предложений, точной цены и наличия рекомендуйте связаться с отделом продаж.
- Если клиент просит человека — рекомендуйте оператора.
- Отвечайте на русском языке, кратко и профессионально.
"""

PLATFORM_LINKS = [
    (1, "Glotr.uz", "https://glotr.uz/rele-kompleksnoy-zashiti-trexfaznix-elektrodvigateley-mpr-62-kontrol-napryajeniya-toka-temperaturi-dlkip-electronics-p-1158338/", "https://glotr.uz/blok-zashiti-impulsnix-perenapryajeniy-3pn-400-v-na-din-reyku-zashita-promishlennogo-oborudovaniya-dlkip-electronics-p-1158240/", "https://glotr.uz/blok-zashiti-ot-impulsnix-perenapryazheniy-3380-v-na-din-reyku-zashita-promishlennoy-avtomatiki-dlkip-electronics-p-1158236/"),
    (2, "Prom.uz", "https://www.prom.uz/ads/rele-kompleksnoi-zashhity-trexfaznyx-elektrodvigatelei-mpr-62-kontrol-napryazheniya-toka-temperatury-dlkip-electronics/", "https://www.prom.uz/ads/blok-zashhity-impulsnyx-perenapryazenii-3pn-400-v-na-din-reiku-zashhita-promyslennogo-oborudovaniya-dlkip-electronics/", "https://www.prom.uz/ads/blok-zashhity-ot-impulsnyx-perenapryazenii-3380-v-na-din-reiku-zashhita-promyslennoi-avtomatiki-dlkip-electronics/"),
    (3, "Leoboard.ru", "https://leboard.ru/uz/tashkent/vse_dlya_biznesa/oborudovanie_dlya_biznesa/rele_kompleksnoy_zaschity_trehfaznyh_elektrodvigateley_mpr_62_6177747", "https://leboard.ru/uz/tashkent/elektronika/drugoe/blok_zaschity_impulsnyh_perenapryazheniy_3p_n_400_v_6177986", "https://leboard.ru/uz/tashkent/elektronika/drugoe/blok_zaschity_ot_impulsnyh_perenapryazheniy_3_380_v_6177995"),
    (4, "OLX.uz", "https://www.olx.uz/list/user/AvxpD/", "https://www.olx.uz/list/user/AvxpD/", "https://www.olx.uz/list/user/AvxpD/"),
    (5, "Adbox.uz", "https://adbox.uz/home-garden/riemont-i-stroitiel-stvo/instrumienty/prodam-rielie-komplieksnoi-zashchity-triekhfaznykh-eliektrodvighatieliei-mpr-62-208111.html", "https://adbox.uz/services/tradesmen-construction/electricians/blok-zashchity-impul-snykh-pierienapriazhienii-3p-n-400-v-200457.html", "https://adbox.uz/home-garden/riemont-i-stroitiel-stvo/instrumienty/prodam-blok-zashchity-3x380-v-na-din-rieiku-dlkip-208114.html"),
    (6, "Cenotavr.uz", "https://www.cenotavr.uz/tashkent/rele-kompleksnoi-zashshity-trehfaznyh-elektrodvigatelei-mpr-62-tashkent-14136", "https://www.cenotavr.uz/tashkent/blok-zashshity-impulsnyh-perenapryajenii-3p-n-400-v-tashkent-14137", "https://birbir.uz/ru/tashkent/cat/stroyka-i-remont/tovary-dlya-stroitelstva-remonta/elektrika/o/blok-zashchity-3-380-v-na-din-reyku-dlkip-287794797"),
    (7, "BirBir.uz", "https://birbir.uz/ru/tashkent/cat/stroyka-i-remont/tovary-dlya-stroitelstva-remonta/elektrika/o/rele-zashchity-dvigatelya-mpr-62-380v-dlkip-287791311", "https://birbir.uz/ru/tashkent/cat/stroyka-i-remont/instrumenty/elektroinstrument/o/blok-zashchity-3p-n-400-v-na-din-reyku-dlkip-287794060", "https://birbir.uz/ru/profile/157244e7-3c9f-4ef0-9fa1-8c8e9c87bf33"),
    (8, "Golden Pages", "https://www.goldenpages.uz/company/?Id=121676", "https://www.goldenpages.uz/company/?Id=121676", "https://www.goldenpages.uz/company/?Id=121676"),
    (9, "Elbozor.uz", "https://www.elbozor.uz/item/rele-kompleksnoy-zashchity-trehfaznyh-elektrodvigateley-mpr-62-25a0400b5b4ef7081d8fa122802c205e", "https://www.elbozor.uz/item/blok-zashchity-impulsnyh-perenapryazheniy-3p-n-400-v-7f4fefea54867830ccb2d6b82cd0aaaa", "https://www.elbozor.uz/item/blok-zashchity-ot-impulsnyh-perenapryazheniy-3-380-05a8715c9b0ec9522641bc6a7f7e16d2"),
    (10, "Megaprom.uz", "https://megaprom.uz/obyavleniye/rele-zashhity-dvigatelya-mpr-62-380v-dlkip/", "https://megaprom.uz/obyavleniye/blok-zashhity-3p-n-400-v-na-din-rejku-dlkip/", "https://megaprom.uz/obyavleniye/blok-zashhity-3x380-v-na-din-rejku-dlkip/"),
    (11, "Tashkent.Salexy.uz", "https://tashkent.salexy.uz/c/rele_zaschity_dvigatelya_mpr_62_534050.html", "https://tashkent.salexy.uz/c/uzip_3pn_380v_zaschita_534049.html", "https://tashkent.salexy.uz/c/uzip_3380_v_dlkip_534051.html"),
    (12, "Selxoz.uz", "https://selxoz.uz/resurslar/turli-xil2/rele-zashhity-jelektrodvigatelja-mpr-62-dlkip-electronics_i71", "https://selxoz.uz/resurslar/turli-xil2/blok-zashhity-impulsnyh-perenaprjazhenij-3pn-400-v-dlkip-electronics_i72", "https://selxoz.uz/resurslar/turli-xil2/blok-zashhity-impulsnyh-perenaprjazhenij-3380-v-dlkip-electronics_i73"),
    (13, "Tovar.uz", "https://tovar.uz/product/131343", "https://tovar.uz/product/131345", "https://tovar.uz/product/131346"),
    (14, "Karvon.uz", "https://karvon24.uz/ru/ad/rele-kompleksnoy-zaschity-trehfaznyh-elektrodvigateley-mpr-62--ad_1787565710800/", "https://karvon24.uz/ru/ad/blok-zaschity-impulsnyh-perenapryazheniy-3p-n-400-v--ad_1787565957562/", "https://karvon24.uz/ru/ad/blok-zaschity-ot-impulsnyh-perenapryazheniy-3-380-v--ad_1787566221080/"),
    (15, "Tashkent.Unibo.su", "https://tashkent.unibo.su/m37943194/rele-kompleksnoy-zaschiti-trehfaznih-elektrodvigateley-mpr-62.htm", "https://tashkent.unibo.su/m37943202/blok-zaschiti-impulsnih-perenapryazheniy-3pn-400-v.htm", "https://tashkent.unibo.su/m37943209/blok-zaschiti-ot-impulsnih-perenapryazheniy-3380-v.htm"),
    (16, "Topserver.ru", "https://topserver.ru/buildingoods/electroproducts/427.html", "https://topserver.ru/buildingoods/electroproducts/428.html", "https://topserver.ru/buildingoods/electroproducts/429.html"),
    (17, "Узбекистан Бесплатные Объявления", "https://xn--80abmghlx4ajd.xn--80abbembcyvesfij3at4loa4ff.xn--p1ai/rele-kompleksnoj-zashhity-trehfaznyh-elektrodvigatelej-mpr-62-2694655", "https://xn--80abmghlx4ajd.xn--80abbembcyvesfij3at4loa4ff.xn--p1ai/blok-zashhity-impulsnyh-perenapryazhenij-3p-n-400-v-2694643", "https://xn--80abmghlx4ajd.xn--80abbmghlx4ajd.xn--80ababbcyvesfij3at4ff.xn--p1ai/blok-zashhity-ot-impulsnyh-perenapryazhenij-3-380-v-2694656"),
    (18, "2GIS.uz", "https://2gis.uz/tashkent/search/Dlkip%20Electronics%2C%20%D0%BF%D1%80%D0%BE%D0%B8%D0%B7%D0%B2%D0%BE%D0%B4%D1%81%D1%82%D0%B2%D0%B5%D0%BD%D0%BD%D0%B0%D1%8F%20%D0%BA%D0%BE%D0%BC%D0%BF%D0%B0%D0%BD%D0%B8%D1%8F/firm/70000001116423561/69.374881%2C41.246852", None, None),
    (19, "Tashkent.Boplus.uz", "https://tashkent.boplus.uz/biznes-i-promyshlennost/sotrudnichestvo-i-partnerstvo/34575.html", "https://tashkent.boplus.uz/biznes-i-promyshlennost/prochee-oborudovanie-i-syryo/prodazha/34573.html", "https://tashkent.boplus.uz/biznes-i-promyshlennost/sotrudnichestvo-i-partnerstvo/34576.html"),
    (20, "Egasi.uz", "https://www.egasi.uz/energy-power/rele-kompleksnoy-zashchity-trehfaznyh-elektrodvigateley-mpr--p-83a29108", "https://www.egasi.uz/other/blok-zashchity-impulsnyh-perenapryazheniy-3pn-400-v-p-83a3423d", "https://www.egasi.uz/other/blok-zashchity-ot-impulsnyh-perenapryazheniy-3380-v-p-83a36637"),
    (21, "Sprav.uz", "https://sprav.uz/company/26827-dlkip-electronics", "https://sprav.uz/company/26827-dlkip-electronics", "https://sprav.uz/company/26827-dlkip-electronics"),
    (22, "PC.uz", "https://pc.uz/company/127128-dlkip-electronics", "https://pc.uz/company/127128-dlkip-electronics", "https://pc.uz/company/127128-dlkip-electronics"),
    (23, "Stroyvitrina.uz", "https://stroyvitrina.uz/company/6903-dlkip-electronics", "https://stroyvitrina.uz/company/6903-dlkip-electronics", "https://stroyvitrina.uz/company/6903-dlkip-electronics"),
    (24, "Tashkent.Freeads.uz", "http://tashkent.freeads.uz/ru-i-offer-i-id-i-3233789-i-rele-kompleksnoj-zashchity-trehfaznyh-elektrodvigatelej-mpr-62-dlkip-electronics.html", "http://tashkent.freeads.uz/ru-i-offer-i-id-i-3233791-i-blok-zashchity-impulisnyh-perenaprjazhenij-3pn-400-v-dlkip-electronics.html", "http://tashkent.freeads.uz/ru-i-offer-i-id-i-3233792-i-blok-zashchity-ot-impulisnyh-perenaprjazhenij-3%C3%97380-v-dlkip-electronics.html"),
    (25, "Tataxon.uz", "https://tataxon.uz/tashkent/meropriyatiya-pod-klyuch-drugoe/rele-kompleksnoj-zashity-trehfaznyh-elektrodvigateley-mpr-62-1388", "https://tataxon.uz/tashkent/meropriyatiya-pod-klyuch-drugoe/blok-zashity-impulsnyh-perenapryazhenij-3p-n-400-v-1387", "https://tataxon.uz/tashkent/meropriyatiya-pod-klyuch-drugoe/blok-zashity-ot-impulsnyh-perenapryazhenij-3-380-v-1389"),
    (26, "Tanlash.uz", "https://dlkipelectronics1.range.uz/p/1300648-rele-kompleksnoy-zashchity-trehfaznyh-elektrodvigateley-mpr-62/", "https://dlkipelectronics1.range.uz/p/1300653-blok-zashchity-impulsnyh-perenapryazheniy-3p-n-400-v/", "https://dlkipelectronics1.range.uz/p/1300655-blok-zashchity-ot-impulsnyh-perenapryazheniy-3380-v/"),
    (27, "Agroshop.site", "https://agroshop.site/card/5331/", "https://agroshop.site/card/5332/", None),
]

def platform_cards():
    html = []
    for _, name, mpr, bp, bzip in PLATFORM_LINKS:
        links = []
        if mpr:
            links.append(f'<a href="{mpr}" target="_blank" rel="noopener">MPR-62</a>')
        if bp:
            links.append(f'<a href="{bp}" target="_blank" rel="noopener">БП</a>')
        if bzip:
            links.append(f'<a href="{bzip}" target="_blank" rel="noopener">БЗИП</a>')
        html.append(f"""
            <article class="platform-card">
                <div class="platform-name">{name}</div>
                <div class="platform-links">{"".join(links)}</div>
            </article>
        """)
    return "".join(html)

PLATFORM_CARDS = platform_cards()


@app.route("/sitemap.xml")
def sitemap():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://dlkip-electronics.onrender.com/</loc>
        <changefreq>weekly</changefreq>
        <priority>1.0</priority>
    </url>
</urlset>"""
    return app.response_class(xml, mimetype="application/xml")


@app.route("/robots.txt")
def robots():
    text = """User-agent: *
Allow: /

Sitemap: https://dlkip-electronics.onrender.com/sitemap.xml
"""
    return app.response_class(text, mimetype="text/plain")


@app.route("/")
def home():
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<meta name="google-site-verification" content="aOzrJYJ1BQFWghMazPJjYVoRknQlbDNuodHy75cqCUE" />

<title>DLKIP Electronics — промышленная автоматизация, КИПиА и электроника</title>

<meta name="description" content="DLKIP Electronics — промышленная электроника, автоматизация, КИПиА, датчики, реле, контроллеры, источники питания и технические консультации в Узбекистане.">

<link rel="canonical" href="https://dlkip-electronics.onrender.com/">

<meta property="og:title" content="DLKIP Electronics • DLKIPChatBot">
<meta property="og:description" content="Промышленная электроника, автоматизация, КИПиА, датчики, реле, контроллеры и технические консультации DLKIP Electronics.">
<meta property="og:url" content="https://dlkip-electronics.onrender.com/">
<meta property="og:type" content="website">

<style>
:root {{
    --bg:#050505; --panel:#0d0d0d; --line:#282828;
    --orange:#ff4d00; --orange2:#ff7a35; --text:#f5f5f5;
}}
* {{ box-sizing:border-box; margin:0; padding:0; }}
html {{ scroll-behavior:smooth; }}
body {{
    min-height:100vh; font-family:Arial,Helvetica,sans-serif; color:var(--text);
    background:
        radial-gradient(circle at 50% -8%,rgba(255,75,0,.20),transparent 34%),
        radial-gradient(circle at 100% 100%,rgba(255,40,0,.08),transparent 28%),
        var(--bg);
    padding:18px;
    position:relative;
}}
body:before {{
    content:""; position:fixed; inset:0; pointer-events:none; opacity:.10;
    background-image:
        linear-gradient(rgba(255,255,255,.022) 1px,transparent 1px),
        linear-gradient(90deg,rgba(255,255,255,.022) 1px,transparent 1px);
    background-size:38px 38px;
}}
.app {{ max-width:1280px; margin:auto; position:relative; z-index:1; }}
.topbar {{ display:flex; justify-content:space-between; align-items:center; gap:10px; margin-bottom:10px; }}
.topbrand {{ display:flex; align-items:center; gap:8px; }}
.mini-dot {{ width:10px; height:10px; border-radius:50%; background:var(--orange); box-shadow:0 0 12px var(--orange); }}
.topbrand span:last-child {{ font-size:15px; font-weight:900; letter-spacing:1.5px; }}
.top-actions {{ display:flex; gap:7px; flex-wrap:wrap; justify-content:flex-end; }}
.top-actions a {{
    color:#ddd; text-decoration:none; border:1px solid var(--line); background:#0c0c0c;
    padding:9px 12px; border-radius:9px; font-size:12px; font-weight:800;
}}
.top-actions a:hover {{ border-color:rgba(255,77,0,.6); color:var(--orange2); }}
.hero {{ display:grid; grid-template-columns:190px 1fr 230px; gap:14px; align-items:center; margin-bottom:12px; }}
.logo-box {{
    height:145px; border:1px solid rgba(255,77,0,.45); border-radius:18px;
    background:linear-gradient(145deg,#131313,#070707); display:flex; align-items:center;
    justify-content:center; padding:10px; overflow:hidden; box-shadow:0 0 24px rgba(255,60,0,.08);
}}
.logo-box img {{ max-width:100%; max-height:122px; object-fit:contain; }}
.hero-center {{ text-align:center; }}
.hero-center h1 {{ font-size:56px; line-height:1; font-weight:950; letter-spacing:2px; color:#fff; }}
.hero-center h1 span {{ color:var(--orange); }}
.hero-center p {{ margin-top:9px; color:#a5a5a5; font-size:16px; }}
.hero-tag {{
    display:inline-block; margin-top:9px; padding:8px 12px; border:1px solid rgba(255,77,0,.30);
    border-radius:99px; color:var(--orange2); font-size:11px; font-weight:900; letter-spacing:.7px;
}}
.quick {{ border:1px solid var(--line); background:linear-gradient(145deg,#121212,#080808); border-radius:18px; padding:14px; }}
.quick-title {{ font-size:11px; letter-spacing:.9px; color:var(--orange2); font-weight:900; }}
.quick a {{ display:block; margin-top:8px; color:#eee; text-decoration:none; font-size:13px; font-weight:800; line-height:1.35; word-break:break-word; }}
.quick a:hover {{ color:var(--orange2); }}
.banner {{
    width:100%; border:1px solid rgba(255,77,0,.32); border-radius:18px; background:#090909;
    overflow:hidden; margin-bottom:14px; box-shadow:0 0 28px rgba(255,55,0,.06),inset 0 0 24px rgba(255,55,0,.03);
}}
.banner img {{ display:block; width:100%; height:auto; aspect-ratio:1983 / 793; object-fit:contain; background:#060606; }}
.banner-caption {{ padding:8px 10px; text-align:center; color:#666; font-size:9px; letter-spacing:.4px; }}

.center-videos {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; min-width:0; margin-bottom:14px; }}
.center-video {{
    overflow:hidden; border:1px solid rgba(255,77,0,.32); border-radius:18px; background:#090909;
    box-shadow:0 0 24px rgba(255,55,0,.06); min-width:0;
}}
.center-video video {{
    display:block; width:100%; aspect-ratio:16 / 9; height:auto; object-fit:cover; background:#050505;
}}
.gutter-video {{
    position:absolute;
    top:110px;
    width:225px;
    height:3060px;
    overflow:hidden;
    border:1px solid rgba(255,77,0,.32);
    border-radius:18px;
    background:#090909;
    box-shadow:0 0 24px rgba(255,55,0,.08);
    z-index:2;
}}

.gutter-video.left {{
    left:calc(50% - 900px);
}}

.gutter-video.right {{
    right:calc(50% - 900px);
}}

.gutter-video video {{
    display:block;
    width:100%;
    height:100%;
    object-fit:cover;
    background:#050505;
}}
.main {{ display:grid; grid-template-columns:minmax(0,1.58fr) minmax(300px,.82fr); gap:14px; }}
.card {{ background:linear-gradient(180deg,#151515,#080808); border:1px solid var(--line); border-radius:18px; box-shadow:0 0 22px rgba(255,60,0,.045); }}
.chat {{ overflow:hidden; border-color:rgba(255,77,0,.48); }}
.chat-head {{ min-height:88px; padding:16px 20px; display:flex; align-items:center; justify-content:space-between; background:linear-gradient(90deg,#090909,#161616,#090909); border-bottom:1px solid rgba(255,77,0,.20); }}
.bot-info {{ display:flex; align-items:center; gap:13px; }}
.bot-avatar {{ width:32px; height:32px; border-radius:7px; display:flex; align-items:center; justify-content:center; background:linear-gradient(135deg,#ff6200,#e62d00); font-size:17px; box-shadow:0 0 16px rgba(255,70,0,.2); overflow:hidden; flex:0 0 32px; }}
.bot-avatar img {{ width:100%; height:100%; object-fit:cover; display:block; border-radius:7px; }}
.bot-name {{ font-size:21px; font-weight:900; }}
.online {{ display:flex; align-items:center; gap:5px; margin-top:5px; color:#999; font-size:13px; }}
.dot {{ width:9px; height:9px; border-radius:50%; background:var(--orange); box-shadow:0 0 8px rgba(255,75,0,.9); animation:pulse 1.8s infinite; }}
@keyframes pulse {{ 50% {{ opacity:.3; }} }}
.badge {{ padding:8px 12px; border-radius:99px; border:1px solid rgba(255,80,0,.32); color:var(--orange2); font-size:11px; font-weight:900; }}
#messages {{ height:470px; overflow-y:auto; padding:20px; background:radial-gradient(circle at 50% 0,rgba(255,70,0,.035),transparent 34%); }}
#messages::-webkit-scrollbar {{ width:6px; }}
#messages::-webkit-scrollbar-track {{ background:#090909; }}
#messages::-webkit-scrollbar-thumb {{ background:#35170b; border-radius:8px; }}
.message-row {{ display:flex; margin-bottom:12px; }}
.bot-row {{ justify-content:flex-start; }}
.user-row {{ justify-content:flex-end; }}
.message {{
    max-width:85%; padding:2px 0; margin:0; background:transparent !important; border:0 !important;
    border-radius:0 !important; box-shadow:none !important; line-height:1.45; white-space:pre-wrap;
    font-size:14px; color:#eee; word-wrap:break-word;
}}
.bot-message,.user-message {{ background:transparent !important; border:0 !important; border-radius:0 !important; box-shadow:none !important; }}
.user-message {{ color:#fff !important; }}
.label {{ margin-bottom:3px; font-size:10px; font-weight:900; opacity:.6; }}
.typing {{ display:flex; gap:4px; align-items:center; height:14px; }}
.typing span {{ width:5px; height:5px; border-radius:50%; background:var(--orange); animation:typing 1.1s infinite; }}
.typing span:nth-child(2) {{ animation-delay:.15s; }}
.typing span:nth-child(3) {{ animation-delay:.3s; }}
@keyframes typing {{ 30% {{ opacity:1; transform:translateY(-2px); }} 0%,60%,100% {{ opacity:.22; }} }}
.input-area {{ display:flex; gap:8px; padding:10px; background:#080808; border-top:1px solid #222; }}
.input-wrap {{ flex:1; border:1px solid #2a2a2a; background:#111; border-radius:10px; padding:0 10px; }}
.input-wrap:focus-within {{ border-color:var(--orange); box-shadow:0 0 0 3px rgba(255,70,0,.05); }}
#text {{ width:100%; height:38px; border:0; outline:0; background:transparent; color:#fff; font-size:15px; }}
#text::placeholder {{ color:#646464; }}
.send {{ min-width:118px; height:38px; border:0; border-radius:10px; background:linear-gradient(135deg,#ff6200,#ed3200); color:#fff; font-size:12px; font-weight:900; cursor:pointer; }}
.send:hover {{ box-shadow:0 7px 17px rgba(255,65,0,.19); transform:translateY(-1px); }}
.side {{ display:flex; flex-direction:column; gap:12px; }}
.panel {{ padding:17px; }}
.panel h2 {{ font-size:20px; margin-bottom:9px; }}
.panel p {{ font-size:14px; line-height:1.55; color:#a8a8a8; }}
.contact {{ margin-top:8px; padding:12px; border:1px solid #292929; border-radius:10px; background:#0e0e0e; overflow:hidden; }}
.role {{ font-size:14px; font-weight:900; color:var(--orange2); margin-bottom:3px; }}
.name {{ font-size:15px; font-weight:900; line-height:1.3; }}
.link {{ display:block; margin-top:3px; color:#ddd; text-decoration:none; font-size:13px; font-weight:700; line-height:1.4; overflow-wrap:anywhere; word-break:break-word; }}
.link:hover {{ color:var(--orange2); }}
.social-panel {{ padding:12px; }}

.socials {{
    display:grid;
    grid-template-columns:repeat(2, minmax(0, 1fr));
    gap:8px;
    width:100%;
    margin:0;
}}

.social {{
    min-width:0;
    min-height:40px;
    width:100%;
    padding:0 10px;
    display:flex;
    align-items:center;
    justify-content:center;
    gap:7px;
    border:1px solid #282828;
    border-radius:8px;
    background:#0f0f0f;
    color:#fff;
    text-decoration:none;
    font-size:12px;
    font-weight:800;
    text-align:center;
}}

.social:hover {{
    border-color:rgba(255,77,0,.58);
    color:var(--orange2);
}}

.social img {{
    width:22px;
    height:22px;
    object-fit:contain;
    flex:0 0 22px;
    margin:0;
}}

.socials > .social:last-child {{
    grid-column:1 / -1;
}}

.products {{ display:grid; grid-template-columns:repeat(3,1fr); gap:7px; }}
.product {{ padding:12px; border:1px solid #292929; border-radius:10px; background:#0e0e0e; }}
.product h3 {{ font-size:14px; margin-bottom:5px; }}
.product p {{ font-size:12px; color:#888; line-height:1.4; }}
.product a {{ display:inline-block; margin-top:7px; padding:5px 7px; border-radius:7px; text-decoration:none; color:var(--orange2); border:1px solid rgba(255,75,0,.27); font-size:10px; font-weight:900; }}
.platforms {{ margin-top:14px; padding:18px; }}
.section-head {{ display:flex; justify-content:space-between; align-items:end; gap:10px; margin-bottom:10px; }}
.section-head h2 {{ font-size:22px; }}
.section-head p {{ font-size:11px; color:#777; }}
.map-links {{ display:grid; grid-template-columns:repeat(5,1fr); gap:9px; }}
.map-links a {{ min-height:46px; display:flex; align-items:center; justify-content:center; text-decoration:none; border:1px solid #292929; background:#101010; border-radius:9px; color:#fff; font-size:13px; font-weight:800; text-align:center; padding:7px; }}
.map-links a:hover {{ border-color:rgba(255,77,0,.55); color:var(--orange2); }}
details {{ margin-top:11px; }}
details summary {{ cursor:pointer; color:var(--orange2); font-size:15px; font-weight:900; list-style:none; padding:13px 15px; border:1px solid rgba(255,77,0,.30); border-radius:10px; background:#111; text-align:center; transition:.2s; }}
details summary:hover {{ background:#181818; border-color:rgba(255,77,0,.65); box-shadow:0 0 16px rgba(255,70,0,.08); }}
.platform-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-top:11px; }}
.platform-card {{ min-height:108px; padding:12px; border:1px solid #252525; background:#0d0d0d; border-radius:10px; display:flex; flex-direction:column; justify-content:space-between; }}
.platform-card:hover {{ border-color:rgba(255,77,0,.38); }}
.platform-name {{ font-size:14px; font-weight:900; line-height:1.25; margin-bottom:9px; color:#fff; overflow-wrap:anywhere; }}
.platform-links {{ display:flex; flex-wrap:wrap; gap:6px; }}
.platform-links a {{ display:flex; align-items:center; justify-content:center; min-height:32px; padding:5px 9px; border-radius:7px; background:#151515; border:1px solid rgba(255,75,0,.27); color:var(--orange2); text-decoration:none; font-size:12px; font-weight:900; white-space:nowrap; }}
.platform-links a:hover {{ background:rgba(255,70,0,.10); border-color:var(--orange); }}
.operator {{ position:fixed; right:18px; bottom:18px; z-index:80; height:56px; padding:0 18px; border-radius:28px; border:1px solid rgba(255,80,0,.55); background:linear-gradient(135deg,#161616,#080808); color:#fff; font-size:13px; font-weight:900; display:flex; align-items:center; gap:7px; cursor:pointer; box-shadow:0 7px 22px rgba(0,0,0,.42); }}
.operator:hover {{ border-color:var(--orange); box-shadow:0 0 19px rgba(255,65,0,.15); }}
#operator-window {{ display:none; position:fixed; right:18px; bottom:84px; width:340px; z-index:90; background:#101010; border:1px solid rgba(255,77,0,.48); border-radius:16px; box-shadow:0 18px 50px rgba(0,0,0,.55),0 0 25px rgba(255,65,0,.08); overflow:hidden; }}
.operator-window-head {{ display:flex; align-items:center; justify-content:space-between; padding:14px 16px; background:linear-gradient(90deg,#0b0b0b,#171717); border-bottom:1px solid rgba(255,77,0,.20); }}
.operator-window-title {{ font-size:17px; font-weight:900; }}
.operator-close {{ border:0; background:transparent; color:#aaa; font-size:20px; cursor:pointer; }}
.operator-close:hover {{ color:#fff; }}
.operator-window-body {{ padding:16px; }}
.operator-window-body p {{ color:#bdbdbd; font-size:14px; line-height:1.55; margin-bottom:12px; }}
.operator-telegram {{ display:flex; align-items:center; justify-content:center; width:100%; min-height:46px; padding:10px 12px; border-radius:10px; background:linear-gradient(135deg,#ff6200,#ea3000); color:#fff; text-decoration:none; font-size:12px; font-weight:900; text-align:center; }}
.operator-telegram:hover {{ box-shadow:0 8px 20px rgba(255,65,0,.18); }}
.footer {{ text-align:center; color:#4d4d4d; font-size:16px; padding:14px 4px 3px; }}
@media(max-width:1000px) {{
    .hero {{ grid-template-columns:160px 1fr; }}
    .quick {{ grid-column:1 / -1; }}
    .main {{ grid-template-columns:1fr; }}
    .platform-grid {{ grid-template-columns:repeat(3,1fr); }}
    .map-links {{ grid-template-columns:repeat(3,1fr); }}
}}
@media(max-width:1100px) {{
    body {{ padding:8px; }}
    .topbar {{ align-items:flex-start; }}
    .top-actions a {{ font-size:10px; padding:7px 8px; }}
    .hero {{ grid-template-columns:1fr; }}
    .logo-box {{ height:125px; }}
    .hero-center h1 {{ font-size:35px; }}
    .center-videos {{ grid-template-columns:1fr 1fr; }}
    .hero-center p {{ font-size:14px; }}
    .gutter-video {{ display:none; }}
    .platform-grid {{ grid-template-columns:repeat(2,1fr); }}
    .map-links {{ grid-template-columns:1fr 1fr; }}
    .products {{ grid-template-columns:1fr; }}
    .message {{ max-width:90%; font-size:14px; }}
    .input-area {{ flex-direction:column; }}
    .send {{ width:100%; }}
    #operator-window {{ left:10px; right:10px; bottom:76px; width:auto; }}
}}
@media(max-width:450px) {{
    .platform-grid {{ grid-template-columns:1fr; }}
    .topbrand span:last-child {{ font-size:12px; }}
    .hero-center h1 {{ font-size:30px; }}
    .bot-name {{ font-size:18px; }}
    .badge {{ display:none; }}
}}
.top-actions a img {{
    width:22px;
    height:22px;
    object-fit:contain;
    vertical-align:middle;
}}

.products-title {{
    display:flex;
    align-items:center;
    gap:8px;
}}

.products-title img {{
    width:32px;
    height:32px;
    object-fit:contain;
    flex:0 0 32px;
}}
.company-title {{
    display:flex;
    align-items:center;
    gap:9px;
}}

.company-title img {{
    width:38px;
    height:38px;
    object-fit:contain;
    border-radius:7px;
    flex:0 0 38px;
}}

.contacts-title {{
    display:flex;
    align-items:center;
    gap:9px;
}}

.contacts-title img {{
    width:32px;
    height:32px;
    object-fit:contain;
    flex:0 0 32px;
}}

.contact .link {{
    display:flex;
    align-items:center;
    gap:7px;
}}

.contact .link img {{
    width:22px;
    height:22px;
    object-fit:contain;
    flex:0 0 22px;
}}
.welcome-title {{
    display:flex;
    align-items:center;
    gap:8px;
}}

.welcome-title img {{
    width:30px;
    height:30px;
    object-fit:contain;
    flex:0 0 30px;
}}
.platforms-title {{
    display:flex;
    align-items:center;
    gap:9px;
}}

.platforms-title img {{
    width:32px;
    height:32px;
    object-fit:contain;
    flex:0 0 32px;
}}
.operator img {{
    width:30px;
    height:30px;
    object-fit:contain;
    flex:0 0 30px;
}}

.operator {{
    display:flex;
    align-items:center;
    gap:8px;
}}

.operator-window-title {{
    display:flex;
    align-items:center;
    gap:8px;
}}

.operator-window-title img {{
    width:30px;
    height:30px;
    object-fit:contain;
    flex:0 0 30px;
}}
#operator-window {{
    width:420px;
    max-width:calc(100vw - 36px);
}}

/* OPERATOR CHAT */
#operator-messages {{ min-height:180px; max-height:300px; overflow-y:auto; margin-bottom:12px; padding:10px; background:#080808; border:1px solid #292929; border-radius:10px; }}
.operator-message {{ color:#eee; font-size:13px; line-height:1.5; margin-bottom:8px; padding:8px 10px; border-radius:9px; background:#121212; }}
.operator-message.user {{ border-left:2px solid var(--orange); }}
.operator-message.operator-reply {{ border-left:2px solid #777; }}
.operator-input-area {{ display:flex; gap:7px; margin-bottom:10px; }}
#operator-text {{ flex:1; min-width:0; height:40px; padding:0 10px; border:1px solid #303030; border-radius:9px; outline:none; background:#0b0b0b; color:#fff; font-size:13px; }}
#operator-text:focus {{ border-color:var(--orange); }}
.operator-input-area button {{ height:40px; padding:0 12px; border:0; border-radius:9px; background:linear-gradient(135deg,#ff6200,#ed3200); color:#fff; font-size:11px; font-weight:900; cursor:pointer; }}

</style>
</head>
<body>
<div class="gutter-video left">
    <video src="/static/vertical.mp4" autoplay muted loop playsinline preload="metadata"></video>
</div>
<div class="gutter-video right">
    <video src="/static/vertical.mp4" autoplay muted loop playsinline preload="metadata"></video>
</div>
<div class="app">

<div class="topbar">
    <div class="topbrand"><span class="mini-dot"></span><span>DLKIP ELECTRONICS</span></div>
    <div class="top-actions">
       <a href="https://t.me/DlkipElectronics_bot" target="_blank" rel="noopener">
    <img src="/static/bot.jpg" alt="Bot"> Bot
</a>

<a href="https://t.me/dlmanokip" target="_blank" rel="noopener">
    <img src="/static/telegram.png" alt="Telegram"> Telegram
</a>

<a href="https://www.instagram.com/dlkip_electronics/" target="_blank" rel="noopener">
    <img src="/static/instagram.png" alt="Instagram"> Instagram
</a>

<a href="https://www.youtube.com/@DLKIP/videos" target="_blank" rel="noopener">
    <img src="/static/youtube.png" alt="YouTube"> YouTube
</a>

<a href="https://dlkip.uz" target="_blank" rel="noopener">
    <img src="/static/website.png" alt="DLKIP.UZ"> DLKIP.UZ
</a>
    </div>
</div>

<section class="hero">
    <div class="logo-box"><img src="/static/logo.png" alt="DLKIP Electronics"></div>
    <div class="hero-center">
        <h1>DLKIP<span>ChatBot</span></h1>
        <p>Интеллектуальный цифровой помощник DLKIP Electronics</p>
        <div class="hero-tag">ПРОМЫШЛЕННАЯ АВТОМАТИКА • КИПиА • ЭЛЕКТРОНИКА</div>
    </div>
    <div class="quick">
        <div class="quick-title">БЫСТРАЯ СВЯЗЬ</div>
        <a href="tel:+998900003779">+998 90 000 37 79</a>
        <a href="tel:+998920013382">+998 92 001 33 82</a>
        <a href="mailto:dlkipworker03@gmail.com">dlkipworker03@gmail.com</a>
    </div>
</section>

<section class="banner">
    <img src="/static/shablon.jpg" alt="DLKIP Electronics">
</section>

<section class="center-videos">
    <div class="center-video">
        <video id="black-video" src="/static/black.mp4" muted playsinline preload="auto"></video>
    </div>
    <div class="center-video">
        <video id="orange-video" src="/static/orange.mp4" muted playsinline preload="auto"></video>
    </div>
</section>

<section class="main">
<div class="card chat">
    <div class="chat-head">
        <div class="bot-info">
            <div class="bot-avatar">
                <img src="/static/bot.jpg" alt="DLKIP Bot">
            </div>
            <div>
                <div class="bot-name">DLKIP Operator Bot</div>
                <div class="online"><span class="dot"></span>Онлайн • Оператор помощник</div>
            </div>
        </div>
        <div class="badge">AI-ПЛАТФОРМА</div>
    </div>

  <div id="messages">
    <div class="message-row bot-row">
        <div class="message bot-message">

            <div class="label">DLKIP Operator Bot</div>

            <div class="welcome-title">
                <img src="/static/bot2.png" alt="DLKIP Operator Bot">
                <span>Добро пожаловать в DLKIP Electronics!</span>
            </div>

            <br>

            Я — оператор-бот консультант DLKIP Electronics.<br><br>

            Помогу вам:<br>
            • подобрать оборудование под вашу задачу;<br>
            • получить техническую информацию о продукции;<br>
            • разобраться в характеристиках и возможностях оборудования;<br>
            • найти решения в области промышленной автоматизации и КИПиА.<br><br>

            Опишите вашу задачу или задайте вопрос — я постараюсь предложить подходящее решение.<br><br>

            DLKIP Electronics — технологии для надежной автоматизации.

        </div>
    </div>
</div>

<div class="input-area">
    <div class="input-wrap">
        <input
            id="text"
            type="text"
            autocomplete="off"
            placeholder="Введите вопрос о продукции или услугах..."
            onkeydown="if(event.key==='Enter')sendMessage()"
        >
    </div>

    <button class="send" onclick="sendMessage()">ОТПРАВИТЬ</button>
</div>
</div>

<aside class="side">

    <div class="card panel">
        <h2 class="company-title">
            <img src="/static/workshop.png" alt="DLKIP Electronics">
            DLKIP Electronics
        </h2>

        <p>
            Оборудование и решения для промышленной автоматизации,
            КИПиА, электроники и электротехнических систем.
        </p>
    </div>

    <div class="card panel">
        <h2 class="contacts-title">
            <img src="/static/mobil.png" alt="Контакты">
            Контакты
        </h2>

        <div class="contact">
            <div class="role">Заместитель директора</div>
            <div class="name">Ислам Нигматов</div>
            <a class="link" href="tel:+998900003779">
                <img src="/static/mobil.png" alt="Телефон">
                +998 90 000 37 79
            </a>
        </div>

        <div class="contact">
            <div class="role">Руководитель отдела продаж</div>
            <div class="name">Шавкат Халиков</div>
            <a class="link" href="tel:+998920013382">
                <img src="/static/mobil.png" alt="Телефон">
                +998 92 001 33 82
            </a>
        </div>

        <div class="contact">
            <div class="role">Дизайн чат-бота</div>
            <div class="name">Solihov Muhammadali</div>
            <a class="link" href="tel:+998940728098">
                <img src="/static/mobil.png" alt="Телефон">
                +998 94 072 80 98
            </a>
        </div>

        <div class="contact">
            <div class="role">Дизайн сайта</div>
            <div class="name">Solihov Muhammadali</div>
            <a class="link" href="tel:+998940728098">
                <img src="/static/mobil.png" alt="Телефон">
                +998 94 072 80 98
            </a>
        </div>
    </div>



<div class="card panel social-panel">
    <div class="socials">
        <a class="social" href="https://t.me/DlkipElectronics_bot" target="_blank" rel="noopener">
            <img src="/static/bot.jpg" alt="Bot"> Bot
        </a>

        <a class="social" href="https://t.me/dlmanokip" target="_blank" rel="noopener">
            <img src="/static/telegram.png" alt="Telegram"> Telegram
        </a>

        <a class="social" href="https://www.instagram.com/dlkip_electronics/" target="_blank" rel="noopener">
            <img src="/static/instagram.png" alt="Instagram"> Instagram
        </a>

        <a class="social" href="https://www.youtube.com/@DLKIP/videos" target="_blank" rel="noopener">
            <img src="/static/youtube.png" alt="YouTube"> YouTube
        </a>

        <a class="social" href="https://dlkip.uz" target="_blank" rel="noopener">
            <img src="/static/website.png" alt="DLKIP.UZ"> DLKIP.UZ
        </a>
    </div>
</div>


<div class="card panel">
    <h2 class="products-title">
        <img src="/static/product.png" alt="Продукция">
        Каталог продукции
    </h2>

    <div class="products">
        <div class="product">
            <h3>MPR-62</h3>
            <p>Реле комплексной защиты трехфазных электродвигателей.</p>
            <a href="https://glotr.uz/rele-kompleksnoy-zashiti-trexfaznix-elektrodvigateley-mpr-62-kontrol-napryajeniya-toka-temperaturi-dlkip-electronics-p-1158338/" target="_blank">ОТКРЫТЬ</a>
        </div>
        <div class="product">
            <h3>БП</h3>
            <p>Блок защиты импульсных перенапряжений 3P+N 400 В.</p>
            <a href="https://glotr.uz/blok-zashiti-impulsnix-perenapryajeniy-3pn-400-v-na-din-reyku-zashita-promishlennogo-oborudovaniya-dlkip-electronics-p-1158240/" target="_blank">ОТКРЫТЬ</a>
        </div>
        <div class="product">
            <h3>БЗИП</h3>
            <p>Блок защиты от импульсных перенапряжений 3×380 В.</p>
            <a href="https://glotr.uz/blok-zashiti-ot-impulsnix-perenapryazheniy-3380-v-na-din-reyku-zashita-promishlennoy-avtomatiki-dlkip-electronics-p-1158236/" target="_blank">ОТКРЫТЬ</a>
        </div>
    </div>
</div>
</aside>
</section>

<section class="card platforms">
    <div class="section-head">
        <div>
            <h2 class="platforms-title">
                <img src="/static/website.png" alt="Площадки">
                Площадки, каталоги и карты
            </h2>
            <p>Основные карты и каталоги DLKIP Electronics</p>
        </div>
    </div>
    <div class="map-links">
        <a href="https://2gis.uz/tashkent/search/Dlkip%20Electronics%2C%20%D0%BF%D1%80%D0%BE%D0%B8%D0%B7%D0%B2%D0%BE%D0%B4%D1%81%D1%82%D0%B2%D0%B5%D0%BD%D0%BD%D0%B0%D1%8F%20%D0%BA%D0%BE%D0%BC%D0%BF%D0%B0%D0%BD%D0%B8%D1%8F/firm/70000001116423561/69.374881%2C41.246852" target="_blank">📍 2GIS</a>
        <a href="https://www.google.com/maps/search/?api=1&query=DLKIP+Electronics+Tashkent" target="_blank">🗺 Google Maps</a>
        <a href="https://www.goldenpages.uz/company/?Id=121676" target="_blank">Golden Pages</a>
        <a href="https://top.uz/company/dlkip" target="_blank">Top.uz</a>
        <a href="https://www.yellowpages.uz/kompaniya/dlkip" target="_blank">Yellow Pages</a>
    </div>
   <details>
    <summary>Показать все площадки и ссылки на товары</summary>
    <div class="platform-grid">{PLATFORM_CARDS}</div>
</details>
</section>

<div class="footer">DLKIP Electronics • DLKIPChatBot • Ташкент • 2026</div>
</div>

<div class="operator" onclick="operatorChat()">
    <img src="/static/operator.png" alt="Оператор">
    <span>Оператор</span>
</div>

<div id="operator-window">
    <div class="operator-window-head">
        <div class="operator-window-title">
            <img src="/static/operator.png" alt="Оператор">
            <span>Оператор</span>
        </div>
        <button class="operator-close" onclick="closeOperator()">×</button>
    </div>

    <div class="operator-window-body">
        <p>Здравствуйте! Напишите сообщение оператору DLKIP Electronics.</p>

        <div id="operator-messages">
            <div class="operator-message">
                Оператор онлайн. Чем можем помочь?
            </div>
        </div>

        <div class="operator-input-area">
            <input
                id="operator-text"
                type="text"
                placeholder="Введите сообщение..."
                autocomplete="off"
                onkeydown="if(event.key==='Enter')sendOperatorMessage()"
            >
            <button onclick="sendOperatorMessage()">ОТПРАВИТЬ</button>
        </div>

        <a class="operator-telegram"
           href="https://t.me/Islam_Nigmatov"
           target="_blank"
           rel="noopener">
            💬 НАПИСАТЬ ОПЕРАТОРУ В TELEGRAM
        </a>
    </div>
</div>

<script>

document.addEventListener("DOMContentLoaded", function () {{
    const gutterVideos = document.querySelectorAll(".gutter-video video");

    gutterVideos.forEach(function(video) {{
        video.addEventListener("loadedmetadata", function() {{
            if (video.duration > 10) {{
                video.currentTime = 10;
            }}
        }});
    }});

    const blackVideo = document.getElementById("black-video");
    const orangeVideo = document.getElementById("orange-video");
    const centerVideos = [blackVideo, orangeVideo];
    let centerStarted = false;

    function playTogether() {{
        if (centerStarted || centerVideos.some(video => !video || video.readyState < 3)) return;
        centerStarted = true;

        centerVideos.forEach(function(video) {{
            video.pause();
            video.currentTime = 0;
        }});

        centerVideos.forEach(function(video) {{
            video.play().catch(function() {{}});
        }});
    }}

    centerVideos.forEach(function(video) {{
        if (video) video.addEventListener("canplay", playTogether);
    }});

    function restartTogether() {{
        if (!blackVideo || !orangeVideo) return;

        centerVideos.forEach(function(video) {{
            video.pause();
            video.currentTime = 0;
        }});

        centerVideos.forEach(function(video) {{
            video.play().catch(function() {{}});
        }});
    }}

    centerVideos.forEach(function(video) {{
        if (video) video.addEventListener("ended", restartTogether);
    }});

    playTogether();
}});

async function sendMessage() {{
    const input = document.getElementById("text");
    const messages = document.getElementById("messages");
    const text = input.value.trim();
    if (!text) return;

    messages.innerHTML += `
        <div class="message-row user-row">
            <div class="message user-message">
                <div class="label">Вы</div>
                ${{escapeHtml(text)}}
            </div>
        </div>
    `;

    input.value = "";

    const typingId = "typing-" + Date.now();

    messages.innerHTML += `
        <div class="message-row bot-row" id="${{typingId}}">
            <div class="message bot-message">
                <div class="label">DLKIP Operator Bot</div>
                <div class="typing"><span></span><span></span><span></span></div>
            </div>
        </div>
    `;

    messages.scrollTop = messages.scrollHeight;

    try {{
        const response = await fetch("/chat", {{
            method:"POST",
            headers:{{"Content-Type":"application/json"}},
            body:JSON.stringify({{message:text}})
        }});

        const data = await response.json();
        const typingElement = document.getElementById(typingId);
        if (typingElement) typingElement.remove();

        messages.innerHTML += `
            <div class="message-row bot-row">
                <div class="message bot-message">
                    <div class="label">DLKIP Operator Bot</div>
                    ${{escapeHtml(data.reply)}}
                </div>
            </div>
        `;
    }} catch(error) {{
        const typingElement = document.getElementById(typingId);
        if (typingElement) typingElement.remove();

        messages.innerHTML += `
            <div class="message-row bot-row">
                <div class="message bot-message">
                    <div class="label">DLKIP Operator Bot</div>
                    ❌ Временно невозможно связаться с сервером.
                </div>
            </div>
        `;
    }}

    messages.scrollTop = messages.scrollHeight;
}}

function operatorChat() {{
    const windowBox = document.getElementById("operator-window");
    windowBox.style.display = windowBox.style.display === "block" ? "none" : "block";
}}

function closeOperator() {{
    document.getElementById("operator-window").style.display = "none";
}}


function getOperatorClientId() {{
    let id = localStorage.getItem("dlkip_operator_client_id");
    if (!id) {{
        id = (window.crypto && crypto.randomUUID) ? crypto.randomUUID() :
             "client-" + Date.now() + "-" + Math.random().toString(16).slice(2);
        localStorage.setItem("dlkip_operator_client_id", id);
    }}
    return id;
}}

async function sendOperatorMessage() {{
    const input = document.getElementById("operator-text");
    const messages = document.getElementById("operator-messages");
    const text = input.value.trim();
    if (!text) return;

    const clientId = getOperatorClientId();
    input.disabled = true;

    try {{
        const response = await fetch("/operator/send", {{
            method:"POST",
            headers:{{"Content-Type":"application/json"}},
            body:JSON.stringify({{client_id:clientId, message:text}})
        }});
        const data = await response.json();

        if (!response.ok || !data.ok) throw new Error(data.error || "send error");

        const box = document.createElement("div");
        box.className = "operator-message user";
        box.textContent = "Вы: " + text;
        messages.appendChild(box);
        input.value = "";
        messages.scrollTop = messages.scrollHeight;
    }} catch(e) {{
        const box = document.createElement("div");
        box.className = "operator-message";
        box.textContent = "❌ Сообщение не отправлено. Попробуйте ещё раз.";
        messages.appendChild(box);
    }} finally {{
        input.disabled = false;
        input.focus();
    }}
}}

let operatorLastMessageId = 0;
async function pollOperatorMessages() {{
    try {{
        const clientId = getOperatorClientId();
        const response = await fetch("/operator/messages?client_id=" +
            encodeURIComponent(clientId) + "&after=" + operatorLastMessageId);
        const data = await response.json();
        const messages = document.getElementById("operator-messages");

        (data.messages || []).forEach(function(item) {{
            const box = document.createElement("div");
            box.className = "operator-message operator-reply";
            box.textContent = "Оператор: " + item.text;
            messages.appendChild(box);
            operatorLastMessageId = Math.max(operatorLastMessageId, item.id);
        }});
        if ((data.messages || []).length) messages.scrollTop = messages.scrollHeight;
    }} catch(e) {{}}
}}
setInterval(pollOperatorMessages, 2500);

function escapeHtml(text) {{
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}}
</script>
</body>
</html>"""


def telegram_api(method, payload):
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


@app.route("/operator/send", methods=["POST"])
def operator_send():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_OPERATOR_CHAT_ID:
        return jsonify({"ok": False, "error": "Telegram operator is not configured"}), 503

    data = request.get_json() or {}
    client_id = str(data.get("client_id", "")).strip()
    message = str(data.get("message", "")).strip()

    if not client_id or not message:
        return jsonify({"ok": False, "error": "Empty client_id or message"}), 400
    if len(message) > 3000:
        return jsonify({"ok": False, "error": "Message is too long"}), 400

    short_id = client_id[:12]
    telegram_text = (
        "🌐 DLKIP сайт\\n"
        f"Клиент: {short_id}\\n\\n"
        f"{message}\\n\\n"
        "↩️ Ответьте на ЭТО сообщение через Reply."
    )

    try:
        result = telegram_api("sendMessage", {
            "chat_id": TELEGRAM_OPERATOR_CHAT_ID,
            "text": telegram_text
        })
        tg_message_id = result["result"]["message_id"]
        TELEGRAM_MESSAGE_CLIENTS[tg_message_id] = client_id
        OPERATOR_CLIENT_MESSAGES.setdefault(client_id, [])
        return jsonify({"ok": True})
    except Exception as e:
        print("Telegram send error:", e)
        return jsonify({"ok": False, "error": "Telegram send failed"}), 502


@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():
    update = request.get_json() or {}
    message = update.get("message") or {}

    if str((message.get("chat") or {}).get("id", "")) != str(TELEGRAM_OPERATOR_CHAT_ID):
        return jsonify({"ok": True})

    reply_to = message.get("reply_to_message") or {}
    replied_message_id = reply_to.get("message_id")
    text = str(message.get("text", "")).strip()

    client_id = TELEGRAM_MESSAGE_CLIENTS.get(replied_message_id)
    if client_id and text:
        queue = OPERATOR_CLIENT_MESSAGES.setdefault(client_id, [])
        next_id = (queue[-1]["id"] + 1) if queue else 1
        queue.append({"id": next_id, "text": text})

    return jsonify({"ok": True})


@app.route("/operator/messages", methods=["GET"])
def operator_messages():
    client_id = request.args.get("client_id", "").strip()
    try:
        after = int(request.args.get("after", "0"))
    except ValueError:
        after = 0
    messages = OPERATOR_CLIENT_MESSAGES.get(client_id, [])
    return jsonify({"messages": [m for m in messages if m["id"] > after]})


@app.route("/chat", methods=["POST"])
def chat():
    if not client:
        return jsonify({"reply": "API Gemini ещё не подключён."})

    data = request.get_json() or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"reply": "Задайте ваш вопрос."})

    prompt = f"""
{DLKIP_CONTEXT}

Вопрос клиента:
{message}

Ответьте профессионально, кратко и точно.
Не выдумывайте цену, наличие или характеристики.
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )
        return jsonify({"reply": response.text})
    except Exception as e:
        print("Gemini error:", e)
        return jsonify({"reply": "Произошла ошибка при обработке запроса."})

if __name__ == "__main__":
    app.run(debug=True)
