import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 400, 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (135, 206, 250)
GREEN = (34, 139, 34)
YELLOW = (255, 255, 0)


class Bird:
    def __init__(self):
        self.x = 80
        self.y = HEIGHT // 2
        self.velocity = 0
        self.gravity = 0.5
        self.jump_strength = -10
        self.size = 30

    def jump(self):
        self.velocity = self.jump_strength

    def update(self):
        self.velocity += self.gravity
        self.y += self.velocity

    def draw(self, screen):
        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), self.size // 2)

    def get_rect(self):
        return pygame.Rect(
            self.x - self.size // 2, self.y - self.size // 2, self.size, self.size
        )


class Pipe:
    def __init__(self, x, gap=200):
        self.x = x
        self.width = 70
        self.gap = gap
        self.top_height = random.randint(100, HEIGHT - self.gap - 100)
        self.speed = 3
        self.passed = False

    def update(self):
        self.x -= self.speed

    def draw(self, screen):
        # Top pipe
        pygame.draw.rect(screen, GREEN, (self.x, 0, self.width, self.top_height))
        # Bottom pipe
        pygame.draw.rect(
            screen,
            GREEN,
            (
                self.x,
                self.top_height + self.gap,
                self.width,
                HEIGHT - self.top_height - self.gap,
            ),
        )

    def collides_with(self, bird):
        bird_rect = bird.get_rect()
        top_pipe = pygame.Rect(self.x, 0, self.width, self.top_height)
        bottom_pipe = pygame.Rect(
            self.x,
            self.top_height + self.gap,
            self.width,
            HEIGHT - self.top_height - self.gap,
        )
        return bird_rect.colliderect(top_pipe) or bird_rect.colliderect(bottom_pipe)

    def off_screen(self):
        return self.x + self.width < 0


class FlappyBirdGame:
    def __init__(self, pipe_distance=300, pipe_gap=200, speed_increase_rate=0.0):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Flappy Bird - Q-Learning")
        self.clock = pygame.time.Clock()
        self.pipe_distance = pipe_distance  # Distance between pipes
        self.pipe_gap = pipe_gap  # Height of gap in pipes
        self.speed_increase_rate = (
            speed_increase_rate  # Speed increase per second (0 = no increase)
        )
        self.base_speed = 3  # Starting pipe speed
        self.reset()

    def reset(self):
        """Reset the game to initial state"""
        self.bird = Bird()
        self.pipes = [Pipe(WIDTH + 200, self.pipe_gap)]
        self.pipes[0].speed = self.base_speed
        self.score = 0
        self.game_over = False
        self.current_speed = self.base_speed
        self.frames_elapsed = 0  # Track time
        return self.get_state()

    def get_state(self):
        """
        Return the current game state for Q-learning.
        Returns a tuple of relevant features:
        - bird_y: Bird's y position
        - bird_velocity: Bird's velocity
        - next_pipe_x: Horizontal distance to next pipe
        - next_pipe_top: Height of top pipe opening
        - next_pipe_bottom: Height of bottom pipe opening
        """
        # Find the next pipe ahead of the bird
        next_pipe = None
        for pipe in self.pipes:
            if pipe.x + pipe.width > self.bird.x:
                next_pipe = pipe
                break

        if next_pipe:
            return (
                self.bird.y,
                self.bird.velocity,
                next_pipe.x - self.bird.x,
                next_pipe.top_height,
                next_pipe.top_height + next_pipe.gap,
            )
        else:
            return (self.bird.y, self.bird.velocity, WIDTH, HEIGHT // 2, HEIGHT)

    def step(self, action):
        """
        Execute one game step with the given action.
        action: 0 = do nothing, 1 = jump
        Returns: (next_state, reward, done)
        """
        # Process action
        if action == 1:
            self.bird.jump()

        # Update bird
        self.bird.update()

        # Increase frame counter and update speed based on time
        self.frames_elapsed += 1
        seconds_elapsed = self.frames_elapsed / FPS
        self.current_speed = self.base_speed + (
            seconds_elapsed * self.speed_increase_rate
        )

        # Update pipes
        for pipe in self.pipes:
            pipe.speed = self.current_speed
            pipe.update()

            # Check collision
            if pipe.collides_with(self.bird):
                self.game_over = True
                return self.get_state(), -1000, True

            # Check if passed pipe
            if not pipe.passed and pipe.x + pipe.width < self.bird.x:
                pipe.passed = True
                self.score += 1

        # Remove off-screen pipes
        self.pipes = [p for p in self.pipes if not p.off_screen()]

        # Add new pipes
        if len(self.pipes) == 0 or self.pipes[-1].x < WIDTH - self.pipe_distance:
            new_pipe = Pipe(WIDTH, self.pipe_gap)
            new_pipe.speed = self.current_speed
            self.pipes.append(new_pipe)

        # Check boundaries
        if self.bird.y > HEIGHT or self.bird.y < 0:
            self.game_over = True
            return self.get_state(), -1000, True

        # Small reward for staying alive
        reward = 1

        return self.get_state(), reward, False

    def render(self, show_game_over=False):
        """Render the game (optional, for visualization)"""
        self.screen.fill(BLUE)

        # Draw pipes
        for pipe in self.pipes:
            pipe.draw(self.screen)

        # Draw bird
        self.bird.draw(self.screen)

        # Draw score
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))

        # Draw game over text if needed
        if show_game_over:
            font = pygame.font.Font(None, 48)

            text = font.render("Game Over! Press SPACE", True, (255, 0, 0))
            text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
            self.screen.blit(text, text_rect)

            score_text = font.render(f"Final Score: {self.score}", True, (255, 0, 0))
            score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40))
            self.screen.blit(score_text, score_rect)

        pygame.display.flip()
        self.clock.tick(FPS)

    def play_human(self):
        """Play manually (for testing)"""
        running = True
        while running:
            action = 0  # Default: no jump

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        if self.game_over:
                            self.reset()
                        else:
                            action = 1

            if not self.game_over and running:
                _, _, done = self.step(action)

            self.render(show_game_over=self.game_over)

        pygame.quit()
        sys.exit()


# Example usage
if __name__ == "__main__":
    # Create game with custom settings
    # pipe_distance: horizontal distance between pipes (default 300)
    # pipe_gap: vertical gap height in pipes (default 200)
    # speed_increase_rate: speed increase per second (default 0.0 = no increase)
    #   Examples: 0.1 = gradual increase, 0.5 = faster increase, 0.0 = constant speed
    game = FlappyBirdGame(pipe_distance=300, pipe_gap=200, speed_increase_rate=0)

    # Play manually with spacebar
    print("Press SPACE to jump. Close window to quit.")
    print("Speed will gradually increase over time!")
    game.play_human()

    # For Q-learning, you would use something like:
    # state = game.reset()
    # while True:
    #     action = your_q_learning_agent.choose_action(state)
    #     next_state, reward, done = game.step(action)
    #     your_q_learning_agent.learn(state, action, reward, next_state, done)
    #     if done:
    #         state = game.reset()
    #     else:
    #         state = next_state
    #     game.render()  # Optional: visualize training
