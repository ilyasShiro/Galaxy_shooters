import pygame
import random
import math
import sys
import array as arr

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

WIDTH, HEIGHT = 900, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Galaxy Attack")
clock = pygame.time.Clock()

font     = pygame.font.SysFont("arial", 22)
big_font = pygame.font.SysFont("arial", 52, bold=True)
med_font = pygame.font.SysFont("arial", 30, bold=True)
sml_font = pygame.font.SysFont("arial", 16)

BLACK   = (10,  10,  25)
WHITE   = (255, 255, 255)
BLUE    = (30,  100, 255)
LBLUE   = (140, 200, 255)
PURPLE  = (180,  50, 255)
RED     = (255,  60,  60)
GREEN   = (50,  220,  80)
YELLOW  = (255, 230,   0)
CYAN    = (0,   240, 240)
ORANGE  = (255, 140,   0)
PINK    = (255,  80, 160)
DKRED   = (120,   0,   0)
DKGREEN = (20,  100,  30)
MAGENTA = (255,   0, 200)
TEAL    = (0,   200, 160)

# ── Sound ──────────────────────────────────────────────
SAMPLE_RATE = 44100

def _build_sound(samples):
    stereo = arr.array('h')
    for s in samples:
        stereo.append(s); stereo.append(s)
    return pygame.mixer.Sound(buffer=stereo)

def make_tone(freq, duration, vol=0.3, wave="square"):
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        x = i / SAMPLE_RATE
        if wave == "square":   v = 1 if math.sin(2*math.pi*freq*x) >= 0 else -1
        elif wave == "sawtooth": v = 2*(freq*x % 1) - 1
        else:                  v = math.sin(2*math.pi*freq*x)
        samples.append(int(32767 * vol * v))
    fade = max(1, n // 8)
    for i in range(fade): samples[n-1-i] = int(samples[n-1-i] * (i/fade))
    return _build_sound(samples)

def make_noise(duration, vol=0.2):
    n = int(SAMPLE_RATE * duration)
    samples = [int(32767 * vol * (random.random()*2-1)) for _ in range(n)]
    fade = max(1, n // 4)
    for i in range(fade): samples[n-1-i] = int(samples[n-1-i] * (i/fade))
    return _build_sound(samples)

try:
    SFX_SHOOT    = make_tone(880, 0.08, 0.18, "square")
    SFX_EXPLODE  = make_noise(0.18, 0.22)
    SFX_BOSS_HIT = make_tone(160, 0.09, 0.14, "sawtooth")
    SFX_POWERUP  = make_tone(660, 0.14, 0.18, "sine")
    SFX_HIT      = make_noise(0.12, 0.25)
    SFX_LEVELUP  = make_tone(440, 0.22, 0.18, "sine")
    SOUNDS_OK = True
except Exception:
    SOUNDS_OK = False

def play(sfx):
    if SOUNDS_OK:
        try: sfx.play()
        except: pass

# ── Highscore ──────────────────────────────────────────
SAVE_FILE = "highscore.txt"
def load_highscore():
    try:
        with open(SAVE_FILE) as f: return int(f.read())
    except: return 0
def save_highscore(s):
    if s > load_highscore():
        with open(SAVE_FILE, "w") as f: f.write(str(s))

# ── Particles ──────────────────────────────────────────
particles = []

def burst(x, y, color, count=14, force=4):
    for _ in range(count):
        angle = random.uniform(0, math.pi*2)
        spd   = random.uniform(1, force)
        particles.append({"x":x,"y":y,"vx":math.cos(angle)*spd,"vy":math.sin(angle)*spd,
                           "life":1.0,"color":color,"size":random.uniform(2,5)})

def update_particles():
    for p in particles:
        p["x"] += p["vx"]; p["y"] += p["vy"]; p["vy"] += 0.12; p["life"] -= 0.035
    particles[:] = [p for p in particles if p["life"] > 0]

def draw_particles(surf):
    for p in particles:
        r = int(p["size"] * p["life"])
        if r < 1: continue
        pygame.draw.circle(surf, tuple(min(255,v) for v in p["color"]),
                           (int(p["x"]),int(p["y"])), r)

# ── Draw helpers ───────────────────────────────────────
def draw_ship(surf, x, y, shield, shield_timer=0):
    pygame.draw.ellipse(surf, (30,80,200),   pygame.Rect(x+16,y+46,22,12))
    pygame.draw.ellipse(surf, (100,180,255), pygame.Rect(x+20,y+46,14,8))
    pygame.draw.polygon(surf, BLUE,  [(x+27,y),(x+54,y+48),(x,y+48)])
    pygame.draw.polygon(surf, LBLUE, [(x+27,y+6),(x+44,y+44),(x+10,y+44)])
    pygame.draw.ellipse(surf, CYAN,  pygame.Rect(x+19,y+14,18,22))
    pygame.draw.ellipse(surf, WHITE, pygame.Rect(x+22,y+16,10,12))
    pygame.draw.polygon(surf, (0,60,180), [(x,y+44),(x-14,y+58),(x+12,y+48)])
    pygame.draw.polygon(surf, (0,60,180), [(x+54,y+44),(x+68,y+58),(x+42,y+48)])
    if shield:
        pygame.draw.circle(surf, CYAN,      (x+27,y+26), 40, 2)
        pygame.draw.circle(surf, (0,180,180),(x+27,y+26), 38, 1)

def draw_alien_a(surf, x, y, tick):
    pygame.draw.ellipse(surf, PURPLE,      pygame.Rect(x+2,y+10,32,16))
    pygame.draw.ellipse(surf, (200,80,255),pygame.Rect(x+8,y+4,20,14))
    pygame.draw.circle(surf, YELLOW,(x+13,y+12),4)
    pygame.draw.circle(surf, YELLOW,(x+23,y+12),4)
    pygame.draw.circle(surf, BLACK, (x+13,y+12),2)
    pygame.draw.circle(surf, BLACK, (x+23,y+12),2)
    for i in range(5):
        ox   = x+6+i*6
        wave = int(math.sin(tick/20+i)*4)
        pygame.draw.line(surf,(180,50,220),(ox,y+24),(ox+wave,y+34),2)

def draw_alien_b(surf, x, y, tick):
    pygame.draw.polygon(surf, RED,    [(x+18,y+2),(x+34,y+28),(x+18,y+22),(x+2,y+28)])
    pygame.draw.ellipse(surf, ORANGE, pygame.Rect(x+10,y+14,16,12))

def draw_alien_c(surf, x, y, tick):
    pygame.draw.polygon(surf, DKGREEN,
        [(x+18,y+2),(x+32,y+8),(x+32,y+22),(x+18,y+28),(x+4,y+22),(x+4,y+8)])
    pygame.draw.polygon(surf, GREEN,
        [(x+18,y+7),(x+27,y+11),(x+27,y+19),(x+18,y+23),(x+9,y+19),(x+9,y+11)])
    pygame.draw.circle(surf,(150,255,150),(x+18,y+15),5)

def draw_boss(surf, bx, by, bw, bh, hp, max_hp, phase=1):
    hp_pct   = max(0, hp/max_hp)
    glow_col = (255,0,0) if phase==3 else ((200,80,0) if phase==2 else (180,0,0))
    glow     = pygame.Surface((bw+60,bh+60), pygame.SRCALPHA)
    pulse_a  = int(40+abs(math.sin(pygame.time.get_ticks()/300))*60)
    pygame.draw.ellipse(glow, (*glow_col, pulse_a), glow.get_rect())
    surf.blit(glow, (bx-30,by-30))
    hull_col = (220,0,0) if phase==3 else (180,20,20)
    pygame.draw.rect(surf, DKRED,     (bx,by,bw,bh))
    pygame.draw.rect(surf, hull_col,  (bx+8,by+8,bw-16,bh-16))
    seg_w = (bw-24)//4
    for i in range(4):
        c = (220+random.randint(0,35),20,20) if phase==3 else (180,20,20)
        pygame.draw.rect(surf, c, (bx+12+i*(seg_w+1),by+12,seg_w,bh-24))
    turret_col = (220,60,0) if phase==3 else (180,40,0)
    for tx in [bx+30, bx+bw//2-15, bx+bw-60]:
        pygame.draw.circle(surf, turret_col,  (tx+15,by+bh//2), 16)
        pygame.draw.circle(surf, (240,80,0),  (tx+15,by+bh//2), 9)
        pygame.draw.circle(surf, YELLOW,      (tx+15,by+bh//2), 4)
    pygame.draw.rect(surf, (30,30,30), (bx,by-20,bw,12))
    fill = int(bw*hp_pct)
    col  = GREEN if hp_pct>0.55 else (ORANGE if hp_pct>0.25 else RED)
    pygame.draw.rect(surf, col, (bx,by-20,fill,12))
    phase_str = ["","PHASE 1","⚡ PHASE 2","🔥 RAGE"][phase]
    lbl = font.render(f"BOSS  {int(hp)}/{max_hp}  {phase_str}", True, WHITE)
    surf.blit(lbl, (bx+bw//2-lbl.get_width()//2, by-20))

# ── Powerups  (NO bounce) ──────────────────────────────
PW_KINDS = ["speed","fire","damage","life","shield","spread","size"]

def pw_color(kind):
    return {"speed":CYAN,"fire":YELLOW,"damage":ORANGE,"life":GREEN,
            "shield":WHITE,"spread":PINK,"size":TEAL}.get(kind,WHITE)

def pw_letter(kind):
    return {"speed":"S","fire":"F","damage":"D","life":"♥",
            "shield":"Sh","spread":"Sp","size":"Sz"}.get(kind,"?")

def draw_powerup(surf, p, tick, player_rect):
    x,y,kind = int(p["x"]),int(p["y"]),p["kind"]
    col = pw_color(kind)
    px,py = player_rect.centerx, player_rect.centery
    dist  = math.hypot(px-x,py-y)
    if dist < 220:
        alpha = int(max(0,120*(1-dist/220)))
        beam  = pygame.Surface((WIDTH,HEIGHT), pygame.SRCALPHA)
        pygame.draw.line(beam, (*col,alpha),(x,y),(px,py),2)
        surf.blit(beam,(0,0))
    pygame.draw.circle(surf, col,   (x,y), 12)
    pygame.draw.circle(surf, WHITE, (x,y), 6)
    letter = sml_font.render(pw_letter(kind), True, BLACK)
    surf.blit(letter,(x-letter.get_width()//2, y-letter.get_height()//2))
    ring_r = 14+int(math.sin(tick/12)*3)
    pygame.draw.circle(surf, col, (x,y), ring_r, 1)

def draw_bullet(surf, b):
    pygame.draw.rect(surf, b["color"], b["rect"])
    pygame.draw.rect(surf, WHITE, (b["rect"].x+1, b["rect"].y, max(1,b["rect"].width-2), min(6,b["rect"].height//3)))

def draw_boss_bullet(surf, r):
    pygame.draw.rect(surf, ORANGE, r)
    pygame.draw.rect(surf, YELLOW, (r.x+2,r.y,r.width-4,6))

# ── Stars ──────────────────────────────────────────────
stars = [{"x":random.randint(0,WIDTH),"y":random.randint(0,HEIGHT),
          "s":random.uniform(0.5,2),"sp":random.uniform(0.2,0.9)} for _ in range(120)]

def draw_stars(surf):
    for s in stars:
        pygame.draw.circle(surf, WHITE, (int(s["x"]),int(s["y"])), max(1,int(s["s"])))
        s["y"] += s["sp"]
        if s["y"] > HEIGHT: s["y"] = 0

shake_amt = 0
def shake(amt):
    global shake_amt
    shake_amt = max(shake_amt, amt)

# ── Bullet builder ─────────────────────────────────────
def make_bullets(cx, cy, spread_lvl, dmg, size_lvl):
    out   = []
    shots = 1 + spread_lvl
    bw    = 6  + size_lvl * 3
    bh    = 18 + size_lvl * 4
    speed = 12 + size_lvl * 0.5
    total_angle = min(80, spread_lvl * 9)
    for i in range(shots):
        angle_deg = 0 if shots==1 else -total_angle/2 + i*(total_angle/(shots-1))
        rad = math.radians(angle_deg - 90)
        vx  = math.cos(rad)*speed
        vy  = math.sin(rad)*speed
        col = TEAL if size_lvl>=5 else (PINK if spread_lvl>3 else YELLOW)
        out.append({"rect":pygame.Rect(cx-bw//2,cy,bw,bh),
                    "vx":vx,"vy":vy,"color":col,"dmg":dmg})
    return out

# ── HUD upgrade bar ────────────────────────────────────
def draw_upgrade_bar(surf):
    upgrades = [
        ("SPD",  speed_up,   6, CYAN),
        ("FIRE", fire_up,    7, YELLOW),
        ("DMG",  dmg_up-1,   3, ORANGE),
        ("SPRD", spread_up,  5, PINK),
        ("SIZE", size_up,    4, TEAL),
    ]
    bx,by = WIDTH-185, 6
    for name,lvl,cap,col in upgrades:
        surf.blit(sml_font.render(name,True,(180,180,200)),(bx,by))
        for i in range(cap):
            pip = WHITE if (i<lvl and lvl>=cap) else (col if i<lvl else (35,35,55))
            pygame.draw.rect(surf, pip, (bx+46+i*13,by+2,10,10), 0 if i<lvl else 1)
        by += 17

# ── Game state ─────────────────────────────────────────
def reset_game():
    global score,level,lives,kills,kills_needed
    global speed_up,fire_up,dmg_up,shield,shield_timer,spread_up,size_up
    global bullets,aliens,boss_bullets,powerups,particles
    global spawn_timer,shoot_timer,boss_shoot_timer
    global boss,boss_hp,boss_active,boss_dir,boss_max_hp
    global shake_amt,tick,flash_msg,flash_alpha

    score=0; level=1; lives=3; kills=0; kills_needed=40
    speed_up=0; fire_up=0; dmg_up=1; shield=False; shield_timer=0
    spread_up=0; size_up=0
    bullets=[]; aliens=[]; boss_bullets=[]; powerups=[]; particles=[]
    spawn_timer=0; shoot_timer=0; boss_shoot_timer=0
    boss=None; boss_hp=0; boss_active=False; boss_dir=1; boss_max_hp=0
    shake_amt=0; tick=0; flash_msg=None; flash_alpha=0.0
    player_rect.x = WIDTH//2-27
    player_rect.y = HEIGHT-90

highscore   = load_highscore()
player_rect = pygame.Rect(WIDTH//2-27, HEIGHT-90, 54, 48)
reset_game()

def player_speed(): return 10 + speed_up * 1.2   # meaningful but not overwhelming
def shoot_delay():  return max(5, 16-fire_up*1.1) # floor of 5 — can't spam endlessly

def drop_powerup(x, y):
    # Mild early bias toward damage/fire, but not overwhelming
    if dmg_up < 3:
        pool = ["damage","damage","fire","speed"] + PW_KINDS
    else:
        pool = PW_KINDS
    powerups.append({"x":float(x),"y":float(y),"kind":random.choice(pool),
                     "vx":random.uniform(-0.5,0.5),"vy":1.5})

def spawn_boss():
    global boss,boss_hp,boss_active,boss_dir,boss_shoot_timer,boss_max_hp,kills,flash_msg,flash_alpha
    boss_active = True
    w = min(320, 220+level*10)
    boss = pygame.Rect(WIDTH//2-w//2, 60, w, 90)
    boss_max_hp = 150 + level*70  # scales much harder each level
    boss_hp = float(boss_max_hp)
    boss_shoot_timer = 0; kills = 0
    flash_msg = "⚠ BOSS INCOMING!"; flash_alpha = 1.0

def next_level():
    global kills_needed
    kills_needed = 40 + level*10   # level 2→60, level 3→70, level 4→80 …

# ── Main loop ──────────────────────────────────────────
running=True; game_over=False; flash_msg=None; flash_alpha=0.0; tick=0

while running:
    clock.tick(60)
    tick += 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if game_over and event.key in (pygame.K_ESCAPE,pygame.K_RETURN,pygame.K_SPACE):
                reset_game(); game_over=False; highscore=load_highscore()

    if game_over:
        screen.fill(BLACK); draw_stars(screen)
        screen.blit(big_font.render("GAME OVER",True,RED),
                    (WIDTH//2-big_font.size("GAME OVER")[0]//2, HEIGHT//2-70))
        screen.blit(med_font.render(f"Score: {score}   Best: {highscore}",True,WHITE),
                    (WIDTH//2-med_font.size(f"Score: {score}   Best: {highscore}")[0]//2, HEIGHT//2))
        screen.blit(font.render("Press Space or Enter to restart",True,(170,170,200)),
                    (WIDTH//2-font.size("Press Space or Enter to restart")[0]//2, HEIGHT//2+50))
        pygame.display.flip(); continue

    keys = pygame.key.get_pressed()

    # ── Move ──
    ps = player_speed()
    if (keys[pygame.K_LEFT]  or keys[pygame.K_a]) and player_rect.left   > 0:      player_rect.x -= ps
    if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and player_rect.right  < WIDTH:   player_rect.x += ps
    if (keys[pygame.K_UP]    or keys[pygame.K_w]) and player_rect.top    > HEIGHT//2: player_rect.y -= ps
    if (keys[pygame.K_DOWN]  or keys[pygame.K_s]) and player_rect.bottom < HEIGHT:  player_rect.y += ps

    # ── Shoot (hold space) ──
    if shoot_timer > 0: shoot_timer -= 1
    if keys[pygame.K_SPACE] and shoot_timer == 0:
        bullets.extend(make_bullets(player_rect.centerx, player_rect.top,
                                    spread_up, dmg_up, size_up))
        shoot_timer = int(shoot_delay())
        play(SFX_SHOOT)

    # ── Shield countdown ──
    if shield and shield_timer > 0:
        shield_timer -= 1
        if shield_timer <= 0: shield = False

    # ── Spawn aliens ──
    if not boss_active:
        spawn_timer += 1
        spawn_rate = max(6, 34-level*3)
        if spawn_timer > spawn_rate:
            count = 1 if level<3 else (2 if level<6 else 3)
            for _ in range(count):
                atype = 0 if level<3 else random.randint(0, min(2,level-1))
                hp    = (3 if atype==2 else 1) + max(0,(level-2)//2)  # HP grows faster
                aliens.append({"rect":pygame.Rect(random.randint(0,WIDTH-36),-50-random.randint(0,80),36,30),
                                "hp":hp,"type":atype,"t":0,
                                "vx":random.uniform(-1,1)*(1+level*0.2),
                                "shoot_timer":random.randint(50,140)})  # tighter shoot window
            spawn_timer = 0

    # ── Alien shooting at level 3+ ──
    if level >= 3:
        for a in aliens:
            if "shoot_timer" in a:
                a["shoot_timer"] -= 1
                if a["shoot_timer"] <= 0:
                    boss_bullets.append({"rect":pygame.Rect(a["rect"].centerx-4,a["rect"].bottom,8,14),
                                         "vx":0,"vy":3.5+level*0.35})
                    a["shoot_timer"] = max(35, 160-level*14)

    # ── Move bullets ──
    alive = []
    for b in bullets:
        b["rect"].x += int(b["vx"]); b["rect"].y += int(b["vy"])
        if b["rect"].bottom>0 and b["rect"].top<HEIGHT and b["rect"].right>0 and b["rect"].left<WIDTH:
            alive.append(b)
    bullets = alive

    # ── Move & check aliens ──
    for a in aliens[:]:
        a["t"] += 1
        a["rect"].y += int(2.5+level*0.55)
        a["rect"].x += int(a["vx"]*(2.5 if a["type"]==1 else 1.0))
        if a["rect"].left<0 or a["rect"].right>WIDTH: a["vx"] *= -1
        if a["rect"].colliderect(player_rect):
            burst(a["rect"].centerx,a["rect"].centery,PINK,12,5)
            aliens.remove(a)
            if not shield: lives-=1; shake(8)
            continue
        if a["rect"].top > HEIGHT:
            aliens.remove(a)
            if not shield: lives-=1
            continue
        for b in bullets[:]:
            if a["rect"].colliderect(b["rect"]):
                bullets.remove(b); a["hp"] -= b["dmg"]
                burst(a["rect"].centerx,a["rect"].centery,GREEN if a["type"]==2 else PURPLE,8,3)
                if a["hp"] <= 0:
                    burst(a["rect"].centerx,a["rect"].centery,ORANGE,18,6)
                    shake(3); play(SFX_EXPLODE)
                    if random.random() < 0.40: drop_powerup(a["rect"].centerx,a["rect"].centery)
                    score += 30 if a["type"]==2 else 10
                    kills += 1; aliens.remove(a)
                break

    # ── Powerup physics ──
    for p in powerups[:]:
        dx = player_rect.centerx-p["x"]; dy = player_rect.centery-p["y"]
        dist = math.hypot(dx,dy) or 1
        homing_f = 0.55 if dist<180 else 0.18
        p["vx"] += (dx/dist)*homing_f; p["vy"] += (dy/dist)*homing_f
        spd = math.hypot(p["vx"],p["vy"])
        ms  = 14 if dist<80 else 8
        if spd>ms: p["vx"]=p["vx"]/spd*ms; p["vy"]=p["vy"]/spd*ms
        p["x"] += p["vx"]; p["y"] += p["vy"]
        pr = pygame.Rect(p["x"]-10,p["y"]-10,20,20)
        if pr.colliderect(player_rect):
            burst(int(p["x"]),int(p["y"]),pw_color(p["kind"]),16,4)
            k = p["kind"]
            if   k=="speed":   speed_up  = min(speed_up+1,  6)
            elif k=="fire":    fire_up   = min(fire_up+1,   7)
            elif k=="damage":  dmg_up    = min(dmg_up+1,    4)
            elif k=="life":    lives     = min(lives+1,      6)
            elif k=="shield":  shield=True; shield_timer=min(shield_timer+300, 300) # 5s, no stacking
            elif k=="spread":  spread_up = min(spread_up+1,  5)
            elif k=="size":    size_up   = min(size_up+1,    4)
            play(SFX_POWERUP)
            flash_msg=k.upper()+" UP!"; flash_alpha=1.0
            powerups.remove(p)
        elif p["y"]>HEIGHT+40 or p["x"]<-40 or p["x"]>WIDTH+40:
            powerups.remove(p)

    # ── Boss trigger ──
    if kills >= kills_needed and not boss_active:
        spawn_boss()

    # ── Boss logic ──
    if boss_active and boss:
        hp_pct = boss_hp/boss_max_hp
        phase  = 3 if hp_pct<0.25 else (2 if hp_pct<0.55 else 1)
        base_spd = 3.5 + level*0.6 + (phase-1)*2.5
        boss.x += int(base_spd*boss_dir)
        if phase==3: boss.y = 60+int(math.sin(tick/30)*40)
        if boss.left<=0 or boss.right>=WIDTH: boss_dir *= -1

        boss_shoot_timer += 1
        fire_rate = max(6, 40-level*4-(phase-1)*8)
        if boss_shoot_timer > fire_rate:
            cx,cy = boss.centerx, boss.bottom
            if phase==1:
                boss_bullets.append({"rect":pygame.Rect(cx-5,cy,10,22),"vx":0,"vy":7})
                boss_bullets.append({"rect":pygame.Rect(boss.x+20,cy,8,18),"vx":-1.5,"vy":6})
                boss_bullets.append({"rect":pygame.Rect(boss.right-28,cy,8,18),"vx":1.5,"vy":6})
            elif phase==2:
                dx=player_rect.centerx-cx; dy=player_rect.centery-cy
                d=math.hypot(dx,dy) or 1
                boss_bullets.append({"rect":pygame.Rect(cx-5,cy,10,22),"vx":(dx/d)*8,"vy":(dy/d)*8})
                for ang in [-30,30]:
                    r2=math.radians(90+ang)
                    boss_bullets.append({"rect":pygame.Rect(cx-4,cy,8,18),"vx":math.cos(r2)*6,"vy":math.sin(r2)*6})
                boss_bullets.append({"rect":pygame.Rect(boss.x+10,cy,8,18),"vx":-2,"vy":6})
                boss_bullets.append({"rect":pygame.Rect(boss.right-18,cy,8,18),"vx":2,"vy":6})
            elif phase==3:
                for i in range(8):
                    ang=math.radians(boss_shoot_timer*15+i*45); spd=6
                    boss_bullets.append({"rect":pygame.Rect(cx-4,cy,8,18),
                                         "vx":math.cos(ang)*spd,"vy":abs(math.sin(ang)*spd)+2})
                dx=player_rect.centerx-cx; dy=player_rect.centery-cy; d=math.hypot(dx,dy) or 1
                boss_bullets.append({"rect":pygame.Rect(cx-5,cy,10,22),"vx":(dx/d)*10,"vy":(dy/d)*10})
            boss_shoot_timer = 0

        for b in bullets[:]:
            if boss.colliderect(b["rect"]):
                bullets.remove(b); boss_hp -= b["dmg"]
                burst(b["rect"].x,boss.centery,ORANGE,6,3); play(SFX_BOSS_HIT); shake(2)
                if boss_hp <= 0:
                    for _ in range(8):
                        burst(random.randint(boss.x+20,boss.right-20),
                              random.randint(boss.y+10,boss.bottom-10),ORANGE,22,8)
                    play(SFX_LEVELUP); score += 300+level*80
                    for _ in range(random.randint(3,5)):
                        drop_powerup(random.randint(boss.x+20,boss.right-20),
                                     random.randint(boss.y+10,boss.bottom-10))
                    boss_active=False; boss=None; level+=1; next_level()
                    flash_msg=f"LEVEL {level}!"; flash_alpha=1.0
                break

    # ── Boss bullets ──
    for b in boss_bullets[:]:
        b["rect"].x += int(b["vx"]); b["rect"].y += int(b["vy"])
        r = b["rect"]
        if r.top>HEIGHT or r.bottom<0 or r.left>WIDTH or r.right<0:
            boss_bullets.remove(b); continue
        if r.colliderect(player_rect):
            boss_bullets.remove(b)
            if not shield: lives-=1; shake(10); play(SFX_HIT)
            burst(player_rect.centerx,player_rect.centery,RED,14,5)

    update_particles()

    ox=oy=0
    if shake_amt>0.5:
        ox=random.randint(-int(shake_amt),int(shake_amt))
        oy=random.randint(-int(shake_amt),int(shake_amt))
        shake_amt *= 0.82

    if flash_alpha>0: flash_alpha -= 0.012

    if lives<=0:
        save_highscore(score); highscore=load_highscore(); game_over=True; continue

    # ── Draw ──
    draw_surf = pygame.Surface((WIDTH,HEIGHT))
    draw_surf.fill(BLACK)
    draw_stars(draw_surf)

    if boss_active:
        hp_pct2   = boss_hp/boss_max_hp if boss_max_hp>0 else 1
        pp        = 3 if hp_pct2<0.25 else (2 if hp_pct2<0.55 else 1)
        pulse     = int(abs(math.sin(tick/max(5,22-pp*6)))*(20*pp))
        pygame.draw.rect(draw_surf,(pulse,0,0),(0,0,WIDTH,HEIGHT),0)

    for b in bullets:      draw_bullet(draw_surf, b)
    for a in aliens:
        r=a["rect"]
        if   a["type"]==0: draw_alien_a(draw_surf,r.x,r.y,a["t"])
        elif a["type"]==1: draw_alien_b(draw_surf,r.x,r.y,a["t"])
        else:              draw_alien_c(draw_surf,r.x,r.y,a["t"])
    if boss_active and boss:
        hp_pct3 = boss_hp/boss_max_hp
        bp = 3 if hp_pct3<0.25 else (2 if hp_pct3<0.55 else 1)
        draw_boss(draw_surf,boss.x,boss.y,boss.width,boss.height,boss_hp,boss_max_hp,bp)
    for b in boss_bullets: draw_boss_bullet(draw_surf, b["rect"])
    for p in powerups:     draw_powerup(draw_surf,p,tick,player_rect)
    draw_particles(draw_surf)
    draw_ship(draw_surf,player_rect.x,player_rect.y,shield,shield_timer)

    pygame.draw.rect(draw_surf,(0,0,0,180),(0,0,WIDTH,120))

    if not boss_active:
        pct = kills/kills_needed
        pygame.draw.rect(draw_surf,(40,20,80),(WIDTH//2-100,10,200,10))
        pygame.draw.rect(draw_surf,PURPLE,   (WIDTH//2-100,10,int(200*pct),10))
        lbl = font.render(f"BOSS IN {kills_needed-kills}",True,(200,150,255))
        draw_surf.blit(lbl,(WIDTH//2-lbl.get_width()//2,HEIGHT-28))

    draw_surf.blit(font.render(f"SCORE  {score}",True,(200,220,255)),(14,8))
    draw_surf.blit(font.render(f"LEVEL  {level}",True,GREEN),(14,30))
    draw_surf.blit(font.render("♥ "*lives or "--",True,RED),(14,52))
    draw_surf.blit(font.render(f"BEST  {highscore}",True,YELLOW),(14,74))

    draw_upgrade_bar(draw_surf)

    if shield:
        draw_surf.blit(font.render(f"SHIELD {shield_timer//60}s",True,CYAN),(WIDTH-185,104))

    shots_count = 1+spread_up
    shot_lbl = font.render(f"SHOTS {shots_count}: "+"| "*shots_count,True,PINK)
    draw_surf.blit(shot_lbl,(WIDTH//2-shot_lbl.get_width()//2,8))

    if flash_msg and flash_alpha>0:
        fm=med_font.render(flash_msg,True,YELLOW)
        fm.set_alpha(int(flash_alpha*255))
        draw_surf.blit(fm,(WIDTH//2-fm.get_width()//2,HEIGHT//2-20))

    screen.blit(draw_surf,(ox,oy))
    pygame.display.flip()

save_highscore(score)
pygame.quit()
sys.exit()
