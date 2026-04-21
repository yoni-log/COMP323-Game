import sys

try:
    import pygame
except ModuleNotFoundError:
    print("Pygame is not installed.", file=sys.stderr)
    print("From this folder run:", file=sys.stderr)
    print("  python3 -m venv .venv", file=sys.stderr)
    print("  source .venv/bin/activate   # Windows: .venv\\Scripts\\activate", file=sys.stderr)
    print("  python3 -m pip install -r requirements.txt", file=sys.stderr)
    print("  python3 main.py", file=sys.stderr)
    sys.exit(1)

from src.game import Game
from src.game_config import FPS
from src.pregame import run_pregame_sequence


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Don't Crumble")

    run_pregame_sequence()
    pygame.event.clear()

    game = Game()
    clock = pygame.time.Clock()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                game.handle_event(event)

        game.update(dt)
        game.draw()
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()