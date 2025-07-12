import pygame
import random
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
from datetime import datetime

# Initialize
pygame.init()
WIDTH, HEIGHT = 640, 480
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Quiz Battle: Data Science Edition")
font = pygame.font.SysFont('Arial', 20)

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 200, 0)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)

# Game variables
SNAKE_SIZE = 20
clock = pygame.time.Clock()
speed = 10
learning_mode = False

data_log = []

# Load questions
df_all = pd.read_csv("questions.csv")

def choose_topic():
    # Load background image
    bg = pygame.image.load("bg.jpg")
    bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))

    # Topics from CSV
    topics = df_all['topic'].unique().tolist()
    selected = 0
    tips = [
        "💡 Tip: Use .fillna() to handle missing data in Pandas.",
        "📊 NumPy is 50x faster than Python loops!",
        "🧠 Data Cleaning is 80% of data science work.",
        "🎯 Accuracy = correct / total",
        "📌 Use .describe() to get quick stats."
    ]
    tip = random.choice(tips)

    running = True
    while running:
        win.blit(bg, (0, 0))  # Draw background

        # Title
        title_font = pygame.font.SysFont("Arial", 30, bold=True)
        title = title_font.render("🎯 Choose Your Topic", True, WHITE)
        win.blit(title, (WIDTH // 2 - title.get_width() // 2, 30))

        # Tips
        tip_font = pygame.font.SysFont("Arial", 18)
        tip_text = tip_font.render(tip, True, (255, 255, 100))
        win.blit(tip_text, (40, HEIGHT - 40))

        # Topic buttons
        for i, topic in enumerate(topics):
            is_selected = (i == selected)
            color = (0, 102, 204) if is_selected else (200, 200, 200)
            rect = pygame.Rect(150, 100 + i * 50, 340, 40)
            pygame.draw.rect(win, color, rect, border_radius=10)
            topic_text = font.render(topic, True, WHITE if is_selected else BLACK)
            win.blit(topic_text, (rect.x + 20, rect.y + 10))

            # Arrow selector
            if is_selected:
                win.blit(font.render("➤", True, WHITE), (120, rect.y + 10))

        pygame.display.update()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(topics)
                elif e.key == pygame.K_UP:
                    selected = (selected - 1) % len(topics)
                elif e.key == pygame.K_RETURN:
                    return topics[selected]

def ask_question(df_questions):
    if df_questions.empty:
        print("⚠️ No questions found! Returning dummy question.")
        return False, "No Question Available", None, "No Answer", 0  # safe defaults

    try:
        question_data = df_questions.sample().iloc[0]
    except ValueError:
        print("⚠️ Sampling error: DataFrame is empty!")
        return False, "No Question Available", None, "No Answer", 0

    question = question_data['question']
    options = [question_data[f'option{i}'] for i in range(1, 5)]
    answer = question_data['answer']

    start_ticks = pygame.time.get_ticks()
    selected = None
    time_limit = 10000  

    while True:
        win.fill(WHITE)
        win.blit(font.render("QUIZ TIME!", True, RED), (220, 30))
        win.blit(font.render(question, True, BLACK), (50, 70))
        for i, opt in enumerate(options):
            win.blit(font.render(f"{i+1}. {opt}", True, BLACK), (80, 110 + i*30))

        seconds = (pygame.time.get_ticks() - start_ticks)
        timer = max(0, (time_limit - seconds)//1000)
        pygame.draw.rect(win, RED, (500, 20, (time_limit - seconds)//20, 10))
        win.blit(font.render(f"Timer: {timer}s", True, BLACK), (500, 35))
        pygame.display.update()

        if seconds >= time_limit:
            return False, question, None, answer, 10

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); exit()
            if e.type == pygame.KEYDOWN:
                if pygame.K_1 <= e.key <= pygame.K_4:
                    selected = options[e.key - pygame.K_1]
                    time_taken = seconds / 1000
                    return selected == answer, question, selected, answer, time_taken

def show_results():
    if not data_log:
        return
    df = pd.DataFrame(data_log)
    correct = df['correct'].sum()
    total = len(df)
    accuracy = correct / total * 100

    # Save to CSV
    df.to_csv("game_history.csv", mode='a', index=False)

    # Plot
    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1)
    # Convert RGB 0-255 to 0-1 for matplotlib
    green_norm = tuple(c/255 for c in GREEN)
    red_norm = tuple(c/255 for c in RED)
    plt.pie([correct, total-correct], labels=['Correct', 'Wrong'], autopct='%1.1f%%', colors=[green_norm, red_norm])

    plt.title("Accuracy")

    plt.subplot(1, 2, 2)
    plt.plot(df['time'], marker='o', label='Time per Question (s)')
    plt.title("Time per Question")
    plt.xlabel("Question")
    plt.ylabel("Seconds")
    plt.legend()

    plt.suptitle(f"Final Score: {df['score'].sum()} | Accuracy: {accuracy:.1f}%")
    plt.tight_layout()
    plt.show()

def game_loop():
    global learning_mode
    topic = choose_topic()
    df_topic = df_all[df_all['topic'] == topic]
    game_over = False
    x, y = WIDTH//2, HEIGHT//2
    dx, dy = 0, 0
    snake = []
    length = 1
    score = 0
    accuracy = 1.0

    apple_x = random.randint(0, WIDTH//SNAKE_SIZE - 1) * SNAKE_SIZE
    apple_y = random.randint(0, HEIGHT//SNAKE_SIZE - 1) * SNAKE_SIZE

    while not game_over:
        win.fill(WHITE)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_LEFT: dx, dy = -SNAKE_SIZE, 0
                elif e.key == pygame.K_RIGHT: dx, dy = SNAKE_SIZE, 0
                elif e.key == pygame.K_UP: dx, dy = 0, -SNAKE_SIZE
                elif e.key == pygame.K_DOWN: dx, dy = 0, SNAKE_SIZE
                elif e.key == pygame.K_l: learning_mode = not learning_mode

        x += dx
        y += dy

        if x < 0 or x >= WIDTH or y < 0 or y >= HEIGHT:
            if not learning_mode:
                game_over = True

        head = [x, y]
        snake.append(head)
        if len(snake) > length:
            del snake[0]

        if head in snake[:-1] and not learning_mode:
            game_over = True

        pygame.draw.rect(win, RED, [apple_x, apple_y, SNAKE_SIZE, SNAKE_SIZE])
        for s in snake:
            pygame.draw.rect(win, GREEN, [s[0], s[1], SNAKE_SIZE, SNAKE_SIZE])

        if x == apple_x and y == apple_y:
            # Difficulty-based selection
            if accuracy < 0.5:
                df_filtered = df_topic[df_topic['difficulty'] == 'easy']
            elif accuracy < 0.8:
                df_filtered = df_topic[df_topic['difficulty'] == 'medium']
            else:
                df_filtered = df_topic[df_topic['difficulty'] == 'hard']

            # ✅ Fallback if no question found at this difficulty
            if df_filtered.empty:
                print(f"⚠️ No questions for {topic} at this difficulty. Showing random question instead.")
                df_filtered = df_topic.copy()

            correct, question, selected, answer, time_taken = ask_question(df_filtered)
            # Remove the asked question to avoid repetition
            df_topic = df_topic[df_topic['question'] != question]
            if correct:
                score += 10
                length += 1
            else:
                game_over = True 
                
            data_log.append({
                'question': question,
                'selected': selected,
                'correct': correct,
                'answer': answer,
                'time': round(time_taken, 2),
                'score': score,
                'timestamp': datetime.now().isoformat()
            })

            accuracy = np.mean([1 if d['correct'] else 0 for d in data_log])

            apple_x = random.randint(0, WIDTH//SNAKE_SIZE - 1) * SNAKE_SIZE
            apple_y = random.randint(0, HEIGHT//SNAKE_SIZE - 1) * SNAKE_SIZE

        win.blit(font.render(f"Score: {score}", True, BLACK), (10, 10))
        win.blit(font.render(f"Accuracy: {accuracy*100:.1f}%", True, BLACK), (10, 30))
        win.blit(font.render(f"Learning Mode: {'ON' if learning_mode else 'OFF'}", True, BLUE), (10, 50))

        pygame.display.update()
        clock.tick(speed)

    show_results()

game_loop()
