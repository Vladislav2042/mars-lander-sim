# rocket_mars.py - Полная модель посадочного модуля для Марса с вращением и фиксом отскока
import numpy as np
import config as cfg
from landing_leg import LandingLeg


class RocketMars:
    """Модель посадочного модуля для Марса с отладками."""

    def __init__(self):
        print("\n" + "=" * 50)
        print("ИНИЦИАЛИЗАЦИЯ РАКЕТЫ")
        print("=" * 50)
        # Параметры модуля из конфига
        self.length = cfg.ROCKET_LENGTH
        self.width = cfg.ROCKET_WIDTH
        self.mass = cfg.ROCKET_MASS
        self.g = cfg.GRAVITY

        print(f"Параметры: масса={self.mass}кг, g={self.g}м/с²")
        print(f"Вес на Марсе: {self.mass * self.g:.0f} Н")

        # Момент инерции
        self.I = (1 / 12) * self.mass * (self.width ** 2 + self.length ** 2)

        # Начальное состояние [x, y, phi, Vx, Vy, omega]
        self.state = np.array([
            cfg.INITIAL_POSITION[0], cfg.INITIAL_POSITION[1], cfg.INITIAL_ANGLE,
            cfg.INITIAL_VELOCITY[0], cfg.INITIAL_VELOCITY[1], cfg.INITIAL_ANGULAR_VELOCITY
        ])

        print(
            f"Начальное состояние: y={self.state[1]:.0f}м, Vy={self.state[4]:.0f}м/с, phi={np.degrees(self.state[2]):.1f}°")

        # Управление: Тяга и момент
        self.thrust = 0.0
        self.max_thrust = cfg.MAX_THRUST
        self.torque = 0.0
        self.max_torque = cfg.MAX_TORQUE

        # УВЕЛИЧЕННАЯ чувствительность для ручного вращения
        self.manual_torque_sensitivity = 80.0

        print(f"Управление: max_thrust={self.max_thrust}Н, max_torque={self.max_torque}Н·м")
        print(f"Чувствительность вращения: {self.manual_torque_sensitivity}Н·м/нажатие")

        # Посадочные опоры (2 ноги)
        leg_positions = [
            [cfg.LEG_ATTACHMENT_X_OFFSET, cfg.LEG_ATTACHMENT_Y],
            [-cfg.LEG_ATTACHMENT_X_OFFSET, cfg.LEG_ATTACHMENT_Y]
        ]
        self.legs = [LandingLeg(pos,
                                cfg.LEG_REST_LENGTH,
                                cfg.LEG_SPRING_CONSTANT,
                                cfg.LEG_DAMPING_CONSTANT,
                                cfg.LEG_MAX_COMPRESSION)
                     for pos in leg_positions]

        print(f"Создано опор: {len(self.legs)}")

        # Парашют
        self.parachute_open = False
        self.parachute_deploy_height = cfg.PARACHUTE_DEPLOY_HEIGHT
        self.parachute_deploy_speed = cfg.PARACHUTE_DEPLOY_SPEED

        print(f"Парашют: откроется на высоте < {self.parachute_deploy_height}м")
        print(f"          при скорости < {self.parachute_deploy_speed}м/с")

        # Автопилот и режимы
        self.control_mode = 'MANUAL'  # 'MANUAL' или 'AUTO'
        self.auto_submode = None
        self.landing_phase = None
        self.target_height = 0.0
        self.target_vy = cfg.TARGET_VY
        self.target_phi = 0.0  # В авторежиме всегда выравниваем до 0°

        # ПИД регуляторы
        self.integral_vy_error = 0.0
        self.integral_phi_error = 0.0
        self.integral_height_error = 0.0
        self.prev_vy_error = 0.0
        self.prev_phi_error = 0.0
        self.prev_height_error = 0.0

        # Коэффициенты из конфига
        self.Kp_vy = cfg.KP_VY
        self.Ki_vy = cfg.KI_VY
        self.Kd_vy = cfg.KD_VY
        self.Kp_phi = cfg.KP_PHI
        self.Ki_phi = cfg.KI_PHI
        self.Kd_phi = cfg.KD_PHI
        self.Kp_height = cfg.KP_HEIGHT
        self.Ki_height = cfg.KI_HEIGHT
        self.Kd_height = cfg.KD_HEIGHT

        print(f"PID коэффициенты: Kp_phi={self.Kp_phi}, Ki_phi={self.Ki_phi}, Kd_phi={self.Kd_phi}")

        # Параметры фаз посадки
        self.descent_vy = cfg.DESCENT_VY
        self.final_height_threshold = cfg.FINAL_HEIGHT
        self.touchdown_height = cfg.TOUCHDOWN_HEIGHT
        self.min_vy = cfg.MIN_VY

        # История данных
        self.history = {
            't': [], 'x': [], 'y': [], 'phi': [], 'Vx': [], 'Vy': [], 'omega': [],
            'thrust': [], 'torque': [], 'drag': [], 'contact_forces': [],
            'control_mode': [], 'auto_submode': [], 'landing_phase': []
        }

        # Время и флаг посадки
        self.simulation_time = 0.0
        self.landed = False
        self.landing_successful = False

        # Диагностика
        self.debug = True  # Всегда включаем отладку для тестов

        print("=" * 50 + "\n")

    def rotation_matrix(self):
        """Матрица поворота."""
        phi = self.state[2]
        c, s = np.cos(phi), np.sin(phi)
        return np.array([[c, -s], [s, c]])

    def get_density(self, y):
        """Плотность атмосферы Марса."""
        if y < 0:
            y = 0

        density = cfg.AIR_DENSITY_SURFACE * np.exp(-y / cfg.SCALE_HEIGHT)

        if self.debug and y < 50000 and y % 10000 < 100:
            print(f"Атмосфера: y={y:.0f}м, ρ={density:.6f} кг/м³")

        return density

    def dynamics(self):
        """Уравнения движения. Возвращает derivs и drag_mag."""
        x, y, phi, Vx, Vy, omega = self.state
        V = np.sqrt(Vx ** 2 + Vy ** 2)

        # Избегаем деления на ноль
        if V > 0.1:
            V_dir = np.array([Vx, Vy]) / V
        else:
            V_dir = np.array([0.0, 0.0])

        # Гравитация
        gravity_force = np.array([0.0, -self.mass * self.g])

        # Аэродинамическое сопротивление
        rho = self.get_density(y)
        drag_mag = 0.5 * rho * cfg.DRAG_COEFFICIENT_AEROSHELL * cfg.AEROSHELL_AREA * V ** 2

        if self.debug and drag_mag > 100:
            print(f"Сопротивление: V={V:.0f}м/с, F={drag_mag:.0f}Н")

        # Парашют
        if self.parachute_open:
            para_mag = 0.5 * rho * cfg.DRAG_COEFFICIENT_PARACHUTE * cfg.PARACHUTE_AREA * V ** 2
            drag_mag += para_mag

            if self.debug:
                print(f"Парашют: F={para_mag:.0f}Н")

        drag_force = -drag_mag * V_dir if V > 0.1 else np.array([0.0, 0.0])

        # Тяга двигателя (в локальной системе)
        thrust_local = np.array([0.0, self.thrust])
        R = self.rotation_matrix()
        thrust_global = R @ thrust_local

        # Суммарная сила
        total_force = gravity_force + drag_force + thrust_global
        acceleration = total_force / self.mass

        if self.debug and abs(self.thrust) > 1000:
            print(f"Тяга: локальная={self.thrust:.0f}Н, глобальная=[{thrust_global[0]:.0f},{thrust_global[1]:.0f}]")

        # Моменты от тяги (создает вращение если двигатель не по центру)
        engine_local = np.array([0.0, cfg.ENGINE_POSITION_Y])
        moment_from_thrust = engine_local[0] * thrust_local[1] - engine_local[1] * thrust_local[0]

        # Демпфирование вращения
        moment_damping = -cfg.ROTATION_DAMPING * self.I * omega

        # Суммарный момент (ВКЛЮЧАЕМ ручной torque!)
        total_moment = moment_from_thrust + self.torque + moment_damping
        alpha = total_moment / self.I

        if self.debug and abs(total_moment) > 10:
            print(f"Моменты: от тяги={moment_from_thrust:.1f}, ручной={self.torque:.1f}, "
                  f"демпфирование={moment_damping:.1f}, сумма={total_moment:.1f}, alpha={alpha:.3f} рад/с²")

        return np.array([Vx, Vy, omega, acceleration[0], acceleration[1], alpha]), drag_mag

    def switch_mode(self, new_mode, submode=None):
        """Переключение режимов с сбросом интегралов."""
        print(f"\n[РЕЖИМ] {self.control_mode} -> {new_mode}")

        if new_mode != self.control_mode:
            # Сброс интегральных составляющих
            self.integral_vy_error = 0.0
            self.integral_phi_error = 0.0
            self.integral_height_error = 0.0
            self.prev_vy_error = 0.0
            self.prev_phi_error = 0.0
            self.prev_height_error = 0.0

            # Сброс target_vy при переходе в LANDING
            if submode == 'LANDING':
                self.target_vy = cfg.TARGET_VY  # -1.0 м/с
                print(f"[AUTO] Установлен target_vy={self.target_vy} м/с для посадки")

        self.control_mode = new_mode

        if new_mode == 'AUTO':
            if submode:
                self.auto_submode = submode

                if submode == 'HOVER':
                    self.target_height = self.state[1]
                    print(f"[AUTO] Режим HOVER на высоте {self.target_height:.1f} м")

                elif submode == 'ASCENT':
                    print("[AUTO] Режим ASCENT активирован")

                elif submode == 'LANDING':
                    self.landing_phase = 'DESCENT'
                    self.target_vy = cfg.TARGET_VY  # Гарантируем -1.0 м/с
                    print("[AUTO] Начало процедуры посадки")

            else:
                # Автоматический выбор подрежима по высоте
                if self.state[1] < cfg.THRUSTERS_ACTIVATE_HEIGHT:
                    self.auto_submode = 'LANDING'
                else:
                    self.auto_submode = 'HOVER'

    def autopilot(self, dt):
        """Автопилот."""
        y, Vy, phi, omega = self.state[1], self.state[4], self.state[2], self.state[5]

        # Вычисление ошибки угла
        phi_error = self.target_phi - phi
        d_phi_error = (phi_error - self.prev_phi_error) / dt if dt > 0 else 0.0
        self.integral_phi_error += phi_error * dt
        self.prev_phi_error = phi_error

        # ПИД для угла (момент)
        self.torque = (self.Kp_phi * phi_error +
                       self.Ki_phi * self.integral_phi_error +
                       self.Kd_phi * d_phi_error)
        self.torque = np.clip(self.torque, -self.max_torque, self.max_torque)

        if abs(self.torque) > 10 and self.debug:
            print(f"PID угла: error={np.degrees(phi_error):.1f}°, "
                  f"P={self.Kp_phi * phi_error:.1f}, I={self.Ki_phi * self.integral_phi_error:.1f}, "
                  f"D={self.Kd_phi * d_phi_error:.1f}, torque={self.torque:.1f}Н·м")

        # Подрежимы
        if self.auto_submode == 'HOVER':
            height_error = self.target_height - y
            d_height_error = (height_error - self.prev_height_error) / dt if dt > 0 else 0.0
            self.integral_height_error += height_error * dt
            self.prev_height_error = height_error

            # ПИД для высоты
            thrust_command = (self.Kp_height * height_error +
                              self.Ki_height * self.integral_height_error +
                              self.Kd_height * d_height_error)
            self.thrust = self.mass * self.g + thrust_command  # Компенсация гравитации
            self.thrust = np.clip(self.thrust, 0.0, self.max_thrust)

        elif self.auto_submode == 'ASCENT':
            self.target_vy = cfg.ASCENT_VY

            vy_error = self.target_vy - Vy
            d_vy_error = (vy_error - self.prev_vy_error) / dt if dt > 0 else 0.0
            self.integral_vy_error += vy_error * dt
            self.prev_vy_error = vy_error

            # ПИД для скорости
            thrust_command = (self.Kp_vy * vy_error +
                              self.Ki_vy * self.integral_vy_error +
                              self.Kd_vy * d_vy_error)
            self.thrust = self.mass * self.g + thrust_command
            self.thrust = np.clip(self.thrust, 0.0, self.max_thrust)

        elif self.auto_submode == 'LANDING':
            if self.landing_phase == 'DESCENT':
                if y > self.final_height_threshold:
                    self.target_vy = self.descent_vy
                else:
                    self.target_vy = cfg.TARGET_VY  # Медленный спуск
                    self.landing_phase = 'FINAL_DESCENT'
                    print("[AUTO] Переход в FINAL_DESCENT")

            # Улучшенная логика выключения тяги: проверка контакта опор
            if self.state[1] < cfg.LEGS_ACTIVATE_HEIGHT:
                total_leg_force, _, _ = self.update_leg_forces(dt)
                if total_leg_force[1] > self.mass * self.g * 0.5:  # Если сила от опор > 50% веса
                    self.thrust = 0.0
                    self.landing_phase = 'TOUCHDOWN'
                    print("[AUTO] Контакт обнаружен, тяга выключена")
                    return  # Выходим из автопилота, чтобы не пересчитывать thrust

            vy_error = self.target_vy - Vy
            d_vy_error = (vy_error - self.prev_vy_error) / dt if dt > 0 else 0.0
            self.integral_vy_error += vy_error * dt
            self.prev_vy_error = vy_error

            # ПИД для скорости
            thrust_command = (self.Kp_vy * vy_error +
                              self.Ki_vy * self.integral_vy_error +
                              self.Kd_vy * d_vy_error)
            self.thrust = self.mass * self.g + thrust_command
            self.thrust = np.clip(self.thrust, 0.0, self.max_thrust)

            if self.debug:
                print(f"PID Vy: error={vy_error:.2f}м/с, thrust={self.thrust:.0f}Н")

    def update_leg_forces(self, dt):
        """Расчет сил от посадочных опор."""
        R = self.rotation_matrix()
        total_force = np.zeros(2)
        total_moment = 0.0
        contact_forces = []

        for leg in self.legs:
            # Позиция крепления в глобальных координатах
            attach_world = self.state[0:2] + R @ leg.attachment_local

            # Позиция "стопы" (нижней точки опоры)
            foot_world = attach_world + np.array([0.0, -leg.rest_length])

            # Скорость точки крепления из-за вращения
            V_rot = np.array([-self.state[5] * leg.attachment_local[1],
                              self.state[5] * leg.attachment_local[0]])

            # Полная скорость "стопы"
            foot_velocity = self.state[3:5] + R @ V_rot

            # Обновление силы опоры
            leg_force = leg.update(dt, foot_world, foot_velocity)
            total_force += leg_force

            # Момент от силы опоры
            r = R @ leg.attachment_local
            moment_leg = r[0] * leg_force[1] - r[1] * leg_force[0]
            total_moment += moment_leg

            contact_forces.append(leg.force)

            if leg.force > 100 and self.debug:
                print(f"  Опора: сила={leg.force:.0f}Н, сжатие={leg.compression:.3f}м")

        return total_force, total_moment, contact_forces

    def check_landing_criteria(self):
        """Проверка критериев успешной посадки."""
        if self.landed:
            return self.landing_successful

        y, Vy, Vx, phi, omega = self.state[1], self.state[4], self.state[3], self.state[2], self.state[5]

        # Проверяем основные критерии
        vertical_speed_ok = abs(Vy) <= cfg.MAX_SAFE_LANDING_VY
        horizontal_speed_ok = abs(Vx) <= cfg.MAX_SAFE_LANDING_VX
        angle_ok = abs(np.degrees(phi)) <= cfg.MAX_SAFE_LANDING_ANGLE
        angular_velocity_ok = abs(np.degrees(omega)) <= cfg.MAX_SAFE_ANGULAR_VELOCITY

        # Все опоры должны контактировать
        contact_ok = all(leg.force > cfg.MIN_CONTACT_FORCE for leg in self.legs)

        self.landing_successful = (vertical_speed_ok and horizontal_speed_ok and
                                   angle_ok and angular_velocity_ok and contact_ok)

        return self.landing_successful

    def get_derivs(self):
        """Вычисление полных производных (динамика + силы опор)."""
        derivs, drag = self.dynamics()
        if self.state[1] < cfg.LEGS_ACTIVATE_HEIGHT:
            leg_force, leg_moment, _ = self.update_leg_forces(cfg.TIME_STEP)  # dt не используется, но передаем
            derivs[3:5] += leg_force / self.mass
            derivs[5] += leg_moment / self.I
        return derivs, drag

    def update(self, dt):
        """Основной цикл симуляции с RK4 интеграцией."""
        if self.landed:
            self.state[3:6] = 0.0  # Заморозка скоростей
            self.thrust = 0.0
            self.torque = 0.0
            return False

        self.simulation_time += dt

        if self.debug and self.simulation_time % 2.0 < dt:
            print(f"\n[t={self.simulation_time:.1f}с] y={self.state[1]:.0f}м, "
                  f"Vy={self.state[4]:.0f}м/с, phi={np.degrees(self.state[2]):.1f}°, "
                  f"omega={np.degrees(self.state[5]):.1f}°/с")

        # ===== АКТИВАЦИЯ ПАРАШЮТА =====
        if not self.parachute_open:
            V = np.sqrt(self.state[3] ** 2 + self.state[4] ** 2)
            if (self.state[1] < self.parachute_deploy_height and
                    V < self.parachute_deploy_speed):
                self.parachute_open = True
                print(f"\n[ПАРАШЮТ] ОТКРЫТ! Высота={self.state[1]:.0f}м, V={V:.0f}м/с")

        # ===== АВТОМАТИЧЕСКОЕ ПЕРЕКЛЮЧЕНИЕ РЕЖИМОВ =====
        if self.control_mode == 'AUTO' and self.auto_submode is None:
            if self.state[1] < cfg.THRUSTERS_ACTIVATE_HEIGHT:
                self.switch_mode('AUTO', 'LANDING')
            else:
                self.switch_mode('AUTO', 'HOVER')

        # ===== УПРАВЛЕНИЕ =====
        if self.control_mode == 'AUTO':
            self.autopilot(dt)

        # ===== RK4 ИНТЕГРИРОВАНИЕ =====
        original_state = self.state.copy()

        # k1
        k1, _ = self.get_derivs()

        # k2
        self.state = original_state + 0.5 * dt * k1
        k2, _ = self.get_derivs()

        # k3
        self.state = original_state + 0.5 * dt * k2
        k3, _ = self.get_derivs()

        # k4
        self.state = original_state + dt * k3
        k4, _ = self.get_derivs()

        # Обновление состояния
        self.state = original_state + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)

        # ===== ФИНАЛЬНЫЕ ВЫЧИСЛЕНИЯ ДЛЯ ЛОГИРОВАНИЯ =====
        _, drag = self.dynamics()
        if self.state[1] < cfg.LEGS_ACTIVATE_HEIGHT:
            _, _, contact_forces = self.update_leg_forces(dt)
        else:
            contact_forces = [0.0] * len(self.legs)

        # ===== УСИЛЕННЫЙ ФИКС ВЫСОТЫ И ОТСКОКА =====
        if self.state[1] < 0:
            self.state[1] = 0
            self.state[4] = 0.0  # Полностью гасим Vy

        # Если контакт и Vy > 0 (начало отскока), гасим если малая
        if any(leg.force > cfg.MIN_CONTACT_FORCE for leg in self.legs) and self.state[4] > 0 and self.state[4] < 0.5:
            self.state[4] = 0.0  # Погашение малого отскока

        # ===== СОХРАНЕНИЕ ДАННЫХ =====
        if self.simulation_time % cfg.DATA_LOG_INTERVAL < dt:
            self.history['t'].append(self.simulation_time)
            for i, key in enumerate(['x', 'y', 'phi', 'Vx', 'Vy', 'omega']):
                self.history[key].append(self.state[i])
            self.history['thrust'].append(self.thrust)
            self.history['torque'].append(self.torque)
            self.history['drag'].append(drag)
            self.history['contact_forces'].append(contact_forces)
            self.history['control_mode'].append(self.control_mode)
            self.history['auto_submode'].append(self.auto_submode)
            self.history['landing_phase'].append(self.landing_phase)

            # Ограничение размера истории
            if len(self.history['t']) > cfg.MAX_DATA_POINTS:
                for key in self.history:
                    if len(self.history[key]) > cfg.MAX_DATA_POINTS:
                        self.history[key] = self.history[key][-cfg.MAX_DATA_POINTS:]

        # ===== ПРОВЕРКА ПОСАДКИ =====
        if self.state[1] <= cfg.LANDING_HEIGHT_THRESHOLD and all(
                leg.force > cfg.MIN_CONTACT_FORCE for leg in self.legs):
            self.landed = True
            success = self.check_landing_criteria()

            if success:
                print(f"\n" + "=" * 50)
                print(f"✓ ПОСАДКА УСПЕШНА! Время: {self.simulation_time:.1f} с")
                print(f"  Вертикальная скорость: {self.state[4]:.2f} м/с")
                print(f"  Горизонтальная скорость: {self.state[3]:.2f} м/с")
                print(f"  Угол наклона: {np.degrees(self.state[2]):.1f}°")
                print(f"  Скорость вращения: {np.degrees(self.state[5]):.1f}°/с")
                print("=" * 50)
            else:
                print(f"\n" + "=" * 50)
                print(f"✗ ПОСАДКА НЕУДАЧНА! Время: {self.simulation_time:.1f} с")
                print(f"  Вертикальная скорость: {self.state[4]:.2f} м/с")
                print(f"  Горизонтальная скорость: {self.state[3]:.2f} м/с")
                print(f"  Угол наклона: {np.degrees(self.state[2]):.1f}°")
                print(f"  Скорость вращения: {np.degrees(self.state[5]):.1f}°/с")
                print("=" * 50)

            # Заморозка после посадки и выключение тяги
            self.state[3:6] = 0.0  # Vx, Vy, omega = 0
            self.thrust = 0.0
            self.torque = 0.0
            return False

        return True

    def get_status_text(self):
        """Текстовый статус для HUD."""
        y, Vy, Vx, phi, omega = self.state[1], self.state[4], self.state[3], self.state[2], self.state[5]

        lines = [
            f"Высота: {y:.1f} м",
            f"Вертикальная скорость: {Vy:.1f} м/с",
            f"Горизонтальная скорость: {Vx:.1f} м/с",
            f"Угол: {np.degrees(phi):.1f}°",
            f"Скорость вращения: {np.degrees(omega):.1f}°/с",
            f"Тяга: {self.thrust:.0f} Н",
            f"Момент: {self.torque:.1f} Н·м",
            f"Режим: {self.control_mode}",
        ]

        if self.control_mode == 'AUTO':
            lines.append(f"Подрежим: {self.auto_submode}")
            if self.auto_submode == 'LANDING':
                lines.append(f"Фаза: {self.landing_phase}")

        if self.parachute_open:
            lines.append("Парашют: ОТКРЫТ")
        else:
            lines.append("Парашют: ЗАКРЫТ")

        if any(leg.force > 0 for leg in self.legs):
            lines.append(f"Контакты: {sum(1 for leg in self.legs if leg.force > 0)}/{len(self.legs)}")

        return lines

    def get_hud_data(self):
        """Данные для отображения в HUD."""
        return {
            'altitude': self.state[1],
            'vertical_velocity': self.state[4],
            'horizontal_velocity': self.state[3],
            'angle': np.degrees(self.state[2]),
            'angular_velocity': np.degrees(self.state[5]),
            'thrust_percent': (self.thrust / self.max_thrust) * 100,
            'torque_percent': (self.torque / self.max_torque) * 100,
            'control_mode': self.control_mode,
            'auto_submode': self.auto_submode,
            'landing_phase': self.landing_phase,
            'parachute_open': self.parachute_open,
            'leg_contacts': sum(1 for leg in self.legs if leg.force > cfg.MIN_CONTACT_FORCE),
            'landed': self.landed,
            'landing_successful': self.landing_successful,
            'simulation_time': self.simulation_time
        }

    def reset(self):
        """Сброс симуляции в начальное состояние."""
        self.__init__()

    def manual_control(self, thrust_change=0, torque_change=0):
        """Ручное управление (для вызова из визуализатора)."""
        if self.control_mode == 'MANUAL':
            self.thrust += thrust_change * cfg.MANUAL_THRUST_SENSITIVITY
            self.thrust = np.clip(self.thrust, 0.0, self.max_thrust)

            self.torque += torque_change * cfg.MANUAL_TORQUE_SENSITIVITY
            self.torque = np.clip(self.torque, -self.max_torque, self.max_torque)