import pygame
import pygame.freetype
import numpy as np
import enum

# Initialize pygame
pygame.init()

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

HEX_RADIUS = 4
SPHERE_DIST = 60
SPHERE_RADIUS = 25
EMPTY_RADIUS = 20
SELECTION_WIDTH = 6
WINNER_BG_PADDING = 30


# Create screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
high_res_surface = pygame.Surface((WIDTH * 2, HEIGHT * 2))
pygame.display.set_caption("Abalone Game")
FONT = pygame.freetype.Font(None, 200)


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


class Marble:
    def __init__(self, x, y, color, radius):
        self.x = x
        self.y = y
        self.draw_x = round(WIDTH / 2 + (self.x - HEX_RADIUS) * SPHERE_DIST * 3 ** 0.5 / 2)
        self.draw_y = round(HEIGHT / 2 - (self.y - (self.x if self.x <= HEX_RADIUS else 2 * HEX_RADIUS - self.x) / 2
                                          - 2) * SPHERE_DIST)
        self.color = color
        self.radius = radius

    def draw(self):
        pygame.draw.circle(high_res_surface, self.color, (self.draw_x * 2, self.draw_y * 2), self.radius * 2)

    def select(self, direction):
        pygame.draw.circle(high_res_surface, SELECTED, (self.draw_x * 2, self.draw_y * 2), self.radius * 2,
                           SELECTION_WIDTH)
        if direction == Direction.UP:
            start_angle = -2 * np.pi / 3
            end_angle = -np.pi / 3
        elif direction == Direction.DOWN:
            start_angle = np.pi / 3
            end_angle = 2 * np.pi / 3
        elif direction == Direction.LEFT_UP:
            start_angle = np.pi
            end_angle = 4 * np.pi / 3
        elif direction == Direction.LEFT_DOWN:
            start_angle = 2 * np.pi / 3
            end_angle = np.pi
        elif direction == Direction.RIGHT_UP:
            start_angle = 5 * np.pi / 3
            end_angle = 2 * np.pi
        else:
            start_angle = 0
            end_angle = np.pi / 3

        angles = np.linspace(start_angle, end_angle, num=20)
        points = np.column_stack((self.draw_x + self.radius * np.cos(angles),
                                  self.draw_y + self.radius * np.sin(angles)))
        points = np.vstack((points, [(self.draw_x + 1.4 * self.radius * np.cos((start_angle + end_angle) / 2),
                                     self.draw_y + 1.4 * self.radius * np.sin((start_angle + end_angle) / 2))]))
        points *= 2

        pygame.draw.polygon(high_res_surface, ARROW_COLOR, points)

    def is_inside(self, pos):
        return (pos[0] - self.draw_x) ** 2 + (pos[1] - self.draw_y) ** 2 < self.radius ** 2


def init_board():
    board = {}
    for i in range(HEX_RADIUS + 1):
        for j in range(i + HEX_RADIUS + 1):
            if i < 2 or (i == 2 and 2 <= j <= 4):
                board[(i, j)] = Marble(i, j, WHITE, SPHERE_RADIUS)
                board[(2 * HEX_RADIUS - i, j)] = Marble(2 * HEX_RADIUS - i, j, BLACK, SPHERE_RADIUS)
            else:
                board[(i, j)] = Marble(i, j, EMPTY, EMPTY_RADIUS)
                board[(2 * HEX_RADIUS - i, j)] = Marble(2 * HEX_RADIUS - i, j, EMPTY, EMPTY_RADIUS)
    return board


def get_collision(board, pos):
    for marble in board.values():
        if marble.is_inside(pos):
            return marble.x, marble.y
    return None


def move(board, init_pos, dest_pos, removed):
    player_color = board[init_pos].color
    curr = init_pos
    after = dest_pos
    direction = (dest_pos[0] - init_pos[0], dest_pos[1] - init_pos[1])
    temp = board[curr]
    board[curr] = Marble(curr[0], curr[1], EMPTY, EMPTY_RADIUS)

    while after in board and temp.color != EMPTY:
        temp, board[after] = board[after], temp
        board[after] = Marble(after[0], after[1], board[after].color, board[after].radius)

        curr = after
        after = (curr[0] + direction[0], curr[1] + direction[1])

    if after not in board and temp.color != EMPTY:
        removed[player_color] += 1


def hexa_dist(p1, p2): # calculates the distance between two points in the hexagonal grid
    if p1[0] <= 4 and p2[0] <= 4 or p1[0] >= 4 and p2[0] >= 4: # if they are both on the same side relative to the central column
        if p1[0] <= 4 and p2[0] <= 4:
            p1, p2 = (p1, p2) if p1[0] <= p2[0] else (p2, p1)
        else:
            p1, p2 = (p1, p2) if p1[0] >= p2[0] else (p2, p1)
        p1_range_at_p2 = (p1[1], p1[1] + abs(p2[0] - p1[0]))
        return abs(p1[0] - p2[0]) + max(0, max(p1_range_at_p2[0], p2[1]) - min(p1_range_at_p2[1], p2[1]))
    else: # if they are on different sides of the center
        p1_mid = (p1[1], p1[1] + abs(4 - p1[0]))
        p2_mid = (p2[1], p2[1] + abs(4 - p2[0]))
        return abs(p1[0] - p2[0]) + max(0, max(p1_mid[0], p2_mid[0]) - min(p1_mid[1], p2_mid[1]))


def handle_left_click(board, event, turn, selected):
    collision = get_collision(board, event.pos)
    if collision is None or board[collision].color != turn:
        selected[:] = []
    elif len(selected) < 3 and collision not in selected:
        selected.append(collision)
    elif collision in selected:
        selected.remove(collision)
    elif len(selected) == 3:
        selected[:] = [collision]

    if len(selected) == 2 and hexa_dist(selected[0], selected[1]) > 1: # if picked two that are too far away, switch to newer picked
        selected[:] = [collision]
    elif len(selected) == 3: # if picked three that don't line up, switch to newer picked
        direction = Direction.get_direction(selected[0], selected[1])
        second_dir = None

        if hexa_dist(selected[0], selected[2]) == 1:
            second_dir = Direction.get_direction(selected[0], selected[2])
        elif hexa_dist(selected[1], selected[2]) == 1:
            second_dir = Direction.get_direction(selected[1], selected[2])

        if second_dir is None or (direction != second_dir and direction != second_dir.flip()):
            selected[:] = [collision]


def orthogonal_move(board, turn, selected, direction, other_turn):
    new_pos = [Direction.get_pos_after_move(selection, direction) for selection in selected]
    for pos in new_pos:
        if pos not in board or board[pos].color != EMPTY:
            return turn
    for old, new in zip(selected, new_pos):
        board[old], board[new] = board[new], board[old]
        board[new] = Marble(new[0], new[1], board[new].color, board[new].radius)
        board[old] = Marble(old[0], old[1], board[old].color, board[old].radius)
    selected[:] = []
    return other_turn


def parallel_move(board, turn, selected, direction, other_turn, removed):
    pos = selected[0]
    while pos in selected:
        pos = Direction.get_pos_after_move(pos, direction)
    num_others = 0
    while pos in board and board[pos].color == other_turn:
        num_others += 1
        pos = Direction.get_pos_after_move(pos, direction)
        if num_others >= len(selected):
            return turn
    if ((pos in board and board[pos].color != EMPTY) or num_others >= len(selected) or
            (pos not in board and num_others == 0)):  # if can't move there
        return turn

    # finding first marble in row
    pos = selected[0]
    while pos in selected:
        pos = Direction.get_pos_after_move(pos, direction.flip())
    pos = Direction.get_pos_after_move(pos, direction)
    temp = board[pos]
    board[pos] = Marble(pos[0], pos[1], EMPTY, EMPTY_RADIUS)
    pos = Direction.get_pos_after_move(pos, direction)
    while temp.color != EMPTY and pos in board:
        temp, board[pos] = board[pos], Marble(pos[0], pos[1], temp.color, temp.radius)
        pos = Direction.get_pos_after_move(pos, direction)
    if temp.color != EMPTY:
        removed[temp.color] += 1
    selected[:] = []
    return other_turn


def handle_right_click(board, direction, turn, selected, removed):
    if len(selected) == 0:
        return turn
    other_turn = WHITE if turn == BLACK else BLACK
    dir_selected = Direction.get_direction(selected[0], selected[1]) if len(selected) > 1 else None
    if dir_selected is not None and dir_selected != direction and dir_selected != direction.flip(): # moving orthogonally to selected
        return orthogonal_move(board, turn, selected, direction, other_turn)
    else: # moving along selection
        return parallel_move(board, turn, selected, direction, other_turn, removed)


def calc_direction_selected_mouse(board, selected): # getting the direction of the arrows
    if len(selected) == 0:
        return None
    directions = {-np.pi / 2: Direction.UP, np.pi / 2: Direction.DOWN, -np.pi / 6: Direction.RIGHT_UP,
                  np.pi / 6: Direction.RIGHT_DOWN, -5 * np.pi / 6: Direction.LEFT_UP, 5 * np.pi / 6: Direction.LEFT_DOWN}
    direction_angles = np.fromiter(directions.keys(), dtype=float)
    pos = pygame.mouse.get_pos()
    selected_marbles = [board[selection] for selection in selected]
    center_selected = np.mean(np.array([(selected_marble.draw_x, selected_marble.draw_y)
                                        for selected_marble in selected_marbles]), axis=0)
    angle = np.atan2(pos[1] - center_selected[1], pos[0] - center_selected[0]) # calculating angle between the center of the selected marbles and the mouse position
    return directions[direction_angles[np.argmin(np.abs(direction_angles - angle))]] # returning the direction of the angle


def draw_taken_marbles(removed):
    for i in range(removed[WHITE]):
        pygame.draw.circle(high_res_surface, WHITE,
                           (2 * (WIDTH - SPHERE_DIST), 2 * SPHERE_DIST * (1 + 1.1 * i)), 2 * SPHERE_RADIUS)
    for i in range(removed[BLACK]):
        pygame.draw.circle(high_res_surface, BLACK,
                           (2 * SPHERE_DIST, 2 * SPHERE_DIST * (1 + 1.1 * i)), 2 * SPHERE_RADIUS)


def main():
    board = init_board()
    running = True
    selected = []
    removed = {WHITE: 0, BLACK: 0}
    turn = BLACK
    game_over = False

    while running:
        direction = calc_direction_selected_mouse(board, selected)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and game_over == False:
                if event.button == 1:
                    handle_left_click(board, event, turn, selected)
                elif event.button == 3:
                    turn = handle_right_click(board, direction, turn, selected, removed)

        high_res_surface.fill(BACKGROUND)
        pygame.draw.polygon(high_res_surface, BOARD_COLOR,
                            [(WIDTH + (SPHERE_DIST * HEX_RADIUS + SPHERE_RADIUS + 20) *
                              np.cos(np.radians(angle)) * 2,
                              HEIGHT + (SPHERE_DIST * HEX_RADIUS + SPHERE_RADIUS + 20) *
                              np.sin(np.radians(angle)) * 2)
                             for angle in range(30, 390, 60)], 0)
        for marble in board.values():
            marble.draw()

        for selection in selected:
            board[selection].select(direction)

        draw_taken_marbles(removed)

        if removed[BLACK] == 6:
            text_rect = FONT.get_rect("White wins!")
            text_rect.center = (WIDTH, HEIGHT // 2)
            pygame.draw.rect(high_res_surface, WINNER_COLOR_BACKGROUND,
                             text_rect.inflate(WINNER_BG_PADDING * 2, WINNER_BG_PADDING * 2))
            FONT.render_to(high_res_surface, text_rect, "White wins!", WINNER_COLOR_TEXT)
            game_over = True
        elif removed[WHITE] == 6:
            text_rect = FONT.get_rect("Black wins!")
            text_rect.center = (WIDTH, HEIGHT // 2)
            pygame.draw.rect(high_res_surface, WINNER_COLOR_BACKGROUND,
                             text_rect.inflate(WINNER_BG_PADDING * 2, WINNER_BG_PADDING * 2))
            FONT.render_to(high_res_surface, text_rect, "Black wins!", WINNER_COLOR_TEXT)
            game_over = True

        pygame.transform.smoothscale(high_res_surface, (WIDTH, HEIGHT), screen)
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
