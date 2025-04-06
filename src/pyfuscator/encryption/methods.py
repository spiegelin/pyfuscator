"""
Encryption methods for code obfuscation.
"""
import random
from typing import List

from pyfuscator.core.utils import random_name

def generate_prime_number() -> int:
    """
    Generate a random prime number.
    
    Returns:
        A random prime number between 1000 and 1000000
    """
    def check_if_it_is_prime(n: int) -> bool:
        """Check if a number is prime."""
        if n < 2:
            return False
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                return False
        return True

    while True:
        num = random.randint(1000, 1000000)
        if check_if_it_is_prime(num):
            return num

def mod_exp(base: int, exp: int, mod: int) -> int:
    """
    Modular exponentiation: (base^exp) % mod.
    
    Args:
        base: Base value
        exp: Exponent
        mod: Modulus
        
    Returns:
        Result of modular exponentiation
    """
    result = 1
    while exp > 0:
        if exp % 2 == 1:
            result = (result * base) % mod
        base = (base * base) % mod
        exp //= 2
    return result

def extended_gcd(a: int, b: int) -> int:
    """
    Extended Euclidean algorithm to find modular inverse.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Modular inverse
    """
    old_r, r = a, b
    old_s, s = 1, 0
    old_t, t = 0, 1
    while r != 0:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_s, s = s, old_s - quotient * s
        old_t, t = t, old_t - quotient * t
    return old_s % b

def encryption_method_1(code_to_encode: str) -> str:
    """
    Encryption method 1: Linear congruential encryption.
    
    Args:
        code_to_encode: Python code to encrypt
        
    Returns:
        Encrypted code with decryption mechanism
    """
    prime_number = generate_prime_number()
    salt = random.randint(1, 300)
    
    # Encrypt
    message_int = [ord(b) for b in code_to_encode]
    ct = [(prime_number * number + salt) % 256 for number in message_int]
    encrypted_message = ''.join([hex(i)[2:].zfill(2) for i in ct])
    decryption_func_name = random_name()

    # Generate random variable names
    crypted_var = random_name()
    salt_var = random_name()
    prime_var = random_name()
    result_var = random_name()
    
    # Generate random internal variable names
    encrypted_list_var = random_name()
    table_var = random_name()
    recovery_var = random_name()
    param_prime = random_name()
    param_crypted = random_name()
    param_salt = random_name()

    # Generate output
    output_content = [
        f"def {decryption_func_name}({param_prime}, {param_crypted}, {param_salt}):",
        f"    {encrypted_list_var} = [int({param_crypted}[i:i+2], 16) for i in range(0, len({param_crypted}), 2)]",
        f"    {table_var} = {{(({param_prime} * char + {param_salt}) % 256): char for char in range(256)}}",
        f"    {recovery_var} = [{table_var}.get(num) for num in {encrypted_list_var}]",
        f"    return bytes({recovery_var})\n",
        f"{crypted_var} = \"{encrypted_message}\"",
        f"{salt_var} = {salt}",
        f"{prime_var} = {prime_number}",
        f"{result_var} = {decryption_func_name}({prime_var}, {crypted_var}, {salt_var}).decode('utf-8')",
        f"exec({result_var})"
    ]
    
    return "\n".join(output_content)

def encryption_method_2(code_to_encode: str) -> str:
    """
    Encryption method 2: XOR with shuffled key.
    
    Args:
        code_to_encode: Python code to encrypt
        
    Returns:
        Encrypted code with decryption mechanism
    """
    salt = random.randint(50, 500)
    key = random.randint(10, 250)
    shuffle_key = list(range(256))
    random.shuffle(shuffle_key)
    reverse_key = {v: k for k, v in enumerate(shuffle_key)}
    
    encoded_bytes = bytearray()
    for char in code_to_encode.encode():
        transformed = (shuffle_key[(char ^ key) % 256] + salt) % 256
        encoded_bytes.append(transformed)
    
    encrypted_message = ''.join([hex(i)[2:].zfill(2) for i in encoded_bytes])
    decryption_func_name = random_name()
    
    # Generate random variable names
    crypted_var = random_name()
    key_var = random_name()
    salt_var = random_name()
    reverse_var = random_name()
    result_var = random_name()
    
    # Generate random internal variable names
    encrypted_bytes_var = random_name()
    decrypted_bytes_var = random_name()
    param_encrypted = random_name()
    param_key = random_name()
    param_salt = random_name()
    param_reverse = random_name()
    iter_var = random_name()
    
    output_content = [
        f"def {decryption_func_name}({param_encrypted}, {param_key}, {param_salt}, {param_reverse}):",
        f"    {encrypted_bytes_var} = [int({param_encrypted}[i:i+2], 16) for i in range(0, len({param_encrypted}), 2)]",
        f"    {decrypted_bytes_var} = bytearray({param_reverse}[({iter_var} - {param_salt}) % 256] ^ {param_key} for {iter_var} in {encrypted_bytes_var})",
        f"    return {decrypted_bytes_var}.decode('utf-8')\n",
        f"{crypted_var} = \"{encrypted_message}\"",
        f"{key_var} = {key}",
        f"{salt_var} = {salt}",
        f"{reverse_var} = {reverse_key}",
        f"{result_var} = {decryption_func_name}({crypted_var}, {key_var}, {salt_var}, {reverse_var})",
        f"exec({result_var})"
    ]
    
    return "\n".join(output_content)

def encryption_method_3(code: str) -> str:
    """
    Encryption method 3: RSA-like encryption.
    
    Args:
        code: Python code to encrypt
        
    Returns:
        Encrypted code with decryption mechanism
    """
    prime1 = generate_prime_number()
    prime2 = generate_prime_number()
    n = prime1 * prime2
    phi = (prime1 - 1) * (prime2 - 1)
    e = 65537
    d = extended_gcd(e, phi)
    
    encrypted_values = [mod_exp(ord(c), e, n) for c in code]
    encrypted_hex = ','.join(str(i) for i in encrypted_values)
    decrypt_func = random_name()
    
    # Generate random variable names
    crypted_var = random_name()
    n_var = random_name()
    d_var = random_name()
    result_var = random_name()
    
    # Generate random internal variable names
    decrypted_var = random_name()
    param_encrypted = random_name()
    param_d = random_name()
    param_n = random_name()
    char_var = random_name()
    
    output_code = [
        f"def {decrypt_func}({param_encrypted}, {param_d}, {param_n}):",
        f"    {decrypted_var} = ''.join(chr(pow(int({char_var}), {param_d}, {param_n})) for {char_var} in {param_encrypted}.split(','))",
        f"    return {decrypted_var}\n",
        f"{crypted_var} = \"{encrypted_hex}\"",
        f"{n_var} = {n}",
        f"{d_var} = {d}",
        f"{result_var} = {decrypt_func}({crypted_var}, {d_var}, {n_var})",
        f"exec({result_var})"
    ]
    
    return "\n".join(output_code)

def encryption_method_4(code: str) -> str:
    """
    Encryption method 4: XOR with key array.
    
    Args:
        code: Python code to encrypt
        
    Returns:
        Encrypted code with decryption mechanism
    """
    key = [random.randint(1, 255) for _ in range(16)]
    encrypted_values = [ord(code[i]) ^ key[i % len(key)] for i in range(len(code))]
    encrypted_hex = ','.join(str(i) for i in encrypted_values)
    key_hex = ','.join(str(k) for k in key)
    decrypt_func = random_name()
    
    # Generate random variable names
    crypted_var = random_name()
    key_var = random_name()
    result_var = random_name()
    
    # Generate random internal variable names
    decrypted_var = random_name()
    param_encrypted = random_name()
    param_key = random_name()
    index_var = random_name()
    
    output_code = [
        f"def {decrypt_func}({param_encrypted}, {param_key}):",
        f"    {decrypted_var} = ''.join(chr({param_encrypted}[{index_var}] ^ {param_key}[{index_var} % len({param_key})]) for {index_var} in range(len({param_encrypted})))",
        f"    return {decrypted_var}\n",
        f"{crypted_var} = [{encrypted_hex}]",
        f"{key_var} = [{key_hex}]",
        f"{result_var} = {decrypt_func}({crypted_var}, {key_var})",
        f"exec({result_var})"
    ]
    
    return "\n".join(output_code) 