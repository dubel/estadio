import os
import math
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

if __name__ == "__main__":
    generate_pitch_texture()
    generate_fascia_banner()
    generate_clock_face()
    generate_fan_graffiti_banners()
    print("Wszystkie tekstury wygenerowane pomyślnie!")
