import opensimplex
import numpy as np
import matplotlib.pyplot as plt


gen = opensimplex.OpenSimplex(seed=2500)


width, height = 1000, 1000

scale = 0.25

noise_map = np.zeros((height, width))


for y in range(height):
    for x in range(width):

        noise_map[y][x] = gen.noise2(x * scale, y * scale) * 0.05



num_craters = 30
rng = np.random.default_rng()
for _ in range(num_craters):

    cx = rng.uniform(0, width - 1)
    cy = rng.uniform(0, height - 1)


    sigma_rim = rng.uniform(15, 40)
    sigma_bowl = sigma_rim * rng.uniform(0.3, 0.7)
    A_rim = rng.uniform(0.1, 0.3)
    A_bowl = A_rim * rng.uniform(1.5, 3.0)


    Y, X = np.ogrid[:height, :width]
    r = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)


    crater = A_rim * np.exp(-r ** 2 / (2 * sigma_rim ** 2)) - A_bowl * np.exp(-r ** 2 / (2 * sigma_bowl ** 2))
    noise_map += crater
plt.imshow(noise_map, cmap= 'gist_gray' )
plt.colorbar()
plt.title('Ландшафт')
plt.show()