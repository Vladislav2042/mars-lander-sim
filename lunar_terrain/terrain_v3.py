import opensimplex
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from scipy.ndimage import gaussian_filter

# Генератор базового шума
gen = opensimplex.OpenSimplex(seed=2500)

width, height = 300, 300
scale = 0.25

# Базовая карта (очень слабый шум)
noise_map = np.zeros((height, width))
for y in range(height):
    for x in range(width):
        noise_map[y][x] = gen.noise2(x * scale, y * scale) * 0.02  # уменьшил амплитуду


# Функция степенного закона
def random_diameter(rng, min_d=2, max_d=70, power=-2.8):
    u = rng.random()
    exp = power + 1
    return (min_d ** exp + u * (max_d ** exp - min_d ** exp)) ** (1 / exp)


# Генератор кратеров
num_craters = 2000
rng = np.random.default_rng(42)  # seed для воспроизводимости

# Список для хранения крупных кратеров (чтобы проверять пересечения)
large_craters = []  # каждый элемент: (cx, cy, D)

for _ in range(num_craters):
    D = random_diameter(rng, min_d=2, max_d=70, power=-2.8)
    cx = rng.uniform(0, width - 1)
    cy = rng.uniform(0, height - 1)

    # Проверка пересечений для крупных кратеров (D > 30)
    if D > 30:
        too_close = False
        for lcx, lcy, lD in large_craters:
            dist = np.hypot(cx - lcx, cy - lcy)
            min_dist = (D + lD) * 0.6  # порог
            if dist < min_dist:
                too_close = True
                break
        if too_close:
            continue
        large_craters.append((cx, cy, D))

    # Параметры кратера
    sigma_rim = D * rng.uniform(0.12, 0.25)
    sigma_bowl = D * rng.uniform(0.4, 0.6)
    A_rim = D * rng.uniform(0.005, 0.015)
    A_bowl = A_rim * rng.uniform(2.0, 5.0)

    # Оптимизация: работаем только в bounding box вокруг центра
    radius = max(3 * sigma_rim, 3 * sigma_bowl) + 10
    x0 = max(0, int(cx - radius))
    x1 = min(width, int(cx + radius + 1))
    y0 = max(0, int(cy - radius))
    y1 = min(height, int(cy + radius + 1))

    if x0 >= x1 or y0 >= y1:
        continue

    # Локальная сетка
    Y_local, X_local = np.ogrid[y0:y1, x0:x1]
    r_local = np.sqrt((X_local - cx) ** 2 + (Y_local - cy) ** 2)

    crater_local = A_rim * np.exp(-r_local ** 2 / (2 * sigma_rim ** 2)) - A_bowl * np.exp(
        -r_local ** 2 / (2 * sigma_bowl ** 2))

    # Добавляем ejecta для 30% кратеров
    if rng.random() < 0.3:
        sigma_ejecta = D * rng.uniform(1.5, 3.0)
        A_ejecta = A_rim * rng.uniform(0.05, 0.2)
        ejecta_local = A_ejecta * np.exp(-r_local ** 2 / (2 * sigma_ejecta ** 2))
        crater_local += ejecta_local

    noise_map[y0:y1, x0:x1] += crater_local

# Мелкий шум реголита
for y in range(height):
    for x in range(width):
        noise_map[y][x] += gen.noise2(x * 4.0, y * 4.0) * 0.005

# Лёгкое сглаживание
noise_map = gaussian_filter(noise_map, sigma=0.8)

# Нормализация в узкий диапазон (для реалистичных теней)
noise_map = (noise_map - noise_map.min()) / (noise_map.max() - noise_map.min())
noise_map = noise_map * 0.1 - 0.05  # теперь значения от -0.05 до 0.05

# Освещение
ls = LightSource(azdeg=315, altdeg=20)
rgb = ls.shade(noise_map, cmap=plt.cm.gray, vert_exag=0.8, blend_mode='overlay')

# Отображение
plt.figure(figsize=(8, 8))
plt.imshow(rgb)
plt.axis('off')
plt.title('Лунная поверхность (улучшенная)')
plt.show()