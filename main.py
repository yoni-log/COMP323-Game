import pygame

from anim_feedback.game import Game
from anim_feedback.game_config import *
from anim_feedback.start_screen import *

def main() -> None:
    pygame.init()
    pygame.display.set_caption("Don't Crumble")

    run_start_screen()  # Shows the start screen, returns when Enter is pressed

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