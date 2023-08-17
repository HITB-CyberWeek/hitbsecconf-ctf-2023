import random
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

# Генерация случайного приватного ключа
def generate_private_key():
    return random.randint(1, curve_order-1)

# Генерация публичного ключа на основе приватного ключа
def generate_public_key(private_key):
    return point_multiplication(G, private_key)

# Создание цифровой подписи для сообщения с использованием приватного ключа
def sign(message, private_key):
    k = random.randint(1, curve_order-1)  # Случайное значение k

    # Вычисление точки R
    R = point_multiplication(G, k)
    r = R.x % curve_order

    # Вычисление значения s
    z = int.from_bytes(message, 'big')
    s = (pow(k, -1, curve_order) * (z + private_key * r)) % curve_order
    return r, s

# Проверка цифровой подписи с использованием публичного ключа
def verify(message, signature, public_key):
    r, s = signature
    w = pow(s, -1, curve_order)
    z = int.from_bytes(message, 'big')
    # Вычисление u1 и u2
    u1 = z * w % curve_order
    u2 = r * w % curve_order
    # Вычисление точки P
    P = point_addition(point_multiplication(G, u1), point_multiplication(public_key, u2))
    return r == P.x % curve_order

# Сложение двух точек
def point_addition(P, Q):
    if P is None:
        return Q
    if Q is None:
        return P
    if P.x == Q.x:
        if P.y == Q.y:
            return point_double(P)
        else:
            return None
    s = (Q.y - P.y) * pow(Q.x - P.x, -1, prime_field) % prime_field
    x = (s * s - P.x - Q.x) % prime_field
    y = (s * (P.x - x) - P.y) % prime_field
    return Point(x, y)
# Удвоение точки
def point_double(P):
    s = (3 * P.x * P.x + a) * pow(2 * P.y, -1, prime_field) % prime_field
    x = (s * s - P.x * 2) % prime_field
    y = (s * (P.x - x) - P.y) % prime_field
    return Point(x, y)
# Умножение точки на скаляр
def point_multiplication(P, scalar):
    result = None
    addend = P
    while scalar > 0:
        if scalar & 1:
            result = point_addition(result, addend)
        addend = point_double(addend)
        scalar >>= 1
    return result

curve_order = 23  # Порядок кривой
prime_field = 29  # Поле простого числа p
a = 4
b = 20
G = Point(10, 9)
private_key = generate_private_key()
public_key = generate_public_key(private_key)
message = b"Hello, world!"
signature = sign(message, private_key)
print("Подпись:", signature)
valid = verify(message, signature, public_key)
print("Проверка подписи:", valid)
