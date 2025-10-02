from flask import Flask, render_template, request, jsonify
import random
import json
import os
from datetime import datetime
from threading import Lock

app = Flask(__name__)

# Thread-safe lock for leaderboard file access
leaderboard_lock = Lock()
LEADERBOARD_FILE = 'leaderboard.json'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_levels', methods=['GET'])
def get_levels():
    try:
        with open('texts.json', 'r', encoding='utf-8') as f:
            levels = json.load(f)
        return jsonify(levels)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_monster_sprites', methods=['GET'])
def get_monster_sprites():
    try:
        monsters_dir = 'static/monsters'
        monster_files = [f for f in os.listdir(monsters_dir) if f.endswith('.png')]
        monster_paths = [f'/static/monsters/{f}' for f in monster_files]
        return jsonify(monster_paths)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def load_leaderboard():
    """Thread-safe leaderboard loading"""
    with leaderboard_lock:
        try:
            with open(LEADERBOARD_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {'all_time': [], 'daily': {}}

def save_leaderboard(data):
    """Thread-safe leaderboard saving"""
    with leaderboard_lock:
        with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

@app.route('/get_leaderboard', methods=['GET'])
def get_leaderboard():
    try:
        data = load_leaderboard()
        today = datetime.now().strftime('%Y-%m-%d')

        # Get today's leaderboard
        daily = data['daily'].get(today, [])

        # Sort: first by words collected (desc), then by time (asc)
        daily_sorted = sorted(daily, key=lambda x: (-x['words_collected'], x['time']))[:10]
        all_time_sorted = sorted(data['all_time'], key=lambda x: (-x['words_collected'], x['time']))[:10]

        return jsonify({
            'daily': daily_sorted,
            'all_time': all_time_sorted
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/submit_score', methods=['POST'])
def submit_score():
    try:
        score_data = request.json
        name = score_data.get('name', 'Anonymous')[:20]  # Max 20 chars
        words_collected = score_data.get('words_collected', 0)
        time_seconds = score_data.get('time', 0)

        today = datetime.now().strftime('%Y-%m-%d')

        entry = {
            'name': name,
            'words_collected': words_collected,
            'time': time_seconds,
            'timestamp': datetime.now().isoformat()
        }

        data = load_leaderboard()

        # Add to all-time
        data['all_time'].append(entry)

        # Add to daily
        if today not in data['daily']:
            data['daily'][today] = []
        data['daily'][today].append(entry)

        # Clean up old daily entries (keep last 7 days)
        dates = sorted(data['daily'].keys(), reverse=True)
        for old_date in dates[7:]:
            del data['daily'][old_date]

        save_leaderboard(data)

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate_maze', methods=['POST'])
def generate_maze():
    data = request.json
    words = data.get('words', [])
    word_sequence = data.get('word_sequence', [])  # Ordered list of words to collect
    width = data.get('width', 30)
    height = data.get('height', 20)

    if not words:
        words = ['WORD', 'MAZE', 'GAME', 'PLAY', 'FUN']

    if not word_sequence:
        word_sequence = words[:5]

    # Generate maze with guaranteed path
    maze = generate_maze_with_path(width, height, words, word_sequence)

    return jsonify(maze)

def generate_maze_with_path(width, height, words, word_sequence):
    """Generate a maze with guaranteed path from left to right using recursive backtracking"""
    # Initialize grid (0 = path, 1 = wall)
    grid = [[1 for _ in range(width)] for _ in range(height)]

    # Start position (left side, middle)
    start_y = height // 2
    start_x = 0

    # End position (right side, middle)
    end_y = height // 2
    end_x = width - 1

    # Carve path using recursive backtracking
    def carve(x, y):
        grid[y][x] = 0

        # Random directions
        directions = [(0, -2), (2, 0), (0, 2), (-2, 0)]
        random.shuffle(directions)

        for dx, dy in directions:
            nx, ny = x + dx, y + dy

            if 0 <= nx < width and 0 <= ny < height and grid[ny][nx] == 1:
                # Carve path between cells
                grid[y + dy // 2][x + dx // 2] = 0
                carve(nx, ny)

    # Start carving from start position
    carve(start_x if start_x % 2 == 0 else start_x + 1,
          start_y if start_y % 2 == 0 else start_y)

    # Ensure start and end are open
    grid[start_y][start_x] = 0
    grid[end_y][end_x] = 0

    # Connect start if not already connected
    for i in range(min(3, width)):
        grid[start_y][i] = 0

    # Connect end if not already connected
    for i in range(max(width - 3, 0), width):
        grid[end_y][i] = 0

    # Create word pool for even distribution
    word_pool = []
    wall_count = sum(row.count(1) for row in grid)

    # Fill pool with words, repeating the entire list as needed
    while len(word_pool) < wall_count:
        word_pool.extend(words)

    # Shuffle the pool
    random.shuffle(word_pool)

    # Assign words to walls using the pool
    maze_data = []
    word_index = 0

    for y in range(height):
        row = []
        for x in range(width):
            if grid[y][x] == 1:
                row.append(word_pool[word_index])
                word_index += 1
            else:
                row.append(None)
        maze_data.append(row)

    # Place each word from sequence at least once in the maze
    wall_positions = [(x, y) for y in range(height) for x in range(width) if maze_data[y][x] is not None]

    for word in word_sequence:
        if wall_positions:
            pos = random.choice(wall_positions)
            x, y = pos
            maze_data[y][x] = word

    # Generate monster positions (on path cells)
    monsters = []
    path_cells = [(x, y) for y in range(height) for x in range(width) if grid[y][x] == 0]

    # Place 2-3 initial monsters
    num_monsters = random.randint(2, 3)
    monster_positions = random.sample(path_cells, min(num_monsters, len(path_cells)))

    for x, y in monster_positions:
        # Skip if too close to start
        if abs(x - start_x) < 5 and abs(y - start_y) < 3:
            continue
        monsters.append({
            'x': x,
            'y': y,
            'direction': random.choice(['up', 'down', 'left', 'right']),
            'steps': random.randint(3, 7)
        })

    return {
        'grid': maze_data,
        'start': {'x': start_x, 'y': start_y},
        'end': {'x': end_x, 'y': end_y},
        'monsters': monsters,
        'width': width,
        'height': height,
        'word_sequence': word_sequence
    }

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
