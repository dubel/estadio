import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

TEXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "textures")
os.makedirs(TEXTURES_DIR, exist_ok=True)

FONT_PATH = "/usr/share/fonts/liberation/LiberationSans-Bold.ttf"

def get_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()

def generate_pitch_texture():
    """Generuje fotorealistyczną murawę z pasami koszenia (mowing stripes)."""
    grass_base_path = os.path.join(TEXTURES_DIR, "grass", "Grass001_1K-JPG_Color.jpg")
    size = 2048
    out_img = Image.new("RGB", (size, size))
    
    if os.path.exists(grass_base_path):
        base_tile = Image.open(grass_base_path).convert("RGB")
        tile_w, tile_h = base_tile.size
        for x in range(0, size, tile_w):
            for y in range(0, size, tile_h):
                out_img.paste(base_tile, (x, y))
    else:
        # Fallback jeśli brak pliku
        draw = ImageDraw.Draw(out_img)
        draw.rectangle([0, 0, size, size], fill=(45, 105, 38))
        
    # Pasy koszenia wzdłuż boiska (20 pasów)
    num_stripes = 20
    stripe_h = size / num_stripes
    
    overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d_over = ImageDraw.Draw(overlay)
    
    for i in range(num_stripes):
        y0 = int(i * stripe_h)
        y1 = int((i + 1) * stripe_h)
        if i % 2 == 0:
            # Jaśniejszy pas trawy (odbicie słońca)
            d_over.rectangle([0, y0, size, y1], fill=(180, 240, 140, 45))
        else:
            # Ciemniejszy pas trawy
            d_over.rectangle([0, y0, size, y1], fill=(20, 60, 15, 35))
            
    # Połączenie
    out_img.paste(Image.alpha_composite(out_img.convert("RGBA"), overlay).convert("RGB"))
    
    # Lekki winiet / naturalne zróżnicowanie podłoża
    enhancer = ImageEnhance.Color(out_img)
    out_img = enhancer.enhance(1.15)
    
    save_path = os.path.join(TEXTURES_DIR, "pitch_grass_mowed.jpg")
    out_img.save(save_path, quality=92)
    print(f"Zapisano teksturę murawy: {save_path}")

def generate_fascia_banner():
    """Generuje historyczny banner na białą blendę Trybuny Głównej."""
    w, h = 2048, 256
    img = Image.new("RGBA", (w, h), (242, 242, 240, 255))
    draw = ImageDraw.Draw(img)
    
    # Czerwone pasy klubowe na górze i dole
    draw.rectangle([0, 0, w, 18], fill=(195, 25, 30, 255))
    draw.rectangle([0, h - 18, w, h], fill=(195, 25, 30, 255))
    
    # Herb ŁKS po lewej i prawej stronie
    for cx in [160, w - 160]:
        cy = h // 2
        r = 85
        # Czerwony okrąg
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(195, 25, 30, 255), outline=(255, 255, 255, 255), width=4)
        # Przeplatana litera / napis
        font_crest = get_font(48)
        draw.text((cx, cy - 8), "ŁKS", fill=(255, 255, 255, 255), font=font_crest, anchor="mm")
        font_sub = get_font(22)
        draw.text((cx, cy + 38), "1908", fill=(255, 255, 255, 255), font=font_sub, anchor="mm")
        
    # Główny napis historyczny
    font_main = get_font(68)
    text_part1 = "TUTAJ WYCHOWANI  •  "
    text_part2 = "ŁKS TO WIĘCEJ NIŻ KLUB"
    text_part3 = "  •  WIERNI I ODDANI"
    
    # Wyśrodkowany tekst z podziałem barw
    full_text = text_part1 + text_part2 + text_part3
    draw.text((w // 2, h // 2), full_text, fill=(25, 25, 25, 255), font=font_main, anchor="mm")
    
    # Podświetlenie słowa ŁKS w kolorze czerwonym
    bbox_full = draw.textbbox((w // 2, h // 2), full_text, font=font_main, anchor="mm")
    # Zastępujemy napis barwnym
    draw.rectangle([bbox_full[0]-4, bbox_full[1]-4, bbox_full[2]+4, bbox_full[3]+4], fill=(242, 242, 240, 255))
    
    # Precyzyjny podział
    w_p1 = draw.textlength(text_part1, font=font_main)
    w_p2 = draw.textlength(text_part2, font=font_main)
    w_p3 = draw.textlength(text_part3, font=font_main)
    tot_w = w_p1 + w_p2 + w_p3
    
    start_x = (w - tot_w) / 2
    draw.text((start_x, h // 2), text_part1, fill=(25, 25, 25, 255), font=font_main, anchor="lm")
    draw.text((start_x + w_p1, h // 2), text_part2, fill=(195, 25, 30, 255), font=font_main, anchor="lm")
    draw.text((start_x + w_p1 + w_p2, h // 2), text_part3, fill=(25, 25, 25, 255), font=font_main, anchor="lm")
    
    save_path = os.path.join(TEXTURES_DIR, "banner_tutaj_wychowani.png")
    img.save(save_path)
    print(f"Zapisano banner fasady: {save_path}")

def generate_clock_face():
    """Generuje autentyczną tarczę zegarową z historycznym logo OMEGA / 1908."""
    size = 1024
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cx, cy = size // 2, size // 2
    r_outer = size // 2 - 20
    
    # Jasna kremowa tarcza
    draw.ellipse([cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer], fill=(244, 244, 240, 255), outline=(20, 20, 20, 255), width=18)
    
    # Kreski minutowe i godzinowe
    for min_idx in range(60):
        ang = math.radians(min_idx * 6.0 - 90.0)
        is_hour = (min_idx % 5 == 0)
        tick_len = 45 if is_hour else 20
        tick_w = 12 if is_hour else 4
        
        x0 = cx + (r_outer - 35) * math.cos(ang)
        y0 = cy + (r_outer - 35) * math.sin(ang)
        x1 = cx + (r_outer - 35 - tick_len) * math.cos(ang)
        y1 = cy + (r_outer - 35 - tick_len) * math.sin(ang)
        
        draw.line([x0, y0, x1, y1], fill=(25, 25, 25, 255), width=tick_w)
        
    # Cyfry godzinowe (rzymskie)
    numerals = ["XII", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"]
    font_num = get_font(52)
    for h_idx, num in enumerate(numerals):
        ang = math.radians(h_idx * 30.0 - 90.0)
        rx = cx + (r_outer - 135) * math.cos(ang)
        ry = cy + (r_outer - 135) * math.sin(ang)
        draw.text((rx, ry), num, fill=(20, 20, 20, 255), font=font_num, anchor="mm")
        
    # Logo OMEGA / Plebiscyt 1932 na tarczy
    font_logo = get_font(38)
    draw.text((cx, cy - 140), "OMEGA", fill=(30, 30, 30, 255), font=font_logo, anchor="mm")
    font_sub = get_font(22)
    draw.text((cx, cy + 140), "ŁKS ŁÓDŹ", fill=(195, 25, 30, 255), font=font_sub, anchor="mm")
    
    # Wskazówki zegara (ustawione na 16:45)
    # Wskazówka godzinowa (kąt na 4.75 godziny = 142.5°)
    ang_h = math.radians(142.5 - 90.0)
    hx = cx + (r_outer * 0.48) * math.cos(ang_h)
    hy = cy + (r_outer * 0.48) * math.sin(ang_h)
    draw.line([cx, cy, hx, hy], fill=(15, 15, 15, 255), width=22)
    
    # Wskazówka minutowa (kąt na 45 minut = 270°)
    ang_m = math.radians(270.0 - 90.0)
    mx = cx + (r_outer * 0.72) * math.cos(ang_m)
    my = cy + (r_outer * 0.72) * math.sin(ang_m)
    draw.line([cx, cy, mx, my], fill=(15, 15, 15, 255), width=14)
    
    # Centralny nit
    draw.ellipse([cx - 24, cy - 24, cx + 24, cy + 24], fill=(15, 15, 15, 255))
    
    save_path = os.path.join(TEXTURES_DIR, "clock_face.png")
    img.save(save_path)
    print(f"Zapisano tarczę zegara: {save_path}")

def generate_fan_graffiti_banners():
    """Generuje kibicowskie banery i graffiti wzdłuż murawy i płotów."""
    w, h = 2048, 256
    img = Image.new("RGBA", (w, h), (30, 32, 34, 255))
    draw = ImageDraw.Draw(img)
    
    # 4 sekcje banerów kibicowskich
    sec_w = w // 4
    
    # 1. Biało-czerwono-białe pasy + ŁKS ŁÓDŹ
    draw.rectangle([0, 0, sec_w, h // 3], fill=(255, 255, 255, 255))
    draw.rectangle([0, h // 3, sec_w, 2 * h // 3], fill=(195, 25, 30, 255))
    draw.rectangle([0, 2 * h // 3, sec_w, h], fill=(255, 255, 255, 255))
    font_b = get_font(52)
    draw.text((sec_w // 2, h // 2), "ŁKS ŁÓDŹ", fill=(255, 255, 255, 255), font=font_b, anchor="mm", stroke_width=4, stroke_fill=(15, 15, 15, 255))
    
    # 2. RODOWICI ŁODZIANIE
    x2 = sec_w
    draw.rectangle([x2, 0, x2 + sec_w, h], fill=(235, 235, 230, 255))
    draw.rectangle([x2, 0, x2 + sec_w, 14], fill=(195, 25, 30, 255))
    draw.rectangle([x2, h - 14, x2 + sec_w, h], fill=(195, 25, 30, 255))
    draw.text((x2 + sec_w // 2, h // 2), "RODOWICI ŁODZIANIE", fill=(195, 25, 30, 255), font=font_b, anchor="mm")
    
    # 3. 1908 DUMA ŁODZI
    x3 = 2 * sec_w
    draw.rectangle([x3, 0, x3 + sec_w, h], fill=(195, 25, 30, 255))
    draw.text((x3 + sec_w // 2, h // 2), "1908 • DUMA ŁODZI", fill=(255, 255, 255, 255), font=font_b, anchor="mm", stroke_width=3, stroke_fill=(20, 20, 20, 255))
    
    # 4. GALERA JEST TYLKO JEDNA
    x4 = 3 * sec_w
    draw.rectangle([x4, 0, x4 + sec_w, h], fill=(240, 240, 238, 255))
    draw.rectangle([x4, 0, x4 + sec_w, 14], fill=(195, 25, 30, 255))
    draw.rectangle([x4, h - 14, x4 + sec_w, h], fill=(195, 25, 30, 255))
    draw.text((x4 + sec_w // 2, h // 2), "GALERA JEST TYLKO JEDNA", fill=(20, 20, 20, 255), font=get_font(42), anchor="mm")
    
    save_path = os.path.join(TEXTURES_DIR, "fan_graffiti_banners.png")
    img.save(save_path)
    print(f"Zapisano banery kibicowskie: {save_path}")

def generate_scoreboard_textures():
    """Generuje autentyczną teksturę tablicy wyników i zegara z archiwalnego zdjęcia."""
    src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "zdjecia", "screenshot-2026-10-16_19-37-09.png")
    if not os.path.exists(src_path):
        print(f"Brak pliku źródłowego: {src_path}")
        return
        
    im = Image.open(src_path)
    # Wycięcie prostokąta tablicy (wymiary i proporcje 1:1)
    crop = im.crop((54, 66, 1726, 672))
    
    save_path = os.path.join(TEXTURES_DIR, "scoreboard_historic.png")
    crop.save(save_path)
    
    # Mapa emisji dla trybu nocnego
    import numpy as np
    arr = np.array(crop.convert('RGB'), dtype=np.float32)
    emission = np.zeros_like(arr)
    
    # 1. Świecące białe wskazówki i indeksy zegara (lewa strona tablicy)
    clock_area = arr[:480, :420]
    bright_mask = (clock_area[:, :, 0] > 140) & (clock_area[:, :, 1] > 140) & (clock_area[:, :, 2] > 140)
    emission[:480, :420][bright_mask] = clock_area[bright_mask] * 1.8
    
    # 2. Świecący żółto-zielony napis 'ŁÓDZKI KLUB SPORTOWY' na górnej matrycy
    text_area = arr[:90, 400:1600]
    green_mask = (text_area[:, :, 1] > 100) & (text_area[:, :, 0] > 70) & (text_area[:, :, 2] < 120)
    emission[:90, 400:1600][green_mask] = text_area[green_mask] * 2.2
    
    emission = np.clip(emission, 0, 255).astype(np.uint8)
    em_img = Image.fromarray(emission)
    save_em_path = os.path.join(TEXTURES_DIR, "scoreboard_emission.png")
    em_img.save(save_em_path)
    print(f"Zapisano tablicę wyników i mapę emisji: {save_path}, {save_em_path}")

def generate_przeplatanka_texture():
    """
    Generuje autentyczny biały murek z czerwoną Przeplatanką (historyczny herb ŁKS Łódź)
    na podstawie oficjalnej grafiki nadesłanej przez użytkownika.
    """
    w, h = 2048, 512
    # Drobne ziarno malowanego betonu
    np.random.seed(42)
    noise = np.random.normal(0, 3, (h, w)).astype(np.float32)
    base_r = np.clip(244.0 + noise, 0, 255).astype(np.uint8)
    base_g = np.clip(244.0 + noise, 0, 255).astype(np.uint8)
    base_b = np.clip(242.0 + noise, 0, 255).astype(np.uint8)

    wall = np.stack([base_r, base_g, base_b], axis=-1)
    wall_img = Image.fromarray(wall, 'RGB').convert('RGBA')

    # Wczytanie wypreparowanej Przeplatanki
    przep_path = os.path.join(TEXTURES_DIR, "przeplatanka_clean.png")
    if not os.path.exists(przep_path):
        print(f"Brak {przep_path} — pomijam teksturę murka z Przeplatanką.")
        return
    else:
        przep = Image.open(przep_path).convert('RGBA')

    # Skalowanie herbu do wysokości murka z zachowaniem proporcji
    target_h = 410
    target_w = int(przep.width * (target_h / przep.height))
    przep_scaled = przep.resize((target_w, target_h), Image.Resampling.LANCZOS)

    pos_x = (w - target_w) // 2
    pos_y = (h - target_h) // 2
    wall_img.alpha_composite(przep_scaled, (pos_x, pos_y))

    save_path = os.path.join(TEXTURES_DIR, "przeplatanka_wall.png")
    wall_img.save(save_path)
    print(f"Zapisano teksturę murka z autentyczną Przeplatanką: {save_path}")

GRAFFITI_PHOTO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "zdjecia", "grafy_na_trybunie.png")

# Narożniki (lewy-górny, prawy-górny, prawy-dolny, lewy-dolny) w pikselach grafy_na_trybunie.png (2858 x 1454)
MURAL_QUAD = [(186, 636), (2803, 806), (2803, 895), (186, 745)]          # „Tutaj wychowani … wierni i oddani”


def _rectify(im, quad, size):
    """Prostuje czworokąt ze zdjęcia do prostokąta size (przekształcenie perspektywiczne, nie dwuliniowe)."""
    w, h = size
    dst = [(0, 0), (w, 0), (w, h), (0, h)]
    rows = []
    for (x, y), (u, v) in zip(quad, dst):
        rows.append([u, v, 1, 0, 0, 0, -x * u, -x * v])
        rows.append([0, 0, 0, u, v, 1, -y * u, -y * v])
    coeffs = np.linalg.solve(np.array(rows, dtype=float), np.array([c for p in quad for c in p], dtype=float))
    return im.transform(size, Image.Transform.PERSPECTIVE, tuple(coeffs), Image.Resampling.BICUBIC)


# Graffiti dzielnic na bloczkach sektora górnego, od północy (oś dźwigara k = 1..13; build_grandstand.GRAFFITI_ATLAS).
# Narożniki (lewy-górny, prawy-górny, prawy-dolny, lewy-dolny) w pikselach zdjęć z zdjecia/.
BLOCK_GRAFFITI = [
    ("trybuna_vip.jpg", [(1069, 193), (1232, 193), (1232, 228), (1069, 229)]),                          # WRWG
    ("il20250305_898037543_xlarge.jpg", [(572, 640), (1002, 655), (1002, 722), (572, 712)]),            # OS. KOPERNIKA
    ("il20250305_898037543_xlarge.jpg", [(35, 623), (502, 637), (502, 712), (35, 700)]),                # TOLECHÓW
    ("grafy_na_trybunie.png", [(1430, 582), (1950, 607), (1950, 700), (1430, 690)]),                     # POLESIE
    ("grafy_na_trybunie.png", [(700, 510), (1300, 540), (1300, 650), (700, 600)]),                       # STARE ŁK
    ("lawka_rezerwowych.jpg", [(862, 215), (1170, 218), (1170, 270), (862, 268)]),                      # ŁODZIANIE
    ("lawka_rezerwowych.jpg", [(490, 203), (815, 203), (815, 256), (490, 254)]),                        # RODOWICI
    ("il20250305_898037523_xlarge.jpg", [(663, 563), (1207, 573), (1207, 648), (663, 640)]),            # DĄBROWA
    ("il20250305_898037523_xlarge.jpg", [(52, 550), (580, 557), (580, 635), (52, 628)]),                # LEGION z czaszką
    ("il20250305_898037559_xlarge.jpg", [(930, 462), (1258, 462), (1258, 517), (930, 517)]),            # SOJTA / ELKSA
    ("il20250305_898037559_xlarge.jpg", [(567, 463), (876, 463), (876, 516), (567, 516)]),              # JULIANÓW
    ("il20250305_898037559_xlarge.jpg", [(238, 466), (523, 466), (523, 516), (238, 516)]),              # RADOGOSZCZ
    ("il20250305_898037559_xlarge.jpg", [(37, 467), (197, 467), (197, 514), (37, 514)]),                # MARYSIN
]
GRAFFITI_SLOT = (1024, 168)             # proporcje lica bloczka (7.6 x 1.25 m); atlas 2048 x 2048, 2 kolumny po 12


def generate_block_graffiti_atlas():
    """
    Atlas graffiti bloczków (graffiti_bloczki.png): każde wyprostowane do swoich proporcji; węższe od lica
    bloczka dociągnięte do szerokości slotu powieleniem skrajnych kolumn (tło muru), zamiast rozciągać litery.
    """
    W, H = GRAFFITI_SLOT
    atlas = Image.new("RGB", (2048, 2048), (235, 235, 230))
    for i, (photo, quad) in enumerate(BLOCK_GRAFFITI):
        im = Image.open(os.path.join(PHOTOS_DIR, photo)).convert("RGB")
        w_px = (math.dist(quad[0], quad[1]) + math.dist(quad[3], quad[2])) / 2
        h_px = (math.dist(quad[0], quad[3]) + math.dist(quad[1], quad[2])) / 2
        w = min(W, round(H * w_px / h_px))
        art = _rectify(im, quad, (w, H))
        slot = Image.new("RGB", (W, H))
        x0 = (W - w) // 2
        slot.paste(art, (x0, 0))
        if x0 > 0:
            slot.paste(art.crop((0, 0, 1, H)).resize((x0, H)), (0, 0))
            slot.paste(art.crop((w - 1, 0, w, H)).resize((W - x0 - w, H)), (x0 + w, 0))
        atlas.paste(slot, ((i // 12) * W, (i % 12) * H))
    atlas.save(os.path.join(TEXTURES_DIR, "graffiti_bloczki.png"))
    print("Zapisano atlas graffiti bloczków")


def generate_mural_texture():
    """Mural na licu balustrady czołowej sektora górnego, wyprostowany z grafy_na_trybunie.png (2048 x 128)."""
    im = Image.open(GRAFFITI_PHOTO).convert("RGB")
    mural = _rectify(im, MURAL_QUAD, (2048, 128))
    mural.save(os.path.join(TEXTURES_DIR, "mural_tutaj_wychowani.png"))
    print("Zapisano mural (grafy_na_trybunie.png)")


PHOTOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "zdjecia")
# Narożniki (lewy-górny, prawy-górny, prawy-dolny, lewy-dolny) w pikselach zdjęć (ścieżki względem zdjecia/)
ENTRANCE_GRAPHICS = [
    # baner nad bramą wejścia północnego „ŁÓDZKI KLUB SPORTOWY WITA! / TRYBUNA SEKTOR 7-12” (740 x 416)
    ("wejscia_na_trybune/34dec5jwrhekegfii2gbtewomd2jvtzt.jpeg", [(217, 42), (490, 43), (490, 83), (217, 83)], (1024, 152), "baner_lks_wita.png"),
    # baner nad bramą wejścia południowego „… WITA! / TRYBUNA SEKTOR 1-6 / LOŻA B” (1280 x 853, ujęcie skośne)
    ("il20250305_898038021_xlarge.jpg", [(918, 416), (1212, 384), (1216, 428), (922, 461)], (1024, 152), "baner_lks_wita_poludnie.png"),
    # baner „MOSiR Łódź” na przeszkleniu południowego szczytu trybuny (1024 x 511); lewy dolny róg zasłania budynek
    ("wejscia_na_trybune/lks19 (1).jpg", [(652, 234), (845, 236), (845, 334), (652, 334)], (1024, 512), "baner_mosir.png"),
    # tablica MOSiR z planem sektorów (800 x 600)
    ("wejscia_na_trybune/DSC01679.jpg", [(40, 55), (748, 50), (755, 545), (35, 548)], (1024, 724), "tablica_mosir_plan.png"),
    # napis „RESTAURACJA” na budynku północnego szczytu (1280 x 853)
    ("il20250305_898037725_xlarge.jpg", [(930, 527), (1095, 525), (1095, 583), (930, 585)], (512, 160), "napis_restauracja.png"),
    # tablica sponsorska ZINA / T-Mobile Ekstraklasa na tylnej ścianie ławki rezerwowych (1280 x 853)
    ("lawka_rezerwowych_closeup.jpg", [(205, 333), (1118, 333), (1118, 503), (205, 503)], (2048, 384), "lawka_tablica_sponsorska.png"),
    # kartka „SĘDZIA TECHNICZNY” na budce sędziego technicznego (1280 x 853)
    ("il20250305_898037783_xlarge.jpg", [(513, 201), (636, 199), (636, 324), (513, 324)], (256, 256), "kartka_sedzia_techniczny.png"),
    # tablica pamiątkowa „Działaczom i zawodnikom ŁKS” na białej ścianie z czerwonym pasem (1280 x 1920)
    ("tablica_trybuna.jpg", [(0, 790), (1280, 800), (1280, 1650), (0, 1650)], (768, 512), "tablica_pamiatkowa.png"),
]


def _clean_dugout_board(img):
    """
    Tablica sponsorska ławki (2048 x 384): bez krzesełek zasłaniających dół i bez słupka daszku.
    Słupek (kolumny 928–955) zamalowany: poza środkowym logo Ekstraklasy tłem przesuniętym o jeden rozstaw
    logo ZINA (143 px), w obrębie logo (wiersze 88–190) tym samym miejscem lewego logo (567 px w lewo,
    10 px wyżej). Dół od rzędu zasłoniętego krzesełkami zastąpiony dwiema kopiami czystego rzędu 224–276
    (rozstaw rzędów 52 px).
    """
    img = img.copy()
    x0, x1, box = 928, 956, (88, 190)
    img.paste(img.crop((x0 - 143, 0, x1 - 143, box[0])), (x0, 0))
    img.paste(img.crop((x0 - 143, box[1], x1 - 143, 384)), (x0, box[1]))
    img.paste(img.crop((x0 - 567, box[0] - 10, x1 - 567, box[1] - 10)), (x0, box[0]))
    out = Image.new("RGB", img.size)
    out.paste(img.crop((0, 0, 2048, 276)), (0, 0))
    row = img.crop((0, 224, 2048, 276))
    out.paste(row, (0, 276))
    out.paste(row, (0, 328))
    out.paste(img.crop((0, 0, 2048, 4)).transpose(Image.Transpose.FLIP_TOP_BOTTOM), (0, 380))
    return out


def generate_entrance_textures():
    """Grafiki wejść, szczytów trybuny i ławek rezerwowych, wyprostowane ze zdjęć (ENTRANCE_GRAPHICS)."""
    for photo, quad, size, out in ENTRANCE_GRAPHICS:
        im = Image.open(os.path.join(PHOTOS_DIR, photo)).convert("RGB")
        img = _rectify(im, quad, size)
        if out == "lawka_tablica_sponsorska.png":
            img = _clean_dugout_board(img)
        img.save(os.path.join(TEXTURES_DIR, out))
    print("Zapisano grafiki wejść i szczytów trybuny")


def generate_gate_mesh_texture():
    """Siatka bram wejściowych (34dec5jwrhekegfii2gbtewomd2jvtzt.jpeg): ocynkowane pręty, oczka 5 x 20 cm, kafel 1 m."""
    W = H = 256
    wire = (170, 172, 168, 255)
    img = Image.new("RGBA", (W, H), wire[:3] + (0,))   # tło w kolorze pręta: mipmapy nie przyciemniają siatki
    draw = ImageDraw.Draw(img)
    for i in range(20):
        x = min(int(i * W / 20), W - 1)
        draw.line([(x, 0), (x, H)], fill=wire, width=2)
    for j in range(5):
        y = min(int(j * H / 5), H - 1)
        draw.line([(0, y), (W, y)], fill=wire, width=3)
    img.save(os.path.join(TEXTURES_DIR, "brama_siatka.png"))
    print("Zapisano teksturę siatki bram")


def generate_corrugated_roof_textures():
    """Generuje tekstury blachy trapezowej / falistej w kolorze białym i czerwonym ŁKS."""
    w, h = 512, 512
    # 1. Biała blacha
    img_white = Image.new("RGB", (w, h))
    # 2. Czerwona blacha ŁKS
    img_red = Image.new("RGB", (w, h))
    
    draw_w = ImageDraw.Draw(img_white)
    draw_r = ImageDraw.Draw(img_red)
    
    # Fale trapezowe wzdłuż osi Y (rozstaw przetłoczenia co 16 px)
    wave_period = 16.0
    for x in range(w):
        # Kąt przetłoczenia
        ang = (x % wave_period) / wave_period * 2.0 * math.pi
        shade = 0.5 + 0.5 * math.sin(ang)
        
        # Kolor biały (210 - 250)
        bw = int(210 + 40 * shade)
        draw_w.line([(x, 0), (x, h)], fill=(bw, bw, bw - 2))
        
        # Kolor czerwony (R: 160-220, G: 15-30, B: 20-35)
        br = int(160 + 55 * shade)
        draw_r.line([(x, 0), (x, h)], fill=(br, 22, 28))
        
    path_w = os.path.join(TEXTURES_DIR, "roof_corrugated_white.jpg")
    path_r = os.path.join(TEXTURES_DIR, "roof_corrugated_red.jpg")
    img_white.save(path_w, quality=92)
    img_red.save(path_r, quality=92)
    print(f"Zapisano tekstury blachy falistej: {path_w}, {path_r}")

def generate_floodlight_glow_sprite():
    """Generuje radialny rozbłysk światła (glow flare) dla nocnych jupiterów w Three.js."""
    size = 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cx, cy = size // 2, size // 2
    r_max = size // 2
    
    for r in range(r_max, 0, -1):
        dist = r / r_max
        # Profil wykładniczy rozbłysku (oślepiające białe centrum)
        alpha = int(255 * math.exp(-dist * 4.5))
        # Delikatny błękitno-krystaliczny odcień na obrzeżach reflektora
        color = (255, 255, int(240 + 15 * (1.0 - dist)), alpha)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
        
    save_path = os.path.join(TEXTURES_DIR, "floodlight_glow.png")
    img.save(save_path)
    print(f"Zapisano sprite rozbłysku jupitera: {save_path}")

def generate_goal_net_texture():
    """
    Generuje teksturę siatki bramkarskiej z oczkami i pasami biało-czerwono-białymi
    (w stylu Ajaxu Amsterdam i barw ŁKS Łódź).
    Siatka ma transparentne oczka oraz 3 pionowe pasy:
    Lewy pas: biały (1/3 szerokości)
    Środkowy pas: czerwony ŁKS (1/3 szerokości)
    Prawy pas: biały (1/3 szerokości)
    """
    W, H = 2048, 1024
    num_cells_x = 48
    num_cells_y = 24
    
    # Inicjalizacja tła z kolorem pasów, ale z alpha = 0 (dla idealnego filtrowania mipmap bez ciemnych obwódek)
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    split1 = int(W * 0.333)
    split2 = int(W * 0.667)
    
    # Kolory bazowe pasów
    WHITE_RGB = np.array([255, 255, 255], dtype=np.uint8)
    RED_RGB = np.array([235, 25, 30], dtype=np.uint8)
    
    arr[:, :split1, :3] = WHITE_RGB
    arr[:, split1:split2, :3] = RED_RGB
    arr[:, split2:, :3] = WHITE_RGB
    arr[:, :, 3] = 0 # początkowo całe tło jest przezroczyste
    
    img = Image.fromarray(arr, 'RGBA')
    draw = ImageDraw.Draw(img)
    
    dx = W / num_cells_x
    dy = H / num_cells_y
    cord_w = 8 # grubosc sznurka w pikselach
    
    WHITE_RGBA = (255, 255, 255, 255)
    RED_RGBA = (235, 25, 30, 255)
    
    # 1. Sznurki pionowe
    for i in range(num_cells_x + 1):
        x = int(i * dx)
        if x >= W: x = W - 1
        col = RED_RGBA if (split1 <= x <= split2) else WHITE_RGBA
        draw.line([(x, 0), (x, H)], fill=col, width=cord_w)
        
    # 2. Sznurki poziome
    for j in range(num_cells_y + 1):
        y = int(j * dy)
        if y >= H: y = H - 1
        draw.line([(0, y), (split1, y)], fill=WHITE_RGBA, width=cord_w)
        draw.line([(split1, y), (split2, y)], fill=RED_RGBA, width=cord_w)
        draw.line([(split2, y), (W, y)], fill=WHITE_RGBA, width=cord_w)
        
    # 3. Węzły na skrzyżowaniach
    for i in range(num_cells_x + 1):
        x = int(i * dx)
        if x >= W: x = W - 1
        col = RED_RGBA if (split1 <= x <= split2) else WHITE_RGBA
        for j in range(num_cells_y + 1):
            y = int(j * dy)
            if y >= H: y = H - 1
            draw.ellipse([(x - 4, y - 4), (x + 4, y + 4)], fill=col)
            
    save_path = os.path.join(TEXTURES_DIR, "goal_net_striped.png")
    img.save(save_path)
    print(f"Zapisano teksturę siatki bramkarskiej: {save_path}")

def generate_ball_net_texture():
    """Zielona siatka piłkochwytów za bramką południową (bloczki_na_trybunie.png): oczka 12.5 cm, kafel 1 m."""
    W = H = 512
    cells = 8
    green = (46, 140, 58, 255)
    img = Image.new("RGBA", (W, H), green[:3] + (0,))   # tło w kolorze sznurka: mipmapy nie przyciemniają siatki
    draw = ImageDraw.Draw(img)
    for i in range(cells + 1):
        c = min(int(i * W / cells), W - 1)
        draw.line([(c, 0), (c, H)], fill=green, width=4)
        draw.line([(0, c), (W, c)], fill=green, width=4)
    save_path = os.path.join(TEXTURES_DIR, "pilkochwyt_siatka.png")
    img.save(save_path)
    print(f"Zapisano teksturę siatki piłkochwytów: {save_path}")

def generate_fence_texture():
    """
    Przęsło ogrodzenia trybun (2.5 m x 2.5 m, widok_z_galery.jpg): u dołu pełne, rdzawobrązowe panele
    blachy (~0.9 m), wyżej siatka z drutu w oczka ~10 cm, rama i słupki malowane na czerwonobrązowo.
    RGB przezroczystych pikseli = kolor drutu, żeby mipmapy nie dawały ciemnych obwódek.
    """
    W = H = 256
    px_per_m = W / 2.5
    frame = np.array([118, 40, 34])
    wire = np.array([96, 70, 58])
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    arr[:, :, :3] = wire
    # siatka: druty co 10 cm
    step = int(round(0.10 * px_per_m))
    for k in range(0, W, step):   # 2 px (~2 cm), żeby druty nie znikały w mipmapach przy alpha test
        arr[:, k:k + 2, 3] = 255
        arr[k:k + 2, :, 3] = 255
    # pełny panel blachy u dołu z rdzawymi zaciekami
    panel_top = H - int(0.9 * px_per_m)
    rng = np.random.default_rng(7)
    rust = np.clip(np.array([92, 52, 36]) + rng.normal(0, 9, (H - panel_top, W, 1)), 0, 255)
    streaks = (rng.random(W) < 0.08)[None, :, None] * np.linspace(0, 25, H - panel_top)[:, None, None]
    arr[panel_top:, :, :3] = np.clip(rust - streaks, 0, 255).astype(np.uint8)
    arr[panel_top:, :, 3] = 255
    # rama: górna poręcz, rygiel nad panelem, słupki na krańcach przęsła
    for (y0, y1) in [(0, 7), (panel_top - 5, panel_top)]:
        arr[y0:y1, :, :3] = frame
        arr[y0:y1, :, 3] = 255
    for (x0, x1) in [(0, 6), (W - 6, W)]:
        arr[:, x0:x1, :3] = frame
        arr[:, x0:x1, 3] = 255
    save_path = os.path.join(TEXTURES_DIR, "fence_steel_red.png")
    Image.fromarray(arr, 'RGBA').save(save_path)
    print(f"Zapisano teksturę ogrodzenia: {save_path}")


def generate_facade_texture():
    """
    Elewacja bloku z wielkiej płyty (szarości, mnożona przez kolor bloku w materiale): kafel = 2 kondygnacje
    x 4 okna (5.6 m x 6 m), okna ciemne z lekkim zróżnicowaniem, pas podokienny jaśniejszy.
    """
    W = H = 256
    rng = np.random.default_rng(11)
    arr = np.full((H, W, 3), 225, dtype=np.float32)
    floor_h, win_w = H // 2, W // 4
    for f in range(2):
        for w in range(4):
            y0 = f * floor_h + int(floor_h * 0.28)
            y1 = f * floor_h + int(floor_h * 0.78)
            x0 = w * win_w + int(win_w * 0.18)
            x1 = w * win_w + int(win_w * 0.82)
            arr[y0:y1, x0:x1] = 70 + rng.uniform(-12, 25)
        arr[f * floor_h:f * floor_h + 4] = 190      # styk płyt
    arr += rng.normal(0, 4, arr.shape)
    save_path = os.path.join(TEXTURES_DIR, "facade_blok.png")
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGB').save(save_path)
    print(f"Zapisano teksturę elewacji bloku: {save_path}")


def generate_crown_ads_texture():
    """
    Atlas band reklamowych z korony łuku południowego (widok_na_zegar_u2.png, ok. 2010–2012):
    4 wiersze 1024 x 256 (proporcje 4:1 jak tablica 3.6 x 0.9 m), biały margines 8 px — tył i boki
    tablic próbkują lewy dolny róg wiersza.
    """
    W, H = 1024, 1024
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    M = 8
    rows = [
        ((250, 250, 250), [((60, 55), "KORPORACJA UBEZPIECZENIOWA", 50, (20, 30, 90)), ((300, 140), "FILAR SA", 72, (15, 15, 15))]),
        ((246, 246, 242), [((150, 60), "Nasze okna", 64, (200, 25, 30)), ((300, 140), "na Twój świat", 64, (40, 40, 40))]),
        ((22, 32, 70), [((40, 40), "RADIO TAXI", 70, (255, 255, 255)), ((520, 30), "MER-C", 96, (240, 140, 20)),
                        ((40, 150), "TEL. 650 50 50", 56, (255, 255, 255))]),
        ((250, 250, 250), [((260, 30), "OPOCZNO", 110, (200, 20, 30)), ((230, 160), "naturalna woda mineralna", 44, (60, 60, 60))]),
    ]
    for r, (bg, texts) in enumerate(rows):
        y0 = r * 256
        d.rectangle([M, y0 + M, W - M - 1, y0 + 256 - M - 1], fill=bg)
        if r == 1:
            d.ellipse([40, y0 + 70, 130, y0 + 160], fill=(30, 140, 60))
        for (x, y), text, size, color in texts:
            d.text((x, y0 + y), text, font=get_font(size), fill=color)
    save_path = os.path.join(TEXTURES_DIR, "ads_crown.png")
    img.save(save_path)
    print(f"Zapisano atlas band reklamowych: {save_path}")


# Tekstury ładowane bezpośrednio przez Three.js; reszta trafia do aplikacji wyłącznie w GLB
RUNTIME_TEXTURES = ["floodlight_glow.png"]


def sync_to_public():
    """Kopiuje do public/assets/textures tylko tekstury używane w runtime przez src/main.ts."""
    import shutil
    pub_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "public", "assets", "textures")
    os.makedirs(pub_dir, exist_ok=True)
    for name in RUNTIME_TEXTURES:
        shutil.copy2(os.path.join(TEXTURES_DIR, name), os.path.join(pub_dir, name))
    print(f"Zsynchronizowano tekstury runtime do: {pub_dir}")

if __name__ == "__main__":
    generate_pitch_texture()
    generate_fascia_banner()
    generate_clock_face()
    generate_fan_graffiti_banners()
    generate_scoreboard_textures()
    generate_przeplatanka_texture()
    generate_mural_texture()
    generate_block_graffiti_atlas()
    generate_corrugated_roof_textures()
    generate_floodlight_glow_sprite()
    generate_goal_net_texture()
    generate_ball_net_texture()
    generate_gate_mesh_texture()
    generate_entrance_textures()
    generate_fence_texture()
    generate_facade_texture()
    generate_crown_ads_texture()
    sync_to_public()
    print("Wszystkie tekstury wygenerowane i zsynchronizowane pomyślnie!")
