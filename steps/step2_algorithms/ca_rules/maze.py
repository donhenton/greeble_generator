"""
steps/step2_algorithms/ca_rules/maze.py
Maze rule — B3/S12345

Born:    dead cell with exactly 3 live neighbours becomes alive
Survive: live cell with 1, 2, 3, 4, or 5 live neighbours stays alive
Die:     live cell with 0 or 6+ neighbours dies

Produces dense labyrinthine corridor patterns —
long winding connected regions with gaps between them.
Looks like circuit traces or piping layouts on the box floor.
"""


def apply(grid, rows, cols):
    """
    Apply one generation of Maze B3/S12345 rules.
    grid is a 2D list of bools [row][col].
    Returns new grid.
    """
    new_grid = [[False] * cols for _ in range(rows)]

    for r in range(rows):
        for c in range(cols):
            neighbours = count_neighbours(grid, r, c, rows, cols)
            alive      = grid[r][c]

            if alive:
                new_grid[r][c] = neighbours in (1, 2, 3, 4, 5)  # survive
            else:
                new_grid[r][c] = neighbours == 3                  # born

    return new_grid


def count_neighbours(grid, r, c, rows, cols):
    count = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if grid[nr][nc]:
                    count += 1
    return count
