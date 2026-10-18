import json, math, os
import flet as ft
import flet_map as fm
from data import SCHOOLS, LEVELS

BG, PRIMARY, ACCENT, LAV, INK = "#F4F3EF", "#0F766E", "#FF7A59", "#B8A9FF", "#1F2933"
FONT = "Vazir"
FONT_URL = "https://github.com/rastikerdar/vazirmatn/raw/master/fonts/ttf/Vazirmatn-Regular.ttf"
RES_FILE = os.path.join(os.getenv("FLET_APP_STORAGE_DATA", "."), "reservations.json")
TILE_SETS = {
    "Google Maps": ("https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}", []),
    "Carto": ("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png", ["a", "b", "c", "d"]),
    "OpenStreetMap": ("https://tile.openstreetmap.org/{z}/{x}/{y}.png", []),
}
def tiles():
    u, sd = TILE_SETS[P.get("tile", "Google Maps")]
    for kw in (dict(subdomains=sd, user_agent_package_name="com.madreseyab.app"), dict(subdomains=sd), {}):
        try: return fm.TileLayer(url_template=u, **kw)
        except TypeError: continue
TCOL = {"دولتی": "#0F766E", "نمونه دولتی": "#6C5CE7", "تیزهوشان (سمپاد)": "#F4A100", "غیردولتی": "#FF7A59",
        "هیئت امنایی": "#E84393", "شاهد": "#2D9CDB", "هنرستان (دولتی)": "#4D6BFE"}

PREF = os.path.join(os.getenv("FLET_APP_STORAGE_DATA", "."), "prefs.json")
try: P = json.load(open(PREF, encoding="utf-8"))
except Exception: P = {}
P.setdefault("fav", [])
def save_prefs(): json.dump(P, open(PREF, "w", encoding="utf-8"), ensure_ascii=False)

def km(a, b, c, d):
    p = math.pi / 180
    x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(x))

def pin(lat, lng, icon, color):
    return fm.Marker(content=ft.Icon(icon, color=color, size=38), coordinates=fm.MapLatitudeLongitude(lat, lng))

def main(page: ft.Page):
    page.title = "مدرسه‌یاب"
    page.rtl = True
    page.bgcolor = BG
    page.padding = 0
    page.fonts = {FONT: FONT_URL}
    page.theme = ft.Theme(font_family=FONT, color_scheme_seed=PRIMARY)
    S = {"home": None, "level": None}

    def show(*c):
        page.clean(); page.add(ft.SafeArea(ft.Column(list(c), expand=True), expand=True)); page.update()

    def btn(text, on_click, color=PRIMARY, disabled=False):
        return ft.ElevatedButton(text, on_click=on_click, bgcolor=color, color="white", disabled=disabled,
                                 height=52, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=18)))

    def header(title, back, action=None):
        return ft.Container(ft.Row([ft.IconButton(ft.Icons.ARROW_FORWARD, on_click=back, icon_color=INK),
                                    ft.Text(title, size=17, weight="bold", color=INK, expand=True)] + ([action] if action else [])),
                            padding=ft.padding.only(8, 8, 8, 0))

    # ---------- ۱) خوش‌آمدگویی ----------
    def welcome(e=None):
        def dot(sz, col, **pos): return ft.Container(width=sz, height=sz, bgcolor=col, border_radius=sz, **pos)
        hero = ft.Container(ft.Icon(ft.Icons.SCHOOL_ROUNDED, size=80, color="white"), width=150, height=150, border_radius=75,
                            alignment=ft.alignment.center, gradient=ft.LinearGradient([PRIMARY, "#2DD4BF"]),
                            shadow=ft.BoxShadow(blur_radius=40, color="#662DD4BF", offset=ft.Offset(0, 14)))
        col = ft.Column([hero,
            ft.Text("مدرسه‌یاب", size=34, weight="bold", color=INK),
            ft.Text("بهترین مدرسه را کنار خانه‌تان پیدا کنید؛ با نقشه، امتیاز و نظر اولیا", size=15, color="#52606D", text_align="center"),
            ft.Text(f"سلام {P['user']['name']} 👋" if P.get("user") else "", size=16, color=PRIMARY),
            ft.Container(height=10),
            btn("شروع ✨", lambda _: pick_home() if P.get("user") else login(), ACCENT)],
            horizontal_alignment="center", alignment="center", spacing=16)
        show(ft.Stack([
            ft.Container(left=0, right=0, top=0, bottom=0, gradient=ft.LinearGradient(
                ["#F4F3EF", "#E9E4FF", "#D5F5EE"], begin=ft.alignment.top_left, end=ft.alignment.bottom_right)),
            dot(220, "#55B8A9FF", top=-60, right=-70), dot(160, "#55FF7A59", bottom=90, left=-60), dot(90, "#552DD4BF", top=180, left=30),
            ft.Container(col, padding=32, alignment=ft.alignment.center, left=0, right=0, top=0, bottom=0)], expand=True))

    def login(e=None):
        n = ft.TextField(label="نام و نام خانوادگی")
        ph = ft.TextField(label="شماره موبایل", keyboard_type=ft.KeyboardType.PHONE)
        def go(_):
            if not (n.value and ph.value):
                n.error_text = "نام و شماره را وارد کنید"; page.update(); return
            P["user"] = {"name": n.value, "phone": ph.value}; save_prefs(); pick_home()
        show(header("ورود والدین", welcome), ft.Container(ft.Column([n, ph, btn("ورود", go)], spacing=16), padding=20))

    # ---------- ۲) انتخاب لوکیشن منزل ----------
    def next_tile(rebuild):
        n = list(TILE_SETS); P["tile"] = n[(n.index(P.get("tile", "Google Maps")) + 1) % len(n)]; save_prefs()
        rebuild(); page.open(ft.SnackBar(ft.Text(f"سبک نقشه: {P['tile']}")))

    def pick_home(e=None):
        layer = fm.MarkerLayer(markers=[pin(*S["home"], ft.Icons.HOME_ROUNDED, ACCENT)] if S["home"] else [])
        nxt = btn("تأیید موقعیت و ادامه", levels, PRIMARY, disabled=not S["home"])
        def tap(ev):
            c = getattr(ev, "coordinates", ev)
            S["home"] = (c.latitude, c.longitude)
            layer.markers = [pin(c.latitude, c.longitude, ft.Icons.HOME_ROUNDED, ACCENT)]
            nxt.disabled = False; page.update()
        m = fm.Map(expand=True, initial_center=fm.MapLatitudeLongitude(*(S["home"] or (35.72, 51.40))), initial_zoom=11,
                   on_tap=tap, layers=[tiles(), layer])
        show(header("🏠 خانه‌تان را روی نقشه لمس کنید", welcome,
                    ft.IconButton(ft.Icons.LAYERS, icon_color=PRIMARY, tooltip="تغییر سبک نقشه", on_click=lambda _: next_tile(pick_home))),
             ft.Container(m, expand=True, border_radius=24, margin=ft.margin.symmetric(0, 12), clip_behavior=ft.ClipBehavior.ANTI_ALIAS),
             ft.Container(nxt, padding=16))

    # ---------- ۳) انتخاب مقطع ----------
    def levels(e=None):
        def lcard(k, t, sub, icon, c1, c2):
            n = sum(1 for x in SCHOOLS if x["level"] == k)
            return ft.Container(ft.Row([
                ft.Container(ft.Icon(icon, size=34, color="white"), bgcolor="#33FFFFFF", padding=14, border_radius=20),
                ft.Column([ft.Text(t, size=19, weight="bold", color="white"), ft.Text(f"{sub} • {n} مدرسه", size=12, color="#E6FFFFFF")], spacing=2, expand=True),
                ft.Icon(ft.Icons.ARROW_BACK_IOS_NEW, color="white", size=16)], spacing=14),
                gradient=ft.LinearGradient([c1, c2], begin=ft.alignment.top_left, end=ft.alignment.bottom_right),
                padding=22, border_radius=28, on_click=lambda _: listing(k),
                shadow=ft.BoxShadow(blur_radius=20, color="#33000000", offset=ft.Offset(0, 8)))
        show(header("مقطع تحصیلی را انتخاب کنید", pick_home, ft.IconButton(ft.Icons.FAVORITE, icon_color=ACCENT, tooltip="موردعلاقه‌ها", on_click=favorites)),
             ft.Container(ft.Column([
                 lcard("primary", "ابتدایی", "پایه اول تا ششم", ft.Icons.CHILD_CARE, "#0F766E", "#2DD4BF"),
                 lcard("mid1", "متوسطه اول", "پایه هفتم تا نهم", ft.Icons.MENU_BOOK, "#6C5CE7", "#A29BFE"),
                 lcard("mid2", "متوسطه دوم", "دبیرستان و هنرستان", ft.Icons.ENGINEERING, "#FF7A59", "#FFB347")], spacing=18), padding=20))

    # ---------- ۴) فهرست، جستجو، فیلتر، علاقه‌مندی ----------
    def chip(t, c):
        return ft.Container(ft.Text(t, size=12, color=INK), bgcolor=c, padding=ft.padding.symmetric(4, 10), border_radius=14)

    def heart(s):
        def icon(): return ft.Icons.FAVORITE if s["id"] in P["fav"] else ft.Icons.FAVORITE_BORDER
        def tog(ev):
            f = P["fav"]; f.remove(s["id"]) if s["id"] in f else f.append(s["id"]); save_prefs()
            ev.control.icon = icon(); ev.control.update()
        return ft.IconButton(icon(), icon_color=ACCENT, on_click=tog)

    def card(s):
        d = km(*S["home"], s["lat"], s["lng"]); c = TCOL.get(s["type"], PRIMARY)
        av = ft.Container(ft.Icon(ft.Icons.ENGINEERING if s["tech"] else ft.Icons.SCHOOL_ROUNDED, color="white", size=26),
                          bgcolor=c, width=52, height=52, border_radius=18, alignment=ft.alignment.center)
        return ft.Container(ft.Row([av, ft.Column([
            ft.Text(s["name"], size=15, weight="bold", color=INK),
            ft.Text(f"📍 {s['area']} • {d:.1f} کیلومتر", size=12, color="#7B8794"),
            ft.Row([chip(s["type"], "#EFEAFF"), chip(f"⭐ {s['rating']}", "#FFE9DF")], wrap=True, spacing=6),
        ], spacing=5, expand=True), heart(s)], spacing=12), bgcolor="white", padding=14, border_radius=24,
            on_click=lambda _: detail(s), shadow=ft.BoxShadow(blur_radius=14, color="#14000000", offset=ft.Offset(0, 5)))

    def listing(level=None):
        level = level or S["level"]; S["level"] = level
        S["back"] = lambda _: listing(level)
        base = sorted([x for x in SCHOOLS if x["level"] == level], key=lambda x: km(*S["home"], x["lat"], x["lng"]))
        lv = ft.ListView(expand=True, spacing=12, padding=16)
        q = ft.TextField(hint_text="جستجوی نام مدرسه...", prefix_icon=ft.Icons.SEARCH, border_radius=16,
                         on_change=lambda _: refresh())
        flt = ft.SegmentedButton(selected={"all"}, on_change=lambda _: refresh(), visible=level == "mid2",
                                 segments=[ft.Segment("all", label=ft.Text("همه")), ft.Segment("acad", label=ft.Text("دبیرستان")),
                                           ft.Segment("tech", label=ft.Text("هنرستان"))])
        def refresh():
            f = next(iter(flt.selected))
            items = [x for x in base if (not q.value or q.value in x["name"]) and (f == "all" or (f == "tech") == x["tech"])]
            lv.controls = [card(x) for x in items] or [ft.Text("مدرسه‌ای پیدا نشد", text_align="center")]
            if lv.page: page.update()
        refresh()
        show(header(f"مدارس {LEVELS[level]} (نزدیک‌ترین‌ها)", levels),
             ft.Container(ft.Column([q, flt], spacing=8), padding=ft.padding.symmetric(0, 16)), lv)

    def favorites(e=None):
        S["back"] = favorites
        items = [card(x) for x in SCHOOLS if x["id"] in P["fav"]]
        show(header("مدارس موردعلاقه", levels),
             ft.ListView(items or [ft.Text("هنوز مدرسه‌ای ذخیره نکرده‌اید", text_align="center")], expand=True, spacing=12, padding=16))

    # ---------- ۵) جزئیات مدرسه ----------
    def detail(s):
        d = km(*S["home"], s["lat"], s["lng"]); c = TCOL.get(s["type"], PRIMARY)
        def row(icon, k, v): return ft.Row([ft.Icon(icon, size=18, color=PRIMARY), ft.Text(k, color="#7B8794", width=62), ft.Text(v, color=INK, expand=True)])
        tuition = "رایگان" if s["tuition"] == 0 else f"{s['tuition']:,} تومان / سال"
        gmap = f"https://www.google.com/maps/search/?api=1&query={s['lat']},{s['lng']}"
        mini = fm.Map(height=230, initial_center=fm.MapLatitudeLongitude(s["lat"], s["lng"]), initial_zoom=15,
                      layers=[tiles(), fm.MarkerLayer(markers=[pin(s["lat"], s["lng"], ft.Icons.LOCATION_ON, ACCENT),
                                                               pin(*S["home"], ft.Icons.HOME_ROUNDED, PRIMARY)])])
        hero = ft.Container(ft.Column([
            ft.Text(s["name"], size=21, weight="bold", color="white"),
            ft.Row([chip(s["type"], "#FFFFFF"), chip("دخترانه" if s["girl"] else "پسرانه", "#FFFFFF")], spacing=6),
            ft.Text(f"{'★' * round(s['rating'])}{'☆' * (5 - round(s['rating']))}  {s['rating']} از ۵  ({s['votes']} نظر اولیا)", color="white", size=14)],
            spacing=8), padding=22, border_radius=26,
            gradient=ft.LinearGradient([c, "#1F2933"], begin=ft.alignment.top_left, end=ft.alignment.bottom_right))
        info = ft.Container(ft.Column([
            row(ft.Icons.PAYMENTS, "شهریه", tuition), row(ft.Icons.DIRECTIONS_WALK, "فاصله", f"{d:.1f} کیلومتر از منزل شما"),
            row(ft.Icons.PLACE, "آدرس", s["address"]), row(ft.Icons.PHONE, "تلفن", s["phone"])], spacing=12),
            bgcolor="white", padding=18, border_radius=22)
        body = [hero, info]
        if s["fields"]:
            body += [ft.Text("🎯 رشته‌ها", weight="bold", size=16), ft.Row([chip(f, "#EFEAFF") for f in s["fields"]], wrap=True)]
        def trow(t):
            return ft.Row([ft.Container(ft.Text(t["name"][0], color="white", weight="bold"), bgcolor=c, width=40, height=40,
                                        border_radius=20, alignment=ft.alignment.center),
                           ft.Column([ft.Text(t["name"], weight="bold", size=14, color=INK),
                                      ft.Text(f"{t['subject']} • {t['years']} سال سابقه", size=12, color="#7B8794")], spacing=1, expand=True)])
        body += [ft.Text("👩‍🏫 معلمان و دروس", weight="bold", size=16),
                 ft.Container(ft.Column([trow(t) for t in s["teachers"]], spacing=12), bgcolor="white", padding=16, border_radius=22)]
        body += [ft.Text("💬 نظرات اولیا", weight="bold", size=16)]
        body += [ft.Container(ft.Text(r), bgcolor="white", padding=12, border_radius=16) for r in s["reviews"]]
        body += [ft.Text("🗺️ موقعیت روی نقشه", weight="bold", size=16),
                 ft.Container(mini, border_radius=22, clip_behavior=ft.ClipBehavior.ANTI_ALIAS),
                 ft.TextButton("تغییر سبک نقشه", icon=ft.Icons.LAYERS, on_click=lambda _: next_tile(lambda: detail(s))),
                 ft.Row([btn("Google Maps", lambda _: page.launch_url(gmap), PRIMARY), btn("رزرو ثبت‌نام", lambda _: reserve(s), ACCENT)],
                        wrap=True, alignment="center")]
        show(header("اطلاعات مدرسه", S["back"], heart(s)), ft.ListView(body, expand=True, spacing=12, padding=16))

    # ---------- ۶) رزرو ----------
    def reserve(s):
        u = P.get("user", {})
        parent, child, phone = ft.TextField(label="نام والدین", value=u.get("name")), ft.TextField(label="نام و کلاس فرزند"), \
            ft.TextField(label="شماره تماس", value=u.get("phone"), keyboard_type=ft.KeyboardType.PHONE)
        def save(_):
            if not (parent.value and child.value and phone.value):
                parent.error_text = "همه فیلدها را پر کنید"; page.update(); return
            try: data = json.load(open(RES_FILE, encoding="utf-8"))
            except Exception: data = []
            data.append(dict(school=s["name"], parent=parent.value, child=child.value, phone=phone.value))
            json.dump(data, open(RES_FILE, "w", encoding="utf-8"), ensure_ascii=False)
            page.close(dlg)
            page.open(ft.SnackBar(ft.Text("رزرو شما با موفقیت ثبت شد ✅")))
        dlg = ft.AlertDialog(title=ft.Text("رزرو ثبت‌نام"), content=ft.Column([parent, child, phone], tight=True),
                             actions=[ft.TextButton("انصراف", on_click=lambda _: page.close(dlg)),
                                      ft.ElevatedButton("ثبت رزرو", on_click=save)])
        page.open(dlg)

    def guard(fn):
        def w(*a):
            try: return fn(*a)
            except Exception:
                import traceback
                page.open(ft.AlertDialog(title=ft.Text("خطا (این متن را برای پشتیبان بفرستید)"),
                          content=ft.Text(traceback.format_exc()[-1200:], selectable=True, size=11)))
        return w
    welcome, login, pick_home, levels, listing, favorites, detail, reserve = map(
        guard, (welcome, login, pick_home, levels, listing, favorites, detail, reserve))

    welcome()

ft.app(target=main)
