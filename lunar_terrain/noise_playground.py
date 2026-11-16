import random
value = random.random()
print(value)
#Возвращает случайное число с плавающей точкой в полуинтервале [0.0, 1.0)
# Бросаем шестигранный кубик
dice_roll = random.randint(1, 6) # диапазон от 1 до 6
print(f"Выпало: {dice_roll}")
temperature =  random.uniform(15.5,25.5) # для float
print(f'Температура:{temperature:.2f}')
players = ["Анна", "Борис", "Виктор", "Дарья"]
winner = random.choice(players)
print(f"Победитель: {winner}")


import numpy as np
print(np.random.random(6)) # возвращает массив чисел типа float в диапазоне от 0.0 до 1.0.
print(np.random.randint(0, 10, size=10))
print(np.random.rand(3, 3))

# это устаревшее, новая через rng
rng = np.random.default_rng(seed=42) # создается зерно
arr = rng.random(10)
print(arr)

vals = rng.uniform(-1, 1, (3, 4))
print(vals)

coords = rng.integers(0, 500, size=(10, 2)) #  Целые числа из диапазона [low, high)
print(coords)

# Одно число с μ=0, σ=1
noise = rng.normal(0, 1)
# Массив 100 чисел с μ=5, σ=2
noises = rng.normal(5, 2, 100)
# Для добавления шума к изображению: массив той же формы, что и карта
noise_map = rng.normal(0, 0.1, size=(500, 500))

arr = np.arange(10)
rng.shuffle(arr)  # перемешивает на месте
# или получить перемешанную копию
shuffled = rng.permutation(arr)