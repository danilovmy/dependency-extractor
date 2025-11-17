# import functools
# @functools.lru_cache()  #-> transform to O(n)
def fibonacci(target):     # O(2^n)

  if target < 2:
    return target

  return sum((fibonacci(target - 1),
              fibonacci(target - 2)))

def fibonacci_i(target):     #O(n)
  n_2 = n_1 = 1

  for _ in range(2, target):
    n_1, n_2 = n_2 + n_1, n_1

  return n_1


print(fibonacci_i(7))
print(fibonacci_r(7))

print(fibonacci_i(12))
print(fibonacci_r(12))