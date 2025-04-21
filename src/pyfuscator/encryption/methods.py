"""
Encryption methods for multi-language code obfuscation.
"""
import base64
import random
import zlib
import json
from pyfuscator.core.utils import random_name

# --------------------------
# Common Utility Functions
# --------------------------
def generate_prime_number() -> int:
    def check_if_it_is_prime(n: int) -> bool:
        if n < 2: return False
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0: return False
        return True
    while True:
        num = random.randint(1000, 1000000)
        if check_if_it_is_prime(num): return num

def mod_exp(base: int, exp: int, mod: int) -> int:
    result = 1
    while exp > 0:
        if exp % 2 == 1: result = (result * base) % mod
        base = (base * base) % mod
        exp //= 2
    return result

def extended_gcd(a: int, b: int) -> int:
    old_r, r = a, b
    old_s, s = 1, 0
    old_t, t = 0, 1
    while r != 0:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_s, s = s, old_s - quotient * s
        old_t, t = t, old_t - quotient * t
    return old_s % b

# --------------------------
# Method 1: Linear Congruential
# --------------------------
def encryption_method_1(code_to_encode: str, language: str = "python") -> str:
    prime = generate_prime_number()
    salt = random.randint(1, 300)
    ct = [(prime * ord(c) + salt) % 256 for c in code_to_encode]
    encrypted_hex = ''.join(f"{b:02x}" for b in ct)
    
    var_names = {
        'crypted': random_name(),
        'prime': random_name(),
        'salt': random_name(),
        'result': random_name(),
        'func': random_name(),
        'bytes': random_name(),
        'decrypted': random_name(),
        'm': random_name(),
        'modinv': random_name(),
        'val': random_name()
    }

    if language == "python":
        return (
            f"def {var_names['func']}(p, c, s):\n"
            f"    t = {{(p * ch + s) % 256: ch for ch in range(256)}}\n"
            f"    return bytes([t[b] for b in bytes.fromhex(c)]).decode()\n"
            f"{var_names['crypted']} = '{encrypted_hex}'\n"
            f"{var_names['prime']} = {prime}\n"
            f"{var_names['salt']} = {salt}\n"
            f"exec({var_names['func']}({var_names['prime']}, {var_names['crypted']}, {var_names['salt']}))"
        )
    elif language == "powershell":
        return (
            f"${var_names['crypted']} = '{encrypted_hex}'\n"
            f"${var_names['prime']} = {prime}\n"
            f"${var_names['salt']} = {salt}\n"
            "${3} = 1\n"
            
            "${7} = 256\n"
            "while (${1} -band 1 -eq 0) {{ ${1} = ${1} / 2; ${7} = ${7} / 2 }}\n"
            "for ($_=1; $_ -lt ${7}; $_++) {{\n"
            "    if ((${1} * $_) % $m -eq 1) {{ ${3} = $_; break }}\n"
            "}}\n"
            "${5} = for ($_=0; $_ -lt ${0}.Length; $_+=2) {{\n"
            "    [Convert]::ToByte(${0}.Substring($_,2),16)\n"
            "}}\n"
            "${4} = -join (${5} | %{{\n"
            "    ${6} = ($_ - ${2}) * ${3}\n"
            "    [char]((${6} % ${7} + ${7}) % ${7})\n"  # Double modulo for positive
            "}})\n"
            "iex ${4}"
            .format(var_names['crypted'], var_names['prime'], var_names['salt'], var_names['modinv'], var_names['decrypted'], var_names['bytes'], var_names['val'], var_names['m'])
        )
    elif language == "csharp":
        quote = chr(34)  # Use ASCII character for double quote
        return (
            "using System;\nusing System.Collections.Generic;\n"
            "class Program {{\n"
            f"    static string {var_names['func']}(string encrypted, int prime, int salt) {{\n"
            "        List<byte> bytes = new List<byte>();\n"
            "        for(int i=0; i<encrypted.Length; i+=2)\n"
            "            bytes.Add(Convert.ToByte(encrypted.Substring(i,2), 16));\n"
            "        var table = new Dictionary<int,int>();\n"
            "        for(int ch=0; ch<256; ch++) {{\n"
            "            int key = (prime * ch + salt) % 256;\n"
            "            table[key] = ch;\n"
            "        }}\n"
            "        char[] result = new char[bytes.Count];\n"
            "        for(int i=0; i<bytes.Count; i++)\n"
            "            result[i] = (char)table[bytes[i]];\n"
            "        return new string(result);\n"
            "    }}\n"
            "    static void Main() {{\n"
            f"        string code = {var_names['func']}({quote}{encrypted_hex}{quote}, {prime}, {salt});\n"
            f"        System.Diagnostics.Process.Start({quote}python{quote}, {quote}-c \\\"{{code}}\\\"{quote}).WaitForExit();\n"
            "    }}\n"
            "}}"
        )
    else:
        raise ValueError("Unsupported language")

# --------------------------
# Method 2: XOR with Shuffled Key
# --------------------------
def encryption_method_2(code: str, language: str = "python") -> str:
    key = random.randint(10, 250)
    salt = random.randint(50, 500)
    shuffle = list(range(256))
    random.shuffle(shuffle)
    reverse = {v:k for k,v in enumerate(shuffle)}
    
    encrypted = [(shuffle[(ord(c) ^ key) % 256] + salt) % 256 for c in code]
    encrypted_hex = ''.join(f"{b:02x}" for b in encrypted)
    
    var_names = {
        'encrypted': random_name(),
        'key': random_name(),
        'salt': random_name(),
        'reverse': random_name(),
        'func': random_name(),
        'bytes': random_name(),
        'decrypted': random_name()
    }

    if language == "python":
        return (
            f"def {var_names['func']}(e, k, s, r):\n"
            "    b = bytes.fromhex(e)\n"
            "    return bytes([r[(x - s) % 256] ^ k for x in b]).decode()\n"
            f"{var_names['encrypted']} = '{encrypted_hex}'\n"
            f"{var_names['key']} = {key}\n"
            f"{var_names['salt']} = {salt}\n"
            f"{var_names['reverse']} = {reverse}\n"
            f"exec({var_names['func']}({var_names['encrypted']}, {var_names['key']}, {var_names['salt']}, {var_names['reverse']}))"
        )
    elif language == "powershell":
        # Create a PowerShell array for reverse mapping instead of hashtable
        reverse_array = [0]*256
        for k, v in reverse.items():
            reverse_array[k] = v
            
        return (
            f"${var_names['encrypted']} = '{encrypted_hex}'\n"
            f"${var_names['key']} = {key}\n"
            f"${var_names['salt']} = {salt}\n"
            f"${var_names['reverse']} = @({','.join(map(str, reverse_array))})\n"
            "${4} = for( $i    =0;$i    -lt  ${0}.Length  ; $i  += 2){{[   Convert]::ToByte(   ${0}.Substring($i  ,2)  , 16)}}\n"
            "${5} = -join (${4}    |     %{{\n     [  char    ](${3}[([int]($_    - ${2}) % 256)]     -bxor ${1}) }})\n"
            "&('I'+'e'+'x') ${5}"
            .format(var_names['encrypted'], var_names['key'], var_names['salt'], var_names['reverse'], var_names['bytes'], var_names['decrypted'])
        )
    elif language == "csharp":
        rev_dict = "new Dictionary<int,int>{" + ','.join(f"{{{k},{v}}}" for k,v in reverse.items()) + "}"
        return (
            "using System;\nusing System.Collections.Generic;\n"
            "class Program {{\n"
            "    static string Decrypt(string e, int k, int s, Dictionary<int,int> r) {{\n"
            "        List<byte> bytes = new List<byte>();\n"
            "        for(int i=0;i<e.Length;i+=2)\n"
            "            bytes.Add(Convert.ToByte(e.Substring(i,2),16));\n"
            "        char[] res = new char[bytes.Count];\n"
            "        for(int i=0;i<bytes.Count;i++) {{\n"
            "            int val = (bytes[i] - s) %% 256;\n"
            "            res[i] = (char)(r[val] ^ k);\n"
            "        }}\n"
            "        return new string(res);\n"
            "    }}\n"
            "    static void Main() {{\n"
            f"        var reverse = {rev_dict};\n"
            f"        string code = Decrypt(\"{encrypted_hex}\", {key}, {salt}, reverse);\n"
            "        System.Diagnostics.Process.Start(\"python\", $\"-c \\\"{{code}}\\\"\").WaitForExit();\n"
            "    }}\n"
            "}}"
        )
    else:
        raise ValueError("Unsupported language")

# --------------------------
# Method 3: RSA-like Encryption
# --------------------------
def encryption_method_3(code: str, language: str = "python") -> str:
    p = generate_prime_number()
    q = generate_prime_number()
    n = p * q
    phi = (p-1)*(q-1)
    e = 65537
    d = extended_gcd(e, phi)
    encrypted = [mod_exp(ord(c), e, n) for c in code]
    
    var_names = {
        'encrypted': random_name(),
        'd': random_name(),
        'n': random_name(),
        'func': random_name(),
        'decrypted': random_name()
    }

    if language == "python":
        return (
            f"def {var_names['func']}(e, d, n):\n"
            "    return ''.join(chr(pow(int(c),d,n)) for c in e.split(','))\n"
            f"{var_names['encrypted']} = '{','.join(map(str, encrypted))}'\n"
            f"{var_names['d']} = {d}\n"
            f"{var_names['n']} = {n}\n"
            f"exec({var_names['func']}({var_names['encrypted']}, {var_names['d']}, {var_names['n']}))"
        )
    elif language == "powershell":
        return (
            f"${var_names['encrypted']} = @(  '" + "','".join(f"{x}" for x in encrypted) + "')\n"
            f"${var_names['d']} = {d}\n"
            f"${var_names['n']} = {n}\n"
            "$" + var_names['decrypted'] + " = -join (  ${" + var_names['encrypted'] + "}  |   ForEach-Object { "
            "[char ]::ConvertFromUtf32([int ]([  bigint]::ModPow($_   ,  ${" + var_names['d'] + "},    ${" + var_names['n'] + "}))) "
            "})\n"
            f"iex                                                                                                 ${var_names['decrypted']}"
        )
    elif language == "csharp":
        # Fix: Use chr(34) for quotes in array elements
        quote = chr(34)
        encrypted_joined = f'{quote},{quote}'.join(map(str, encrypted))
        return (
            "using System;\nusing System.Numerics;\n"
            "class Program {{\n"
            "    static string Decrypt(string[] e, BigInteger d, BigInteger n) {{\n"
            "        char[] res = new char[e.Length];\n"
            "        for(int i=0;i<e.Length;i++)\n"
            "            res[i] = (char)BigInteger.ModPow(BigInteger.Parse(e[i]), d, n);\n"
            "        return new string(res);\n"
            "    }}\n"
            "    static void Main() {{\n"
            f"        string code = Decrypt(new[]{{ {quote}{encrypted_joined}{quote} }},\n"
            f"            new BigInteger({d}), new BigInteger({n}));\n"
            "        System.Diagnostics.Process.Start(\"python\", $\"-c \\\"{{code}}\\\"\").WaitForExit();\n"
            "    }}\n"
            "}}"
        )
    else:
        raise ValueError("Unsupported language")
    
# --------------------------
# Method 4: XOR with Key Array
# --------------------------
def encryption_method_4(code: str, language: str = "python") -> str:
    key = [random.randint(1,255) for _ in range(16)]
    encrypted = [ord(c) ^ key[i%len(key)] for i,c in enumerate(code)]
    
    var_names = {
        'encrypted': random_name(),
        'key': random_name(),
        'func': random_name(),
        'decrypted': random_name()
    }

    if language == "python":
        return (
            f"def {var_names['func']}(e, k):\n"
            "    return ''.join(chr(c ^ k[i%len(k)]) for i,c in enumerate(e))\n"
            f"{var_names['encrypted']} = {encrypted}\n"
            f"{var_names['key']} = {key}\n"
            f"exec({var_names['func']}({var_names['encrypted']}, {var_names['key']}))"
        )
    elif language == "powershell":
        return (
            f"${var_names['encrypted']} = @(               {','.join(map(str, encrypted))})\n"
            f"${var_names['key']} = @(  {','.join(map(str, key))})\n"
            "${2} = -join (0..  (${0}.Count- 1) | %{{ \n    [   char   ](${0}[$_ ] -bxor ${1}[$_   % ${1}.Count]) \n}})\n"
            "iex     ${2}"
            .format(var_names['encrypted'], var_names['key'], var_names['decrypted'])
        )
    elif language == "csharp":
        return (
            "using System;\nusing System.Linq;\n"
            "class Program {{\n"
            "    static string Decrypt(int[] e, int[] k) {{\n"
            "        char[] res = new char[e.Length];\n"
            "        for(int i=0;i<e.Length;i++)\n"
            "            res[i] = (char)(e[i] ^ k[i %% k.Length]);\n"
            "        return new string(res);\n"
            "    }}\n"
            "    static void Main() {{\n"
            f"        int[] encrypted = new[] {{ {','.join(map(str, encrypted))} }};\n"
            f"        int[] key = new[] {{ {','.join(map(str, key))} }};\n"
            "        string code = Decrypt(encrypted, key);\n"
            "        System.Diagnostics.Process.Start(\"python\", $\"-c \\\"{{code}}\\\"\").WaitForExit();\n"
            "    }}\n"
            "}}"
        )
    else:
        raise ValueError("Unsupported language")

# --------------------------
# Method 5: Multi-layer Compression
# --------------------------
def encryption_method_5(code: str, language: str = "python") -> str:
    # Layer 3: Base85 + Zlib
    compressed = zlib.compress(code.encode())
    b85 = base64.b85encode(compressed).decode()
    
    # Layer 2: Reverse + XOR
    xor_key = random.randint(1,255)
    reversed_xor = ''.join(chr(ord(c) ^ xor_key) for c in b85[::-1])
    
    # Layer 1: Base64
    final_payload = base64.b64encode(reversed_xor.encode()).decode()

    var_names = {
        'payload': random_name(),
        'xor_key': random_name(),
        'b64': random_name(),
        'b85': random_name(),
        'compressed': random_name(),
    }

    if language == "python":
        return (
            f"import base64,zlib\n"
            f"{var_names['payload']} = '{final_payload}'\n"
            f"{var_names['b64']} = base64.b64decode({var_names['payload']}).decode()\n"
            f"{var_names['xor_key']} = {xor_key}\n"
            f"{var_names['b85']} = ''.join(chr(ord(c) ^ {var_names['xor_key']}) for c in {var_names['b64']}[::-1])\n"
            "exec(zlib.decompress(base64.b85decode({0})).decode())"
            .format(var_names['b85'])
        )
    elif language == "powershell":
        return (
            f"${var_names['payload']} = '{final_payload}'\n"
            "# Base64 decode layer 1\n"
            f"${var_names['b64']} = [Text.Encoding]::Latin1.GetString([Convert]::FromBase64String(${var_names['payload']}))\n"
            f"${var_names['xor_key']} = {xor_key}\n"
            "# XOR decrypt and reverse\n"
            f"${var_names['compressed']} = -join (${{{var_names['b64']}}}[{len(b85)-1}..0] | ForEach-Object {{\n"
            f"    $val = ([byte][char]$_) -bxor ${{{var_names['xor_key']}}}\n"  # Fixed line
            "    [char](($val % 256 + 256) % 256)\n"
            "}})\n"
            "# Decompress and execute\n"
            "$bytes = [Convert]::FromBase64String(${" + var_names['compressed'] + "})\n"
            "$ms = New-Object System.IO.MemoryStream(,$bytes)\n"
            "$gs = New-Object System.IO.Compression.GZipStream $ms, ([System.IO.Compression.CompressionMode]::Decompress)\n"
            "$sr = New-Object System.IO.StreamReader($gs)\n"
            "$decrypted = $sr.ReadToEnd()\n"
            "if (-not [string]::IsNullOrEmpty($decrypted)) {{\n"
            "    iex $decrypted\n"
            "}} else {{\n"
            "    Write-Error 'Decryption failed: Empty result'\n"
            "}}"
        )
    elif language == "csharp":
        return (
            "using System;\nusing System.IO;\nusing System.IO.Compression;\n"
            "using System.Text;\n"
            "class Program {\n"
            "    static string Decrypt(string payload, int key) {\n"
            "        // Base64 decode\n"
            "        string b64 = Encoding.UTF8.GetString(Convert.FromBase64String(payload));\n"
            "        // Reverse and XOR\n"
            "        char[] reversed = b64.ToCharArray();\n"
            "        Array.Reverse(reversed);\n"
            "        for(int i=0;i<reversed.Length;i++) reversed[i] = (char)(reversed[i] ^ key);\n"
            "        // Base85 decode and decompress\n"
            "        byte[] compressed = Convert.FromBase64String(new string(reversed).Replace(\" \", \"\"));\n"
            "        using var ms = new MemoryStream(compressed);\n"
            "        using var gs = new GZipStream(ms, CompressionMode.Decompress);\n"
            "        using var sr = new StreamReader(gs);\n"
            "        return sr.ReadToEnd();\n"
            "    }\n"
            "    static void Main() {\n"
            f"        string code = Decrypt(\"{final_payload}\", {xor_key});\n"
            "        System.Diagnostics.Process.Start(\"python\", $\"-c \\\"{code}\\\"\").WaitForExit();\n"
            "    }\n"
            "}"
        )
    else:
        raise ValueError("Unsupported language")