import opensimplex
import numpy as np
import matplotlib.pyplot as plt

gen = opensimplex.OpenSimplex(seed=2500)

width, height = 300, 300
scale = 0.25

noise_map = np.zeros((height, width))

for y in range(height):
    for x in range(width):
        noise_map[y][x] = gen.noise2(x * scale, y * scale) * 0.05


# Функция для генерации диаметра по степенному закону
def random_diameter(rng, min_d=3, max_d=70, power=-3):
    u = rng.random()
    # power+1 может быть отрицательным, но формула работает
    exp = power + 1
    d = (min_d ** exp + u * (max_d ** exp - min_d ** exp)) ** (1 / exp)
    return d


num_craters = 500  # увеличим количество
rng = np.random.default_rng()  # для воспроизводимости

for _ in range(num_craters):
    # Генерируем диаметр
    D = random_diameter(rng, min_d=3, max_d=70, power=-3)

    # Координаты центра
    cx = rng.uniform(0, width - 1)
    cy = rng.uniform(0, height - 1)

    # Параметры кратера пропорциональны D
    sigma_rim = D * 0.2  # примерное соотношение
    sigma_bowl = sigma_rim * rng.uniform(0.3, 0.7)

    A_rim = D * rng.uniform(0.005, 0.02)
    A_bowl = A_rim * rng.uniform(1.5, 3.0)

    # Создаём сетку
    Y, X = np.ogrid[:height, :width]
    r = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)

    crater = A_rim * np.exp(-r ** 2 / (2 * sigma_rim ** 2)) - A_bowl * np.exp(-r ** 2 / (2 * sigma_bowl ** 2))
    noise_map += crater

from matplotlib.colors import LightSource

ls = LightSource(azdeg=315, altdeg=30)
rgb = ls.shade(noise_map, cmap=plt.cm.gray, vert_exag=1.0, blend_mode='soft')
plt.imshow(rgb)
plt.imshow(noise_map, cmap='gist_gray')
plt.colorbar()
plt.title('Ландшафт')
plt.show()