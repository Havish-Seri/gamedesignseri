import cv2
import mediapipe as mp
import pygame
import numpy as np
import sys
import time

pygame.init()
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hand-Tracking Pong")
clock = pygame.time.Clock()

FONT = pygame.font.SysFont("Arial", 36)
SMALL = pygame.font.SysFont("Arial", 24)

PADDLE_W = 20
PADDLE_H = 140
BALL_SPEED = 25
SMOOTH = 0.65
GLOW = 12
SHAKE_INTENSITY = 20

BG_COLOR = (10, 10, 30)

SKINS = {
    "Neon Yellow": (255, 240, 100),
    "Gold": (255, 215, 0),
    "Ice Blue": (180, 230, 255),
    "Hot Pink": (255, 100, 180),
    "Retro Orange": (255, 160, 60),
}
skin_names = list(SKINS.keys())
selected_skin_index = 0

ice_platform = pygame.image.load("ice_platform.png").convert_alpha()
lava_platform = pygame.image.load("lava_platform.png").convert_alpha()
ice_platform = pygame.transform.scale(ice_platform, (PADDLE_W, PADDLE_H))
lava_platform = pygame.transform.scale(lava_platform, (PADDLE_W, PADDLE_H))

def draw_text_center(text, font, color, x, y):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(x, y))
    screen.blit(surf, rect)
    return rect

def fade_in(duration_ms=300):
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.fill((0, 0, 0))
    start = pygame.time.get_ticks()
    while True:
        t = pygame.time.get_ticks() - start
        alpha = max(0, 255 - int(255 * (t / max(1, duration_ms))))
        overlay.set_alpha(alpha)
        screen.fill((20, 20, 30))
        screen.blit(overlay, (0, 0))
        pygame.display.flip()
        clock.tick(60)
        if alpha <= 0:
            break

def draw_glow_circle(x, y, r, color):
    for i in range(GLOW, 0, -3):
        gl = (max(0, color[0]-i*2), max(0, color[1]-i), max(0, color[2]-i))
        pygame.draw.circle(screen, gl, (x, y), r + i)
    pygame.draw.circle(screen, color, (x, y), r)

def menu_loop():
    fade_in(250)
    while True:
        screen.fill((18, 18, 28))
        mx, my = pygame.mouse.get_pos()

        draw_text_center("HAND-TRACKING PONG", FONT, (235, 235, 245), WIDTH//2, 90)

        play_rect = pygame.Rect(WIDTH//2 - 150, 220, 300, 70)
        skins_rect = pygame.Rect(WIDTH//2 - 150, 320, 300, 70)
        quit_rect = pygame.Rect(WIDTH//2 - 150, 420, 300, 70)

        pygame.draw.rect(screen, (70,70,80) if play_rect.collidepoint(mx,my) else (50,50,60), play_rect, border_radius=14)
        pygame.draw.rect(screen, (70,70,80) if skins_rect.collidepoint(mx,my) else (50,50,60), skins_rect, border_radius=14)
        pygame.draw.rect(screen, (70,70,80) if quit_rect.collidepoint(mx,my) else (50,50,60), quit_rect, border_radius=14)

        draw_text_center("PLAY", FONT, (255,255,255), WIDTH//2, 255)
        draw_text_center("SKINS", FONT, (255,255,255), WIDTH//2, 355)
        draw_text_center("QUIT", FONT, (255,255,255), WIDTH//2, 455)

        preview_color = SKINS[skin_names[selected_skin_index]]
        pygame.draw.circle(screen, preview_color, (WIDTH//2, 160), 28)
        draw_text_center("Ball Preview", SMALL, (200,200,200), WIDTH//2, 200)

        pygame.display.flip()
        clock.tick(60)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN:
                if play_rect.collidepoint(e.pos):
                    return "play"
                if skins_rect.collidepoint(e.pos):
                    return "skins"
                if quit_rect.collidepoint(e.pos):
                    pygame.quit()
                    sys.exit()

def skins_loop():
    global selected_skin_index
    fade_in(200)
    while True:
        screen.fill((16, 18, 28))
        mx, my = pygame.mouse.get_pos()

        draw_text_center("SELECT BALL SKIN", FONT, (235,235,245), WIDTH//2, 80)

        current_name = skin_names[selected_skin_index]
        current_color = SKINS[current_name]
        pygame.draw.rect(screen, (40,40,50), (WIDTH//2 - 140, 140, 280, 220), border_radius=12)
        pygame.draw.circle(screen, current_color, (WIDTH//2, 250), 50)
        draw_text_center(current_name, SMALL, (220,220,220), WIDTH//2, 330)

        left_rect = pygame.Rect(WIDTH//2 - 240, 230, 50, 50)
        right_rect = pygame.Rect(WIDTH//2 + 190, 230, 50, 50)
        pygame.draw.rect(screen, (60,60,70), left_rect, border_radius=8)
        pygame.draw.rect(screen, (60,60,70), right_rect, border_radius=8)
        draw_text_center("<", FONT, (255,255,255), left_rect.centerx, left_rect.centery)
        draw_text_center(">", FONT, (255,255,255), right_rect.centerx, right_rect.centery)

        back_rect = pygame.Rect(WIDTH//2 - 80, 420, 160, 50)
        pygame.draw.rect(screen, (70,70,80), back_rect, border_radius=10)
        draw_text_center("BACK", SMALL, (255,255,255), WIDTH//2, 445)

        pygame.display.flip()
        clock.tick(60)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN:
                if left_rect.collidepoint(e.pos):
                    selected_skin_index = (selected_skin_index - 1) % len(skin_names)
                elif right_rect.collidepoint(e.pos):
                    selected_skin_index = (selected_skin_index + 1) % len(skin_names)
                elif back_rect.collidepoint(e.pos):
                    return "menu"

def run_game():
    cap = cv2.VideoCapture(0)
    hands = mp.solutions.hands.Hands(min_detection_confidence=0.5,
                                     min_tracking_confidence=0.5,
                                     max_num_hands=2)
    mp_draw = mp.solutions.drawing_utils

    p1_x = 40
    p2_x = WIDTH - 40 - PADDLE_W
    p1_y = HEIGHT//2
    p2_y = HEIGHT//2
    p1_target = p1_y
    p2_target = p2_y

    ball_x = WIDTH//2
    ball_y = HEIGHT//2
    ball_vx = BALL_SPEED
    ball_vy = int(BALL_SPEED * 0.6)

    s1 = 0
    s2 = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                hands.close()
                cv2.destroyAllWindows()
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                cap.release()
                hands.close()
                cv2.destroyAllWindows()
                return

        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        if results.multi_hand_landmarks:
            detected = []
            for h in results.multi_hand_landmarks:
                detected.append((h.landmark[9].x, h))
            detected.sort(key=lambda x: x[0])

            if len(detected) >= 1:
                p1_target = int(detected[0][1].landmark[9].y * HEIGHT - PADDLE_H/2)
                mp_draw.draw_landmarks(frame, detected[0][1], mp.solutions.hands.HAND_CONNECTIONS)
            if len(detected) >= 2:
                p2_target = int(detected[1][1].landmark[9].y * HEIGHT - PADDLE_H/2)
                mp_draw.draw_landmarks(frame, detected[1][1], mp.solutions.hands.HAND_CONNECTIONS)

        p1_y = int(p1_y * SMOOTH + p1_target * (1 - SMOOTH))
        p2_y = int(p2_y * SMOOTH + p2_target * (1 - SMOOTH))
        p1_y = max(0, min(HEIGHT - PADDLE_H, p1_y))
        p2_y = max(0, min(HEIGHT - PADDLE_H, p2_y))

        ball_x += ball_vx
        ball_y += ball_vy

        if ball_y <= 0 or ball_y >= HEIGHT:
            ball_vy *= -1

        hit = False
        if ball_x - 10 <= p1_x + PADDLE_W and p1_y <= ball_y <= p1_y + PADDLE_H:
            ball_vx = abs(ball_vx) + 0.6
            ball_vy += (ball_y - (p1_y + PADDLE_H/2)) / 15
            hit = True

        if ball_x + 10 >= p2_x and p2_y <= ball_y <= p2_y + PADDLE_H:
            ball_vx = -abs(ball_vx) - 0.6
            ball_vy += (ball_y - (p2_y + PADDLE_H/2)) / 15
            hit = True

        shake_x = np.random.randint(-SHAKE_INTENSITY, SHAKE_INTENSITY) if hit else 0
        shake_y = np.random.randint(-SHAKE_INTENSITY, SHAKE_INTENSITY) if hit else 0

        if ball_x < 0:
            s2 += 1
            ball_x, ball_y = WIDTH//2, HEIGHT//2
            ball_vx = BALL_SPEED
        if ball_x > WIDTH:
            s1 += 1
            ball_x, ball_y = WIDTH//2, HEIGHT//2
            ball_vx = -BALL_SPEED

        screen.fill(BG_COLOR)
        screen.blit(ice_platform, (p1_x + shake_x, p1_y + shake_y))
        screen.blit(lava_platform, (p2_x + shake_x, p2_y + shake_y))

        ball_color = SKINS[skin_names[selected_skin_index]]
        draw_glow_circle(int(ball_x) + shake_x, int(ball_y) + shake_y, 10, ball_color)

        score = FONT.render(f"{s1}   -   {s2}", True, (230,230,255))
        screen.blit(score, (WIDTH//2 - score.get_width()//2, 18))

        pygame.display.flip()
        clock.tick(60)

        cv2.imshow("Camera Feed", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    hands.close()
    cv2.destroyAllWindows()

def main():
    state = "menu"
    while True:
        if state == "menu":
            state = menu_loop()
        elif state == "skins":
            state = skins_loop()
        else:
            run_game()
            state = "menu"

if __name__ == "__main__":
    main()
