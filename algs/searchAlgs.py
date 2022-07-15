def BinaryArraySearch(A, target):
    lo = 0
    hi = len(A) - 1

    while lo <= hi:
        mid = (lo + hi) // 2

        diff = target - A[mid]
        if diff < 0:
            hi = mid - 1
        elif diff > 0:
            lo = mid + 1
        else:
            return mid
    
    return False # returned if not in array.

def modReturnBinaryArraySearch(A, target):
    lo = 0
    hi = len(A) - 1

    while lo <= hi:
        mid = (lo + hi) // 2

        diff = target - A[mid]
        if diff < 0:
            hi = mid - 1
        elif diff > 0:
            lo = mid + 1
        else:
            return mid
    
    if len(A) % 2 == 0:
        return (lo) # returns where target should be if not in.
    else:
        return -(lo+1) # returns (-) idx position if that is where target would be.
                   # returns (+) idx position if that is where target is. 

A = [3, 14, 15, 19, 26, 53, 58, 65]

print(BinaryArraySearch(A, 17))
# A.insert(-5, 4) # at -4 index, and yeah...
A.insert(3, 17) # at -4 index, and yeah...
print(BinaryArraySearch(A, 17))
for idx, element in enumerate(A):
    print(f"{idx}, {element}")
# print(A)