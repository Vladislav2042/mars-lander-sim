# main_simple.py - Запуск простой визуализации
import config as cfg
from rocket_mars import RocketMars
from simple_visualization import SimpleMarsVisualizer

def main():
    # Исправляем коэффициенты для низкой высоты
    cfg.KP_VY = 50.0
    cfg.KI_VY = 0.5
    cfg.KD_VY = 5.0
    cfg.KP_PHI = 200.0
    cfg.KD_PHI = 50.0
    cfg.MANUAL_THRUST_SENSITIVITY = 500.0
    cfg.MANUAL_TORQUE_SENSITIVITY = 50.0
    cfg.PARACHUTE_DEPLOY_HEIGHT = 800.0
    
    # Устанавливаем тестовые начальные условия
    cfg.INITIAL_POSITION = [0.0, 200.0]
    cfg.INITIAL_VELOCITY = [0.0, -30.0]
    
    print("Загрузка симуляции посадки на Марс...")
    
    # Создаем ракету
    rocket = RocketMars()
    
    # Стартуем в ручном режиме
    rocket.switch_mode('AUTO', 'LANDING')
    
    # Создаем визуализатор
    visualizer = SimpleMarsVisualizer(rocket, cfg)
    
    # Запускаем
    visualizer.run()

if __name__ == "__main__":
    main()
