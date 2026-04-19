import pygame
import random
import sys
import os

pygame.init()
pygame.mixer.init()

# ------------------------
# SETUP
# ------------------------
WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Galaxy Attack PRO MAX")

clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 24)
big_font = pygame.font.SysFont("arial", 60)

# ------------------------
# LOAD SOUND
# ------------------------
shoot_sound = pygame.mixer.Sound("sounds/shoot.wav")
explosion_sound = pygame.mixer.Sound("sounds/explosion.wav")

# ------------------------
# COLORS
# ------------------------
WHITE = (255,255,255)
RED = (255,60,60)
GREEN = (50,255,100)
BLUE = (50,150,255)
YELLOW = (255,255,0)
PURPLE = (180,0,255)
BLACK = (5,5,20)
ORANGE = (255,150,0)
CYAN = (0,255,255)

# ------------------------
# HIGHSCORE
# ------------------------
HIGHSCORE_FILE = "highscore.txt"

def load_highscore():
    if not os.path.exists(HIGHSCORE_FILE):
        with open(HIGHSCORE_FILE, "w") as f:
            f.write("0")
        return 0
    try:
        with open(HIGHSCORE_FILE, "r") as f:
            return int(f.read())
    except:
        return 0

def save_highscore(score):
    if score > load_highscore():
        with open(HIGHSCORE_FILE, "w") as f:
            f.write(str(score))

highscore = load_highscore()

# ------------------------
# PLAYER + UPGRADES
# ------------------------
player = pygame.Rect(WIDTH//2 - 25, HEIGHT - 70, 50, 50)

base_speed = 6
speed_level = 0

fire_rate_level = 0
damage_level = 1

lives = 3
shield = False

def get_player_speed():
    return base_speed + speed_level * 2

def get_cooldown():
    return max(5, 15 - fire_rate_level * 2)

# ------------------------
# POWERUPS
# ------------------------
powerups = []

# ------------------------
# BULLETS
# ------------------------
bullets = []
bullet_speed = 10
shoot_cooldown = 0

# ------------------------
# ALIENS
# ------------------------
aliens = []
spawn_timer = 0

# ------------------------
# BOSS
# ------------------------
boss = None
boss_health = 0
boss_active = False
boss_direction = 1

# ------------------------
# EXPLOSIONS
# ------------------------
explosions = []

# ------------------------
# LEVEL
# ------------------------
score = 0
level = 1
aliens_killed = 0
aliens_needed = 10

def start_level(lvl):
    global aliens_needed, boss_health
    aliens_needed = 10 + lvl * 5
    boss_health = 80 + lvl * 30

start_level(level)

# ------------------------
# DROP SYSTEM
# ------------------------
def drop_powerup(x, y):
    power_type = random.choice(["rapid", "speed", "shield", "upgrade"])
    powerups.append([x, y, power_type])

# ------------------------
# GAME LOOP
# ------------------------
running = True
while running:
    clock.tick(60)
    screen.fill(BLACK)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    # MOVEMENT
    player_speed = get_player_speed()
    if keys[pygame.K_a] and player.left > 0:
        player.x -= player_speed
    if keys[pygame.K_d] and player.right < WIDTH:
        player.x += player_speed

    # SHOOT
    if shoot_cooldown > 0:
        shoot_cooldown -= 1

    if keys[pygame.K_w] and shoot_cooldown == 0:
        bullets.append(pygame.Rect(player.centerx - 4, player.top, 8, 20))
        shoot_sound.play()
        shoot_cooldown = get_cooldown()

    # SPAWN
    if not boss_active:
        spawn_timer += 1
        if spawn_timer > max(20, 60 - level*5):
            aliens.append(pygame.Rect(random.randint(0, WIDTH-40), -40, 40, 40))
            spawn_timer = 0

    # BULLETS
    for bullet in bullets[:]:
        bullet.y -= bullet_speed
        if bullet.bottom < 0:
            bullets.remove(bullet)

    # ALIENS
    for alien in aliens[:]:
        alien.y += 2 + level

        if alien.top > HEIGHT:
            aliens.remove(alien)
            if not shield:
                lives -= 1

        for bullet in bullets[:]:
            if alien.colliderect(bullet):
                aliens.remove(alien)
                bullets.remove(bullet)
                explosion_sound.play()
                explosions.append([alien.centerx, alien.centery, 10])
                score += 1
                aliens_killed += 1

                if random.random() < 0.3:
                    drop_powerup(alien.centerx, alien.centery)
                break

    # POWERUPS
    for power in powerups[:]:
        power[1] += 3
        rect = pygame.Rect(power[0], power[1], 20, 20)

        if rect.colliderect(player):
            if power[2] == "speed":
                speed_level += 1
            elif power[2] == "rapid":
                fire_rate_level += 1
            elif power[2] == "upgrade":
                damage_level += 1
            elif power[2] == "shield":
                shield = True

            powerups.remove(power)

    # LEVEL
    if aliens_killed >= aliens_needed and not boss_active:
        if level % 3 == 0:
            boss_active = True
            boss = pygame.Rect(WIDTH//2 - 100, 50, 200, 100)
        else:
            level += 1
            aliens_killed = 0
            start_level(level)

    # BOSS
    if boss_active and boss:
        boss.x += 4 * boss_direction
        if boss.right >= WIDTH or boss.left <= 0:
            boss_direction *= -1

        for bullet in bullets[:]:
            if boss.colliderect(bullet):
                bullets.remove(bullet)
                boss_health -= damage_level

        if boss_health <= 0:
            explosion_sound.play()

            for _ in range(random.randint(2, 4)):
                drop_powerup(
                    boss.centerx + random.randint(-60, 60),
                    boss.centery + random.randint(-30, 30)
                )

            level += 1
            aliens_killed = 0
            boss_active = False
            start_level(level)

    # GAME OVER
    if lives <= 0:
        save_highscore(score)
        game_over = big_font.render("GAME OVER", True, RED)
        screen.blit(game_over, (WIDTH//2 - 150, HEIGHT//2))
        pygame.display.flip()
        pygame.time.wait(4000)
        running = False

    # DRAW
    pygame.draw.rect(screen, BLUE, player)

    if shield:
        pygame.draw.circle(screen, CYAN, player.center, 40, 2)

    for bullet in bullets:
        pygame.draw.rect(screen, YELLOW, bullet)

    for alien in aliens:
        pygame.draw.rect(screen, PURPLE, alien)

    for power in powerups:
        color = GREEN if power[2]=="rapid" else YELLOW if power[2]=="speed" else CYAN if power[2]=="shield" else ORANGE
        pygame.draw.rect(screen, color, (power[0], power[1], 20, 20))

    if boss_active and boss:
        pygame.draw.rect(screen, RED, boss)
        screen.blit(font.render(f"Boss HP: {boss_health}", True, WHITE), (10,10))

    for explosion in explosions[:]:
        pygame.draw.circle(screen, ORANGE, (explosion[0], explosion[1]), explosion[2])
        explosion[2] += 2
        if explosion[2] > 30:
            explosions.remove(explosion)

    # UI
    screen.blit(font.render(f"Score: {score}", True, WHITE), (10,10))
    screen.blit(font.render(f"Level: {level}", True, GREEN), (10,40))
    screen.blit(font.render(f"Lives: {lives}", True, WHITE), (10,70))
    screen.blit(font.render(f"Highscore: {highscore}", True, ORANGE), (10,100))

    pygame.display.flip()

pygame.quit()
sys.exit()