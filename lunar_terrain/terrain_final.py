import opensimplex
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from scipy.ndimage import gaussian_filter

# ------------------------------------------------------------
# 1. Генерация базового шума (очень слабый фон)
# ------------------------------------------------------------
gen = opensimplex.OpenSimplex(seed=2500)
width, height = 300, 300
scale = 0.25

noise_map = np.zeros((height, width))
for y in range(height):
    for x in range(width):
        noise_map[y][x] = gen.noise2(x * scale, y * scale) * 0.02

# ------------------------------------------------------------
# 2. Функция степенного распределения диаметров
# ------------------------------------------------------------
def random_diameter(rng, min_d=2, max_d=70, power=-2.8):
    u = rng.random()
    exp = power + 1
    return (min_d**exp + u * (max_d**exp - min_d**exp)) ** (1/exp)

# ------------------------------------------------------------
# 3. Генерация кратеров с улучшенными параметрами
# ------------------------------------------------------------
num_craters = 2500
rng = np.random.default_rng(42)

# Для контроля пересечений крупных кратеров
large_craters = []   # (cx, cy, D)

for _ in range(num_craters):
    D = random_diameter(rng, min_d=2, max_d=70, power=-2.8)
    cx = rng.uniform(0, width - 1)
    cy = rng.uniform(0, height - 1)

    # Проверка пересечений для крупных (D > 30)
    if D > 30:
        too_close = False
        for lcx, lcy, lD in large_craters:
            dist = np.hypot(cx - lcx, cy - lcy)
            if dist < (D + lD) * 0.6:
                too_close = True
                break
        if too_close:
            continue
        large_craters.append((cx, cy, D))

    # Улучшенные параметры кратера
    sigma_rim = D * rng.uniform(0.10, 0.18)
    sigma_bowl = D * rng.uniform(0.45, 0.65)
    A_rim = D * rng.uniform(0.005, 0.015)
    A_bowl = A_rim * rng.uniform(4.0, 9.0)   # чаша глубже вала

    # Ограничивающий прямоугольник
    radius = max(3*sigma_rim, 3*sigma_bowl) + 10
    x0 = max(0, int(cx - radius))
    x1 = min(width, int(cx + radius + 1))
    y0 = max(0, int(cy - radius))
    y1 = min(height, int(cy + radius + 1))
    if x0 >= x1 or y0 >= y1:
        continue

    Y_local, X_local = np.ogrid[y0:y1, x0:x1]
    r_local = np.hypot(X_local - cx, Y_local - cy)

    crater_local = A_rim * np.exp(-r_local**2/(2*sigma_rim**2)) - A_bowl * np.exp(-r_local**2/(2*sigma_bowl**2))

    # Ejecta для 50% кратеров
    if rng.random() < 0.5:
        sigma_ejecta = D * rng.uniform(1.8, 4.0)
        A_ejecta = A_rim * rng.uniform(0.1, 0.25)
        ejecta_local = A_ejecta * np.exp(-r_local**2/(2*sigma_ejecta**2))
        crater_local += ejecta_local

    noise_map[y0:y1, x0:x1] += crater_local

# ------------------------------------------------------------
# 4. Добавление морей (большие мягкие понижения)
# ------------------------------------------------------------
num_maria = rng.integers(1, 3)   # 1 или 2
for _ in range(num_maria):
    D = rng.uniform(80, 150)
    cx = rng.uniform(0, width - 1)
    cy = rng.uniform(0, height - 1)
    sigma = D * rng.uniform(1.5, 2.5)
    A = -rng.uniform(0.03, 0.08)   # отрицательная амплитуда

    radius = int(3 * sigma) + 10
    x0 = max(0, int(cx - radius))
    x1 = min(width, int(cx + radius + 1))
    y0 = max(0, int(cy - radius))
    y1 = min(height, int(cy + radius + 1))
    if x0 >= x1 or y0 >= y1:
        continue

    Y_local, X_local = np.ogrid[y0:y1, x0:x1]
    r_local = np.hypot(X_local - cx, Y_local - cy)
    maria_local = A * np.exp(-r_local**2/(2*sigma**2))
    noise_map[y0:y1, x0:x1] += maria_local

# ------------------------------------------------------------
# 5. Мелкий реголит и сглаживание
# ------------------------------------------------------------
for y in range(height):
    for x in range(width):
        noise_map[y][x] += gen.noise2(x * 4.0, y * 4.0) * 0.005

noise_map = gaussian_filter(noise_map, sigma=0.8)

# ------------------------------------------------------------
# 6. Нормализация в узкий диапазон высот
# ------------------------------------------------------------
noise_map = (noise_map - noise_map.min()) / (noise_map.max() - noise_map.min())
noise_map = noise_map * 0.1 - 0.05   # теперь от -0.05 до 0.05

# ------------------------------------------------------------
# 7. Освещение (настроенное)
# ------------------------------------------------------------
ls = LightSource(azdeg=310, altdeg=14)
rgb = ls.shade(noise_map, cmap=plt.cm.gray, vert_exag=0.7, blend_mode='soft')

# ------------------------------------------------------------
# 8. Визуализация и сохранение
# ------------------------------------------------------------
plt.figure(figsize=(10, 8))
plt.imshow(rgb, interpolation='bicubic')

plt.axis('off')
plt.title('Лунная поверхность (финальная версия)')
plt.tight_layout()
plt.savefig('lunar_surface_final.png', dpi=300, bbox_inches='tight', pad_inches=0)
plt.show()