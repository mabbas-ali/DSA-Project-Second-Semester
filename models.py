import csv

CSV_FILE = "drivers_data.csv"

#Creates a car dictionary
def create_car(x, y, car_id, price):
    return {"x": x, "y": y, "id": car_id, "price": price}

#Creates rectangle dictionary
# x,y: centre coordinate
# w,h: width and height
def create_rect(x, y, w, h):
    return {"x": x, "y": y, "w": w, "h": h}

# Add data to csv file
def save_car_to_csv(car):
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([car['id'], car['x'], car['y'], car['price']])

# Create csv file
def initialize_csv():
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Driver_ID", "X_Coordinate", "Y_Coordinate", "Price_per_km"])