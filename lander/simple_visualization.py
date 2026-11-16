# simple_visualization.py - Простая визуализация (166 строк)
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation

class SimpleMarsVisualizer:
    def __init__(self, rocket, config):
        self.rocket = rocket
        self.cfg = config
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        
        # Настройка области
        self.ax.set_xlim(-100, 100)
        self.ax.set_ylim(-20, 180)
        self.ax.set_aspect('equal')
        self.ax.set_facecolor('black')
        
        # Рисуем поверхность Марса
        self.ax.axhline(y=0, color='saddlebrown', linewidth=10, zorder=1)
        self.ax.fill_between([-150, 150], -20, 0, color=(0.5, 0.25, 0.1), alpha=0.8)
        
        # Графические элементы
        self.rocket_body = None
        self.leg1 = None
        self.leg2 = None
        self.parachute = None
        self.thrust_flame = None
        self.info_text = None
        self.time_text = None
        
        self.init_graphics()
    
    def init_graphics(self):
        """Инициализация графических элементов."""
        # Ракета
        self.rocket_body = patches.Rectangle(
            (-4, 0), 8, 16, 
            facecolor='white', edgecolor='gray', linewidth=2, zorder=10
        )
        self.ax.add_patch(self.rocket_body)
        
        # Опоры
        self.leg1 = patches.Rectangle(
            (-6, 0), 2, 3, 
            facecolor='lightgray', edgecolor='darkgray', linewidth=1, zorder=9
        )
        self.leg2 = patches.Rectangle(
            (4, 0), 2, 3, 
            facecolor='lightgray', edgecolor='darkgray', linewidth=1, zorder=9
        )
        self.ax.add_patch(self.leg1)
        self.ax.add_patch(self.leg2)
        
        # Пламя
        self.thrust_flame = patches.Polygon(
            [[-3, -5], [3, -5], [0, -15]],
            facecolor='orange', alpha=0.0, zorder=8
        )
        self.ax.add_patch(self.thrust_flame)
        
        # Парашют
        self.parachute = patches.Polygon(
            [[-10, 30], [10, 30], [0, 50]],
            facecolor='lightblue', alpha=0.0, zorder=5
        )
        self.ax.add_patch(self.parachute)
        
        # Текст
        self.info_text = self.ax.text(
            0.02, 0.98, '',
            transform=self.ax.transAxes,
            fontsize=10,
            color='white',
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='black', alpha=0.7),
            zorder=20
        )
        
        self.time_text = self.ax.text(
            0.98, 0.98, 't = 0.0 с',
            transform=self.ax.transAxes,
            fontsize=10,
            color='yellow',
            verticalalignment='top',
            horizontalalignment='right',
            zorder=20
        )
    
    def update_graphics(self):
        """Обновление графики."""
        x, y, phi = self.rocket.state[0], self.rocket.state[1], self.rocket.state[2]
        
        # Ракета
        self.rocket_body.set_xy((-4 + x, y))
        rotation = plt.matplotlib.transforms.Affine2D().rotate_around(x, y + 8, phi)
        self.rocket_body.set_transform(rotation + self.ax.transData)
        
        # Опоры
        leg_rotation = plt.matplotlib.transforms.Affine2D().rotate_around(x, y, phi)
        self.leg1.set_xy((-6 + x, y))
        self.leg1.set_transform(leg_rotation + self.ax.transData)
        self.leg2.set_xy((4 + x, y))
        self.leg2.set_transform(leg_rotation + self.ax.transData)
        
        # Пламя
        if self.rocket.thrust > 100:
            self.thrust_flame.set_xy([[-3 + x, y - 5], [3 + x, y - 5], [x, y - 15]])
            flame_rotation = plt.matplotlib.transforms.Affine2D().rotate_around(x, y, phi)
            self.thrust_flame.set_transform(flame_rotation + self.ax.transData)
            self.thrust_flame.set_alpha(0.8)
        else:
            self.thrust_flame.set_alpha(0.0)
        
        # Парашют
        if self.rocket.parachute_open:
            self.parachute.set_xy([[-10 + x, y + 15], [10 + x, y + 15], [x, y + 35]])
            self.parachute.set_alpha(0.8)
        else:
            self.parachute.set_alpha(0.0)
        
        # Информация
        info = (
            f"Высота: {y:.1f} м\n"
            f"Скорость: {self.rocket.state[4]:.1f} м/с\n"
            f"Угол: {np.degrees(phi):.1f}°\n"
            f"Тяга: {self.rocket.thrust:.0f} Н\n"
            f"Режим: {self.rocket.control_mode}"
        )
        if self.rocket.control_mode == 'AUTO':
            info += f"\nПодрежим: {self.rocket.auto_submode}"
        self.info_text.set_text(info)
        
        # Время
        self.time_text.set_text(f"t = {self.rocket.simulation_time:.1f} с")
        
        # Результат посадки
        if self.rocket.landed:
            status = "✓ УСПЕХ" if self.rocket.landing_successful else "✗ АВАРИЯ"
            self.ax.text(0.5, 0.5, status,
                        transform=self.ax.transAxes,
                        fontsize=24, 
                        color='green' if self.rocket.landing_successful else 'red',
                        ha='center', va='center',
                        bbox=dict(boxstyle='round', facecolor='black', alpha=0.9))
    
    def setup_keyboard_controls(self):
        """Настройка управления клавиатурой."""
        def on_key_press(event):
            if event.key == 'up':
                self.rocket.manual_control(thrust_change=+1)
            elif event.key == 'down':
                self.rocket.manual_control(thrust_change=-1)
            elif event.key == 'left':
                self.rocket.manual_control(torque_change=-1)
            elif event.key == 'right':
                self.rocket.manual_control(torque_change=+1)
            elif event.key == 'a':
                self.rocket.switch_mode('AUTO', 'LANDING')
            elif event.key == 'm':
                self.rocket.switch_mode('MANUAL')
            elif event.key == 'r':
                self.rocket.reset()
        
        self.fig.canvas.mpl_connect('key_press_event', on_key_press)
    
    def run(self):
        """Запуск визуализации."""
        self.setup_keyboard_controls()
        
        def animate(frame):
            if not self.rocket.landed:
                self.rocket.update(self.cfg.TIME_STEP)
            self.update_graphics()
            return [self.rocket_body, self.leg1, self.leg2, 
                   self.thrust_flame, self.parachute,
                   self.info_text, self.time_text]
        
        ani = FuncAnimation(
            self.fig, animate,
            frames=None,
            interval=self.cfg.TIME_STEP * 1000,
            blit=False,
            repeat=False
        )
        
        print("\n" + "="*50)
        print("ПРОСТАЯ ВИЗУАЛИЗАЦИЯ ПОСАДКИ НА МАРС")
        print("="*50)
        print("Управление:")
        print("  Стрелки ↑/↓ - тяга")
        print("  Стрелки ←/→ - вращение")
        print("  A - авторежим посадки")
        print("  M - ручной режим")
        print("  R - сброс")
        print("="*50)
        
        plt.tight_layout()
        plt.show()
