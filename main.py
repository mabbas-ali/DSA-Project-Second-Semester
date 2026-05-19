import pygame
import random
import time
from models import *
from engine import *

WIDTH, HEIGHT = 900, 600  
MAP_WIDTH = 700           # Main map area
PANEL_WIDTH = 200         # side panel
CAPACITY = 10        #Set quadtree capacity   
NUM_DRIVERS = 1000   #Set number of drivers     
FPS = 60

# Colors
COLOR_BG = (20, 24, 28)
COLOR_GRID = (50, 58, 65)
COLOR_CAR = (0, 200, 255)
COLOR_USER = (255, 80, 80)
COLOR_TEXT = (240, 240, 240)
COLOR_PANEL = (40, 44, 52)
COLOR_HIGHLIGHT = (255, 255, 0)
COLOR_BUTTON = (0, 120, 215)
COLOR_BTN_HOVER = (0, 150, 255)

# Initialize
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Uber-Lite: Booking System")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Consolas", 14) 
header_font = pygame.font.SysFont("Consolas", 18, bold=True)

initialize_csv()
city_area = create_rect(MAP_WIDTH // 2, HEIGHT // 2, MAP_WIDTH // 2, HEIGHT // 2)
my_system = create_quadtree(city_area, CAPACITY)
all_cars_list = []

for i in range(NUM_DRIVERS):
    rx, ry = random.uniform(10, MAP_WIDTH - 10), random.uniform(10, HEIGHT - 10)
    price = round(random.uniform(5, 20), 2)
    car = create_car(rx, ry, f"Driver_{i}", price)
    insert(my_system, car, log_to_csv=True)
    all_cars_list.append(car)

# --- UI STATE MACHINE ---
current_state = "SELECT_LOCATION"
user_location = None
exact_user_pos = None 
found_drivers = []
selected_driver = None
result_rects = [] 
estimated_time = 0

display_limit = 5 
sort_preference = "CHEAPEST" # Can be "CHEAPEST" or "NEAREST"

def draw_quadtree(tree):
    b = tree['boundary']
    rect_coords = (b['x'] - b['w'], b['y'] - b['h'], b['w'] * 2, b['h'] * 2)
    pygame.draw.rect(screen, COLOR_GRID, rect_coords, 1)
    if tree['divided']:
        draw_quadtree(tree['nw']); draw_quadtree(tree['ne'])
        draw_quadtree(tree['sw']); draw_quadtree(tree['se'])

def update_etas_and_sort():
    """Helper to calculate ETAs for found drivers and sort them based on preference"""
    if not exact_user_pos or not found_drivers: return
    
    # Calculate ETA for all found drivers based on straight-line distance
    for d in found_drivers:
        dist = ((d['x'] - exact_user_pos[0])**2 + (d['y'] - exact_user_pos[1])**2)**0.5
        d['current_eta'] = max(1, int(dist / 15)) # 15 pixels approx = 1 minute
        
    # Sort the list
    if sort_preference == "CHEAPEST":
        found_drivers.sort(key=lambda c: c['price'])
    elif sort_preference == "NEAREST":
        found_drivers.sort(key=lambda c: c['current_eta'])

running = True
while running:
    screen.fill(COLOR_BG)
    mx, my = pygame.mouse.get_pos()

    # Define persistent UI buttons
    btn_limit_3 = pygame.Rect(MAP_WIDTH + 10, HEIGHT - 45, 40, 30)
    btn_limit_5 = pygame.Rect(MAP_WIDTH + 60, HEIGHT - 45, 40, 30)
    btn_limit_10 = pygame.Rect(MAP_WIDTH + 110, HEIGHT - 45, 40, 30)
    
    btn_sort_cheap = pygame.Rect(MAP_WIDTH + 10, 75, 85, 25)
    btn_sort_near = pygame.Rect(MAP_WIDTH + 105, 75, 85, 25)

    for event in pygame.event.get():
        if event.type == pygame.QUIT: 
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check general UI buttons (Only when NOT in confirmed state)
            if current_state in ["SELECT_LOCATION", "SHOW_DRIVERS"]:
                if btn_limit_3.collidepoint(mx, my): display_limit = 3
                elif btn_limit_5.collidepoint(mx, my): display_limit = 5
                elif btn_limit_10.collidepoint(mx, my): display_limit = 10
                
                # Check sorting buttons
                if btn_sort_cheap.collidepoint(mx, my):
                    sort_preference = "CHEAPEST"
                    update_etas_and_sort()
                    selected_driver = None # Deselect if sorting changes
                elif btn_sort_near.collidepoint(mx, my):
                    sort_preference = "NEAREST"
                    update_etas_and_sort()
                    selected_driver = None

            if current_state == "SELECT_LOCATION":
                if mx < MAP_WIDTH:
                    exact_user_pos = (mx, my)
                    user_location = create_rect(mx, my, 70, 70) 
                    found_drivers = []
                    query(my_system, user_location, found_drivers)
                    update_etas_and_sort()
                    current_state = "SHOW_DRIVERS"

            elif current_state == "SHOW_DRIVERS":
                # Check if clicked map to reset location
                if mx < MAP_WIDTH:
                    exact_user_pos = (mx, my)
                    user_location = create_rect(mx, my, 70, 70)
                    found_drivers = []
                    selected_driver = None
                    query(my_system, user_location, found_drivers)
                    update_etas_and_sort()
                
                # Check if clicked a driver in the list
                for rect, driver in result_rects:
                    if rect.collidepoint(mx, my):
                        selected_driver = driver
                
                # Check Driver Action Buttons (Only if a driver is selected)
                if selected_driver:
                    back_btn = pygame.Rect(MAP_WIDTH + 10, 440, 180, 35)
                    confirm_btn = pygame.Rect(MAP_WIDTH + 10, 485, 180, 35)
                    
                    if back_btn.collidepoint(mx, my):
                        # Deselect the driver
                        selected_driver = None
                    elif confirm_btn.collidepoint(mx, my):
                        # Confirm ride
                        estimated_time = selected_driver['current_eta']
                        current_state = "CONFIRMED_RIDE"

            elif current_state == "CONFIRMED_RIDE":
                # Check if clicked Cancel Button
                cancel_btn = pygame.Rect(MAP_WIDTH + 10, 545, 180, 35)
                if cancel_btn.collidepoint(mx, my):
                    selected_driver = None
                    user_location = None
                    exact_user_pos = None
                    current_state = "SELECT_LOCATION"

    # Updates moving cars
    for car in random.sample(all_cars_list, int(NUM_DRIVERS * 0.05)):
        new_x = max(5, min(MAP_WIDTH - 5, car['x'] + random.uniform(-1, 1)))
        new_y = max(5, min(HEIGHT - 5, car['y'] + random.uniform(-1, 1)))
        update_position(my_system, car, new_x, new_y)

    # Draw map Quadtree grid
    draw_quadtree(my_system)
    
    # Draw cars 
    for car in all_cars_list:
        if selected_driver is not None and car != selected_driver:
            continue # Hide other cars when one is selected
        pygame.draw.circle(screen, COLOR_CAR, (int(car['x']), int(car['y'])), 2)

    # Draw Search Radius and Pin Pointer
    if user_location and exact_user_pos:
        r = (user_location['x']-user_location['w'], user_location['y']-user_location['h'], user_location['w']*2, user_location['h']*2)
        pygame.draw.rect(screen, COLOR_USER, r, 1)
        pygame.draw.circle(screen, COLOR_USER, exact_user_pos, 5)
        pygame.draw.circle(screen, (255, 255, 255), exact_user_pos, 2) 

    # --- Side panel UI ---
    pygame.draw.rect(screen, COLOR_PANEL, (MAP_WIDTH, 0, PANEL_WIDTH, HEIGHT))
    
    if current_state in ["SELECT_LOCATION", "SHOW_DRIVERS"]:
        # Draw universal header and Sort Toggles
        header_text = "Welcome!" if current_state == "SELECT_LOCATION" else "Select Driver"
        screen.blit(header_font.render(header_text, True, COLOR_HIGHLIGHT), (MAP_WIDTH + 10, 20))
        
        screen.blit(font.render("Sort by:", True, COLOR_TEXT), (MAP_WIDTH + 10, 50))
        
        # Sort Buttons
        cheap_color = COLOR_HIGHLIGHT if sort_preference == "CHEAPEST" else COLOR_GRID
        near_color = COLOR_HIGHLIGHT if sort_preference == "NEAREST" else COLOR_GRID
        
        pygame.draw.rect(screen, cheap_color, btn_sort_cheap)
        pygame.draw.rect(screen, COLOR_TEXT, btn_sort_cheap, 1)
        screen.blit(font.render("Price", True, (0,0,0) if sort_preference == "CHEAPEST" else COLOR_TEXT), (btn_sort_cheap.x + 20, btn_sort_cheap.y + 5))

        pygame.draw.rect(screen, near_color, btn_sort_near)
        pygame.draw.rect(screen, COLOR_TEXT, btn_sort_near, 1)
        screen.blit(font.render("ETA", True, (0,0,0) if sort_preference == "NEAREST" else COLOR_TEXT), (btn_sort_near.x + 28, btn_sort_near.y + 5))

        # Draw Display Limit toggles at the bottom
        screen.blit(font.render("Show Top Results:", True, COLOR_TEXT), (MAP_WIDTH + 10, HEIGHT - 70))
        for limit, btn in [(3, btn_limit_3), (5, btn_limit_5), (10, btn_limit_10)]:
            bg_color = COLOR_HIGHLIGHT if display_limit == limit else COLOR_GRID
            pygame.draw.rect(screen, bg_color, btn)
            pygame.draw.rect(screen, COLOR_TEXT, btn, 1) 
            text_color = (0, 0, 0) if display_limit == limit else COLOR_TEXT
            val_text = font.render(str(limit), True, text_color)
            # Center text in button
            offset_x = 16 if limit < 10 else 12
            screen.blit(val_text, (btn.x + offset_x, btn.y + 8))

    if current_state == "SELECT_LOCATION":
        screen.blit(font.render("Please click on map", True, COLOR_TEXT), (MAP_WIDTH + 10, 110))
        screen.blit(font.render("to set your location", True, COLOR_TEXT), (MAP_WIDTH + 10, 130))

    elif current_state == "SHOW_DRIVERS":
        result_rects = []
        # Display dynamically based on limit
        for i, d in enumerate(found_drivers[:display_limit]): 
            color = COLOR_HIGHLIGHT if d == selected_driver else COLOR_TEXT
            
            # Format text strictly so it never cuts off (e.g. "#45  $12.50  4m")
            short_id = d['id'].replace("Driver_", "#")
            display_text = f"{short_id:<5} ${d['price']:<5.2f} {d['current_eta']}m"
            
            text_surf = font.render(display_text, True, color)
            text_rect = screen.blit(text_surf, (MAP_WIDTH + 10, 110 + (i * 25)))
            result_rects.append((text_rect, d))
        
        if selected_driver:
            # Draw Back Button
            back_btn = pygame.Rect(MAP_WIDTH + 10, 440, 180, 35)
            pygame.draw.rect(screen, (100, 100, 100), back_btn)
            screen.blit(font.render("BACK", True, COLOR_TEXT), (MAP_WIDTH + 80, 450))

            # Draw Confirm Button
            confirm_btn = pygame.Rect(MAP_WIDTH + 10, 485, 180, 35)
            pygame.draw.rect(screen, COLOR_BUTTON, confirm_btn)
            screen.blit(font.render("CONFIRM RIDE", True, COLOR_TEXT), (MAP_WIDTH + 45, 495))

    elif current_state == "CONFIRMED_RIDE":
        screen.blit(header_font.render("Ride Booked!", True, COLOR_HIGHLIGHT), (MAP_WIDTH + 10, 20))
        screen.blit(font.render(f"Driver: {selected_driver['id']}", True, COLOR_TEXT), (MAP_WIDTH + 10, 60))
        screen.blit(font.render(f"Price:  ${selected_driver['price']}", True, COLOR_TEXT), (MAP_WIDTH + 10, 90))
        screen.blit(header_font.render(f"ETA:    {estimated_time} mins", True, COLOR_HIGHLIGHT), (MAP_WIDTH + 10, 140))
        
        # Draw Cancel Button
        cancel_rect = pygame.Rect(MAP_WIDTH + 10, 545, 180, 35)
        pygame.draw.rect(screen, (200, 50, 50), cancel_rect)
        screen.blit(font.render("CANCEL RIDE", True, COLOR_TEXT), (MAP_WIDTH + 50, 555))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()