import sqlite3
from config import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature


class DB_Map():
    def __init__(self, database):
        self.database = database

    DEFAULT_MARKER_COLOR = 'red'
    MARKER_COLORS = {
        'Красный': 'red',
        'Синий': 'blue',
        'Зелёный': 'green',
        'Оранжевый': 'orange',
        'Фиолетовый': 'purple',
        'Чёрный': 'black',
    }
    
    def create_user_table(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS users_cities (
                                user_id INTEGER,
                                city_id TEXT,
                                FOREIGN KEY(city_id) REFERENCES cities(id)
                            )''')
            conn.execute('''CREATE TABLE IF NOT EXISTS users_map_settings (
                                user_id INTEGER PRIMARY KEY,
                                marker_color TEXT NOT NULL
                            )''')
            conn.commit()

    def set_marker_color(self, user_id, marker_color):
        if marker_color not in self.MARKER_COLORS.values():
            raise ValueError(f'Недопустимый цвет маркера: {marker_color}')

        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute(
                '''INSERT OR REPLACE INTO users_map_settings (user_id, marker_color)
                   VALUES (?, ?)''',
                (user_id, marker_color)
            )

    def get_marker_color(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT marker_color FROM users_map_settings WHERE user_id = ?',
                (user_id,)
            )
            color = cursor.fetchone()

        if color is None:
            return self.DEFAULT_MARKER_COLOR
        if color[0] not in self.MARKER_COLORS.values():
            raise ValueError(f'Недопустимый цвет маркера в настройках: {color[0]}')
        return color[0]

    def add_city(self,user_id, city_name ):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM cities WHERE city=?", (city_name,))
            city_data = cursor.fetchone()
            if city_data:
                city_id = city_data[0]  
                conn.execute('INSERT INTO users_cities VALUES (?, ?)', (user_id, city_id))
                conn.commit()
                return 1
            else:
                return 0

            
    def select_cities(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT cities.city 
                            FROM users_cities  
                            JOIN cities ON users_cities.city_id = cities.id
                            WHERE users_cities.user_id = ?''', (user_id,))

            cities = [row[0] for row in cursor.fetchall()]
            return cities


    def select_cities_by_country(self, country):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT city FROM cities WHERE country = ? COLLATE NOCASE ORDER BY city',
                (country.strip(),)
            )
            return [row[0] for row in cursor.fetchall()]


    def get_coordinates(self, city_name):
        conn = sqlite3.connect(self.database)
        with conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT lat, lng
                            FROM cities  
                            WHERE city = ?''', (city_name,))
            coordinates = cursor.fetchone()
            return coordinates

    def create_grapf(self, path, cities, marker_color=DEFAULT_MARKER_COLOR):
        if marker_color not in self.MARKER_COLORS.values():
            raise ValueError(f'Недопустимый цвет маркера: {marker_color}')

        figure, ax = plt.subplots(
            figsize=(12, 6),
            subplot_kw={'projection': ccrs.PlateCarree()}
        )
        try:
            ax.set_global()
            ax.add_feature(cfeature.OCEAN, facecolor='#a6cee3', zorder=0)
            ax.add_feature(cfeature.LAND, facecolor='#f2e8cf', zorder=0)
            ax.add_feature(cfeature.LAKES, facecolor='#a6cee3', edgecolor='#5b8db8', linewidth=0.4)
            ax.add_feature(cfeature.RIVERS, edgecolor='#5b8db8', linewidth=0.4)
            ax.add_feature(cfeature.COASTLINE, linewidth=0.6)
            ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)

            for city in cities:
                coordinates = self.get_coordinates(city)

                if coordinates:
                    lat, lng = coordinates
                    ax.plot(
                        [lng], [lat],
                        marker='o',
                        linestyle='None',
                        markerfacecolor=marker_color,
                        markeredgecolor='black',
                        markersize=7,
                        transform=ccrs.PlateCarree()
                    )
                    ax.text(
                        lng + 3, lat + 2, city,
                        horizontalalignment='left',
                        transform=ccrs.PlateCarree()
                    )

            figure.savefig(path, bbox_inches='tight')
        finally:
            plt.close(figure)
        
    def draw_distance(self, city1, city2):
        pass


if __name__=="__main__":
    
    m = DB_Map(DATABASE)
    m.create_user_table()
