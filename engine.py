from models import *

# Checks if a car is inside a specific rectangle (box)
def contains(rect, car):
    left, right = rect['x'] - rect['w'], rect['x'] + rect['w']
    bottom, top = rect['y'] - rect['h'], rect['y'] + rect['h']
    return left <= car['x'] < right and bottom <= car['y'] < top

 # Checks if two boxes are touching or overlapping
def intersects(rect1, rect2):
    r1_l, r1_r = rect1['x'] - rect1['w'], rect1['x'] + rect1['w']
    r1_b, r1_t = rect1['y'] - rect1['h'], rect1['y'] + rect1['h']
    r2_l, r2_r = rect2['x'] - rect2['w'], rect2['x'] + rect2['w']
    r2_b, r2_t = rect2['y'] - rect2['h'], rect2['y'] + rect2['h']
    return not (r2_l > r1_r or r2_r < r1_l or r2_b > r1_t or r2_t < r1_b)

# Creates a blueprint for an empty box (a Quadtree node)
def create_quadtree(boundary, capacity):
    return {"boundary": boundary, "capacity": capacity, "cars": [], "divided": False,
            "nw": None, "ne": None, "sw": None, "se": None}

# Splits one big box into 4 smaller boxes
def subdivide(tree):
    box = tree['boundary']
    x, y, nw, nh = box['x'], box['y'], box['w'] / 2, box['h'] / 2
    cap = tree['capacity']
    tree['nw'] = create_quadtree(create_rect(x - nw, y + nh, nw, nh), cap)
    tree['ne'] = create_quadtree(create_rect(x + nw, y + nh, nw, nh), cap)
    tree['sw'] = create_quadtree(create_rect(x - nw, y - nh, nw, nh), cap)
    tree['se'] = create_quadtree(create_rect(x + nw, y - nh, nw, nh), cap)
    tree['divided'] = True

# Puts a car into the best possible box 
def insert(tree, car, log_to_csv=False):
    if not contains(tree['boundary'], car):
        return False
    if len(tree['cars']) < tree['capacity'] and not tree['divided']:
        tree['cars'].append(car)
        if log_to_csv: save_car_to_csv(car) # NEW: Logic to log to CSV
        return True
    if not tree['divided']:
        subdivide(tree)
    return (insert(tree['nw'], car, log_to_csv) or insert(tree['ne'], car, log_to_csv) or 
            insert(tree['sw'], car, log_to_csv) or insert(tree['se'], car, log_to_csv))

# Finds all cars within a search area 
def query(tree, search_area, cars_found):
    if not intersects(tree['boundary'], search_area):
        return
    for car in tree['cars']:
        if contains(search_area, car):
            cars_found.append(car)
    if tree['divided']:
        query(tree['nw'], search_area, cars_found)
        query(tree['ne'], search_area, cars_found)
        query(tree['sw'], search_area, cars_found)
        query(tree['se'], search_area, cars_found)

# Removes a car from the Quadtree based on its current position 
def remove(tree, car):
    if not contains(tree['boundary'], car): return False
    if tree['divided']:
        return remove(tree['nw'], car) or remove(tree['ne'], car) or \
               remove(tree['sw'], car) or remove(tree['se'], car)
    for i, c in enumerate(tree['cars']):
        if c['id'] == car['id']:
            tree['cars'].pop(i)
            return True
    return False

 # Moves a car by removing it, updating coordinates, and re-inserting 
def update_position(tree, car, new_x, new_y):
    if remove(tree, car):
        car['x'], car['y'] = new_x, new_y
        insert(tree, car)
        return True
    return False