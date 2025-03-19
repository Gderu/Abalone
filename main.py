import pygame
import pygame.freetype
import numpy as np
import enum

# Constants
WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
EMPTY = (200, 200, 200)
BOARD_COLOR = (105, 105, 105)
BACKGROUND = (225, 225, 235)
SELECTED = (255, 215, 0)
ARROW_COLOR = (255, 153, 204)
WINNER_COLOR_TEXT = (102, 178, 255)
WINNER_COLOR_BACKGROUND = (0, 51, 102)
SCALE_FACTOR = 2
NUM_MARBLES_FOR_VICTORY = 6

HEX_RADIUS = 4
SPHERE_DIST = 60
SPHERE_RADIUS = 25
EMPTY_RADIUS = 20
SELECTION_WIDTH = 6
WINNER_BG_PADDING = 30


class Direction(enum.Enum):
    UP = 0
    DOWN = 1
    LEFT_UP = 2
    LEFT_DOWN = 3
    RIGHT_UP = 4
    RIGHT_DOWN = 5

    def flip(self):
        if self == Direction.UP:
            return Direction.DOWN
        elif self == Direction.DOWN:
            return Direction.UP
        elif self == Direction.LEFT_UP:
            return Direction.RIGHT_DOWN
        elif self == Direction.LEFT_DOWN:
            return Direction.RIGHT_UP
        elif self == Direction.RIGHT_UP:
            return Direction.LEFT_DOWN
        else:
            return Direction.LEFT_UP


    # assumes they are of distance 1 apart
    @staticmethod
    def get_direction(p1, p2):
        diff = (p1[0] - p2[0], p1[1] - p2[1])
        if diff[0] == 0:
            return Direction.UP if diff[1] > 0 else Direction.DOWN
        if p1[0] < 4 or p2[0] < 4:  # if in left side
            if diff[0] == 1 and diff[1] == 0:
                return Direction.RIGHT_DOWN
            elif diff[0] == 1 and diff[1] == 1:
                return Direction.RIGHT_UP
            elif diff[0] == -1 and diff[1] == -1:
                return Direction.LEFT_DOWN
            elif diff[0] == -1 and diff[1] == 0:
                return Direction.LEFT_UP
            else:
                raise Exception(f"Should never happen, incorrect diff in get_direction: {p1, p2}")
        else:  # if in right side
            if diff[0] == 1 and diff[1] == -1:
                return Direction.RIGHT_DOWN
            elif diff[0] == 1 and diff[1] == 0:
                return Direction.RIGHT_UP
            elif diff[0] == -1 and diff[1] == 0:
                return Direction.LEFT_DOWN
            elif diff[0] == -1 and diff[1] == 1:
                return Direction.LEFT_UP
            else:
                raise Exception(f"Should never happen, incorrect diff in get_direction: {p1, p2}")

    # can return positions outside of board
    @staticmethod
    def get_pos_after_move(pos, direction):
        if direction == Direction.UP:
            return pos[0], pos[1] + 1
        elif direction == Direction.DOWN:
            return pos[0], pos[1] - 1

        if pos[0] < 4 or pos[0] == 4 and direction in {Direction.LEFT_UP, Direction.LEFT_DOWN}:  # if in left side
            if direction == Direction.LEFT_DOWN:
                return pos[0] - 1, pos[1] - 1
            elif direction == Direction.LEFT_UP:
                return pos[0] - 1, pos[1]
            elif direction == Direction.RIGHT_DOWN:
                return pos[0] + 1, pos[1]
            else:
                return pos[0] + 1, pos[1] + 1
        else:  # if in right side
            if direction == Direction.LEFT_DOWN:
                return pos[0] - 1, pos[1]
            elif direction == Direction.LEFT_UP:
                return pos[0] - 1, pos[1] + 1
            elif direction == Direction.RIGHT_DOWN:
                return pos[0] + 1, pos[1] - 1
            else:
                return pos[0] + 1, pos[1]


class Logic:
    def __init__(self):
        self.board = {}
        self.init_board()
        self.removed = {WHITE: 0, BLACK: 0}
        self.turn = BLACK
        self.game_over = False

    def init_board(self):
        for i in range(HEX_RADIUS + 1):
            for j in range(i + HEX_RADIUS + 1):
                if i < 2 or (i == 2 and 2 <= j <= 4):
                    self.board[(i, j)] = WHITE
                    self.board[(2 * HEX_RADIUS - i, j)] = BLACK
                else:
                    self.board[(i, j)] = EMPTY
                    self.board[(2 * HEX_RADIUS - i, j)] = EMPTY

    def is_legal_move(self, selected, direction):
        if len(selected) == 0:
            return False

        dir_selected = Direction.get_direction(selected[0], selected[1]) if len(selected) > 1 else None
        if dir_selected is not None and dir_selected != direction and dir_selected != direction.flip():  # moving orthogonally to selected
            return self.is_legal_orthogonal_move(selected, direction)
        else:
            return self.is_legal_parallel_move(selected, direction)

    def is_legal_orthogonal_move(self, selected, direction):
        new_pos = [Direction.get_pos_after_move(selection, direction) for selection in selected]
        for pos in new_pos:
            if pos not in self.board or self.board[pos] != EMPTY:
                return False
        return True

    def is_legal_parallel_move(self, selected, direction):
        pos = selected[0]
        # getting last selected in direction
        while pos in selected:
            pos = Direction.get_pos_after_move(pos, direction)

        num_others = 0
        other_turn = WHITE if self.turn == BLACK else BLACK
        # counting other color marbles
        while pos in self.board and self.board[pos] == other_turn:
            num_others += 1
            pos = Direction.get_pos_after_move(pos, direction)
            if num_others >= len(selected):
                return False

        if (pos in self.board and self.board[pos] != EMPTY) or (pos not in self.board and num_others == 0):  # if can't move there
            return False
        return True

    # moves and assumes the move is legal
    def move(self, selected, direction):

        dir_selected = Direction.get_direction(selected[0], selected[1]) if len(selected) > 1 else None
        if dir_selected is not None and dir_selected != direction and dir_selected != direction.flip():  # moving orthogonally to selected
            self.orthogonal_move(selected, direction)
        else:  # moving along selection
            self.parallel_move(selected, direction)

        self.turn = WHITE if self.turn == BLACK else BLACK

        if NUM_MARBLES_FOR_VICTORY in self.removed.values():
            self.game_over = True

    def orthogonal_move(self, selected, direction):
        for selection in selected:
            new_pos = Direction.get_pos_after_move(selection, direction)
            self.board[new_pos] = self.board[selection]
            self.board[selection] = EMPTY

    def parallel_move(self, selected, direction):
        # finding first marble in row
        pos = selected[0]
        while pos in selected:
            pos = Direction.get_pos_after_move(pos, direction.flip())

        pos = Direction.get_pos_after_move(pos, direction)
        temp = EMPTY
        first = True
        # switching marbles forward
        while (temp != EMPTY or first) and pos in self.board:
            first = False
            temp, self.board[pos] = self.board[pos], temp
            pos = Direction.get_pos_after_move(pos, direction)

        if temp != EMPTY:
            self.removed[temp] += 1

    @staticmethod
    def hexa_dist(p1, p2):  # calculates the distance between two points in the hexagonal grid
        if p1[0] <= 4 and p2[0] <= 4 or p1[0] >= 4 and p2[
            0] >= 4:  # if they are both on the same side relative to the central column
            if p1[0] <= 4 and p2[0] <= 4:
                p1, p2 = (p1, p2) if p1[0] <= p2[0] else (p2, p1)
            else:
                p1, p2 = (p1, p2) if p1[0] >= p2[0] else (p2, p1)
            p1_range_at_p2 = (p1[1], p1[1] + abs(p2[0] - p1[0]))
            return abs(p1[0] - p2[0]) + max(0, max(p1_range_at_p2[0], p2[1]) - min(p1_range_at_p2[1], p2[1]))
        else:  # if they are on different sides of the center
            p1_mid = (p1[1], p1[1] + abs(4 - p1[0]))
            p2_mid = (p2[1], p2[1] + abs(4 - p2[0]))
            return abs(p1[0] - p2[0]) + max(0, max(p1_mid[0], p2_mid[0]) - min(p1_mid[1], p2_mid[1]))

class Graphics:
    def __init__(self):
        # Create screen
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.high_res_surface = pygame.Surface((WIDTH * 2, HEIGHT * 2))
        pygame.display.set_caption("Abalone Game")
        self.FONT = pygame.freetype.Font(None, 200)
        self.selected = []
        self.direction = None

    def handle_left_click(self, board, event_pos, turn):
        collision = self.get_collision(board, event_pos)
        if collision is None or board[collision] != turn:
            self.selected = []
        elif len(self.selected) < 3 and collision not in self.selected:
            self.selected.append(collision)
        elif collision in self.selected:
            self.selected.remove(collision)
        elif len(self.selected) == 3:
            self.selected = [collision]

        # if picked two that are too far away, switch to newer picked
        if len(self.selected) == 2 and Logic.hexa_dist(self.selected[0], self.selected[1]) > 1:
            self.selected = [collision]
        elif len(self.selected) == 3:  # if picked three that don't line up, switch to newer picked
            direction = Direction.get_direction(self.selected[0], self.selected[1])
            second_dir = None

            if Logic.hexa_dist(self.selected[0], self.selected[2]) == 1:
                second_dir = Direction.get_direction(self.selected[0], self.selected[2])
            elif Logic.hexa_dist(self.selected[1], self.selected[2]) == 1:
                second_dir = Direction.get_direction(self.selected[1], self.selected[2])

            if second_dir is None or (direction != second_dir and direction != second_dir.flip()):
                self.selected = [collision]

    def draw_board(self, board, removed):
        self.high_res_surface.fill(BACKGROUND)
        pygame.draw.polygon(self.high_res_surface, BOARD_COLOR,
                            [(WIDTH + (SPHERE_DIST * HEX_RADIUS + SPHERE_RADIUS + 20) *
                              np.cos(np.radians(angle)) * 2,
                              HEIGHT + (SPHERE_DIST * HEX_RADIUS + SPHERE_RADIUS + 20) *
                              np.sin(np.radians(angle)) * 2)
                             for angle in range(30, 390, 60)], 0)

        for (x, y), color in board.items():
            draw_x, draw_y = self.calc_draw_pos(x, y)
            radius = SPHERE_RADIUS if color != EMPTY else EMPTY_RADIUS
            pygame.draw.circle(self.high_res_surface, color,
                               (draw_x * SCALE_FACTOR, draw_y * SCALE_FACTOR), radius * SCALE_FACTOR)

        for (x, y) in self.selected:
            self.select_marble(x, y, SPHERE_RADIUS if board[(x, y)] != EMPTY else EMPTY_RADIUS)

        self.draw_taken_marbles(removed)
        self.draw_victory(removed)

        pygame.transform.smoothscale(self.high_res_surface, (WIDTH, HEIGHT), self.screen)
        pygame.display.flip()

    def draw_victory(self, removed):
        if removed[BLACK] == NUM_MARBLES_FOR_VICTORY:
            text_rect = self.FONT.get_rect("White wins!")
            text_rect.center = (SCALE_FACTOR * WIDTH // 2, SCALE_FACTOR * HEIGHT // 4)
            pygame.draw.rect(self.high_res_surface, WINNER_COLOR_BACKGROUND,
                             text_rect.inflate(WINNER_BG_PADDING * SCALE_FACTOR, WINNER_BG_PADDING * SCALE_FACTOR))
            self.FONT.render_to(self.high_res_surface, text_rect, "White wins!", WINNER_COLOR_TEXT)
        elif removed[WHITE] == NUM_MARBLES_FOR_VICTORY:
            text_rect = self.FONT.get_rect("Black wins!")
            text_rect.center = (SCALE_FACTOR * WIDTH // 2, SCALE_FACTOR * HEIGHT // 4)
            pygame.draw.rect(self.high_res_surface, WINNER_COLOR_BACKGROUND,
                             text_rect.inflate(WINNER_BG_PADDING * SCALE_FACTOR, WINNER_BG_PADDING * SCALE_FACTOR))
            self.FONT.render_to(self.high_res_surface, text_rect, "Black wins!", WINNER_COLOR_TEXT)

    def select_marble(self, x, y, radius):
        draw_x, draw_y = self.calc_draw_pos(x, y)
        pygame.draw.circle(self.high_res_surface, SELECTED,
                           (draw_x * SCALE_FACTOR, draw_y * SCALE_FACTOR), radius * SCALE_FACTOR,
                           SELECTION_WIDTH)
        if self.direction == Direction.UP:
            start_angle = -2 * np.pi / 3
            end_angle = -np.pi / 3
        elif self.direction == Direction.DOWN:
            start_angle = np.pi / 3
            end_angle = 2 * np.pi / 3
        elif self.direction == Direction.LEFT_UP:
            start_angle = np.pi
            end_angle = 4 * np.pi / 3
        elif self.direction == Direction.LEFT_DOWN:
            start_angle = 2 * np.pi / 3
            end_angle = np.pi
        elif self.direction == Direction.RIGHT_UP:
            start_angle = 5 * np.pi / 3
            end_angle = 2 * np.pi
        else:
            start_angle = 0
            end_angle = np.pi / 3

        angles = np.linspace(start_angle, end_angle, num=20)
        points = np.column_stack((draw_x + radius * np.cos(angles), draw_y + radius * np.sin(angles)))
        points = np.vstack((points, [(draw_x + 1.4 * radius * np.cos((start_angle + end_angle) / 2),
                                      draw_y + 1.4 * radius * np.sin((start_angle + end_angle) / 2))]))
        points *= SCALE_FACTOR

        pygame.draw.polygon(self.high_res_surface, ARROW_COLOR, points)

    def draw_taken_marbles(self, removed):
        for i in range(removed[WHITE]):
            pygame.draw.circle(self.high_res_surface, WHITE,
                               (SCALE_FACTOR * (WIDTH - SPHERE_DIST), SCALE_FACTOR * SPHERE_DIST * (1 + 1.1 * i)),
                               SCALE_FACTOR * SPHERE_RADIUS)
        for i in range(removed[BLACK]):
            pygame.draw.circle(self.high_res_surface, BLACK,
                               (SCALE_FACTOR * SPHERE_DIST, SCALE_FACTOR * SPHERE_DIST * (1 + 1.1 * i)),
                               SCALE_FACTOR * SPHERE_RADIUS)

    def calc_direction_selected_mouse(self):  # getting the direction of the arrows
        if len(self.selected) == 0:
            self.direction = None
            return

        directions = {-np.pi / 2: Direction.UP, np.pi / 2: Direction.DOWN, -np.pi / 6: Direction.RIGHT_UP,
                      np.pi / 6: Direction.RIGHT_DOWN, -5 * np.pi / 6: Direction.LEFT_UP,
                      5 * np.pi / 6: Direction.LEFT_DOWN}
        direction_angles = np.fromiter(directions.keys(), dtype=float)
        pos = pygame.mouse.get_pos()
        center_selected = np.mean(np.array([self.calc_draw_pos(x, y) for (x, y) in self.selected]), axis=0)
        angle = np.atan2(pos[1] - center_selected[1], pos[0] - center_selected[0])  # calculating angle between the center of the selected marbles and the mouse position
        self.direction = directions[direction_angles[np.argmin(np.abs(direction_angles - angle))]]  # returning the direction of the angle

    def unselect(self):
        self.selected = []

    @staticmethod
    def calc_draw_pos(x, y):
        draw_x = round(WIDTH / 2 + (x - HEX_RADIUS) * SPHERE_DIST * 3 ** 0.5 / 2)
        draw_y = round(HEIGHT / 2 - (y - (x if x <= HEX_RADIUS else 2 * HEX_RADIUS - x) / 2 - 2) * SPHERE_DIST)
        return draw_x, draw_y

    @staticmethod
    def get_collision(board, pos):
        for (x, y), color in board.items():
            draw_x, draw_y = Graphics.calc_draw_pos(x, y)
            radius = SPHERE_RADIUS if color != EMPTY else EMPTY_RADIUS
            # if pos is inside the marble
            if (pos[0] - draw_x) ** 2 + (pos[1] - draw_y) ** 2 < radius ** 2:
                return x, y
        return None


def main():
    pygame.init()

    logic = Logic()
    graphics = Graphics()
    running = True

    while running:
        graphics.calc_direction_selected_mouse()

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and logic.game_over == False:
                if event.button == 1:
                    graphics.handle_left_click(logic.board, event.pos, logic.turn)
                elif event.button == 3:
                    if logic.is_legal_move(graphics.selected, graphics.direction):
                        logic.move(graphics.selected, graphics.direction)
                        graphics.unselect()

        graphics.draw_board(logic.board, logic.removed)
    pygame.quit()


if __name__ == "__main__":
    main()
