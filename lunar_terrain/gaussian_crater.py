import numpy as np
import matplotlib.pyplot as plt

# Параметры кратера
x0, y0 = 50, 50          # центр
sigma_rim = 15           # ширина внешнего вала
sigma_bowl = 8           # ширина внутренней чаши
A_rim = 1.0              # высота вала
A_bowl = 1.8             # глубина чаши (отрицательная)

# Сетка координат
X, Y = np.meshgrid(np.arange(100), np.arange(100))
R = np.sqrt((X - x0)**2 + (Y - y0)**2)

# Кратер: внешний вал (положительный) минус чаша (тоже положительная, но мы её вычтем)
crater = A_rim * np.exp(-R**2 / (2 * sigma_rim**2)) - A_bowl * np.exp(-R**2 / (2 * sigma_bowl**2))

# Визуализация
plt.imshow(crater, cmap='terrain', origin='lower')
plt.colorbar(label='Высота')
plt.title('Кратер, созданный комбинацией двух гауссиан')
plt.show()