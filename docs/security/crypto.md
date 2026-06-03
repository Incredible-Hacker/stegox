# Cryptography

StegoX uses a small, audited set of primitives:

| Purpose | Algorithm | Parameters |
|---|---|---|
| Symmetric cipher | AES-256-GCM | 12-byte nonce, 16-byte tag |
| Key derivation | Argon2id (preferred) / scrypt / PBKDF2-HMAC-SHA256 | tunable |
| Compression | zlib (zstd if available) | level 6 |
| Random | `secrets` | OS CSPRNG |

## Frame format

```
+---------+---------+--------+--------+--------+----------+-----------+----------+
| Magic   | Version | Flags  | Salt   | Nonce  | Tag Len  | Tag       | LengthLE |
| 4B      | 1B      | 1B     | 16B    | 12B    | 1B (16)  | 16B       | 8B       |
+---------+---------+--------+--------+--------+----------+-----------+----------+
| Ciphertext + LengthLE bytes                                                       |
+-----------------------------------------------------------------------------------+
```

The version is bumped only on breaking changes to the frame layout.

## Password handling

- Passwords are read from CLI args, environment, or `@password-file`.
- Passwords are never written to logs.
- All secret comparisons use `secrets.compare_digest`.
