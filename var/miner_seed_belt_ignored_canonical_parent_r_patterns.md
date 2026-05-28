# Miner Seed Patterns — Belt-Ignored Canonical Set

Equivalence rule:

- Ignore SpaceBelt position/path as topology.
- Ignore miner `R` for equivalence; rotate/reflection-normalize the seed.
- Keep extension parent relation and extension `R` because each extension faces its parent.
- Remove D4 symmetry: 4 rotations + mirror/reflection.

## Counts

| Composition | Count |
|---|---:|
| M | 1 |
| M + 1E | 1 |
| M + 2E | 4 |
| M + 3E | 13 |

**Total: 19**

## m0e_01 — M + 0E

```text
M B
```

Entries:

```json
[
  {
    "X": 1,
    "T": "SpaceBelt_Forward"
  },
  {
    "T": "Layout_ShapeMiner"
  }
]
```

Copy string:

```text
SHAPEZ2-4-H4sIAAAAAAAC/yWOUQfDMBSF/8uxx7zUHkYeaxtlo9apMVVXm1nIkkpSE5H/vmR1OVzHOeeL6MGran9gqFvwiJ0PiwBH4xTpGQzNZHQxjuQJ/AmZf94q8i9jPw5Mr0ptAvemRfDbuh2GxHDS3krhcjDikZcY7rm8W2gStVB+PBv7JTsjsfh3LhTM6seuNF2lFhZpyGhSkw29sE4WmMKb0g+ZKV4HuwAAAA==
```

## m1e_01 — M + 1E

```text
E M B
```

Entries:

```json
[
  {
    "X": 1,
    "T": "SpaceBelt_Forward"
  },
  {
    "T": "Layout_ShapeMiner"
  },
  {
    "X": -1,
    "T": "Layout_ShapeMinerExtension"
  }
]
```

Copy string:

```text
SHAPEZ2-4-H4sIAAAAAAAC/2VPQQrCMBD8y+AxHooHIcdihYJCsVIEKWVpIwZiWpIULSF/N229ycLC7uzM7HhU4Emy2zOkBbjHxk2DAEduFekODHnb6xk4kCPwO2SceaHIPXrzsmB6VGptsE8aBL+Ma6EODJl2RgobiR636MRwjeLlQK1IhXLNsTdvMh0C8wtyoqkfXVPOSmephVmQyNz+qH8H2ccJbWV8MtQxhNRkpkqYZbMkC+ELqki6z+UAAAA=
```

## m2e_01 — M + 2E

```text
E E M B
```

Entries:

```json
[
  {
    "X": 1,
    "T": "SpaceBelt_Forward"
  },
  {
    "T": "Layout_ShapeMiner"
  },
  {
    "X": -1,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "X": -2,
    "T": "Layout_ShapeMinerExtension"
  }
]
```

Copy string:

```text
SHAPEZ2-4-H4sIAAAAAAAC/4VQzQqCQBB+l4+O28E6BHuUDIQCyZAgRIbcaGFbZXelRPbdW7VOHWJgYOb7mZ8BBXgUrTcMcQY+YOH6VoAjtYp0DYb02ugR2JIj8AtkqHmmyN0a87BgulNqTrB3agU/dnOg9AyJdkYKG4QDzmESwymY5y1dRSyUq3aNeZKp4dkwIXvqm85V+eh0kFqYCQnK5Uf6Q0heTmgrw5Jf5uo/swznSk2mL4SZOtMPvH8DBqI2SA8BAAA=
```

## m2e_02 — M + 2E

```text
E M B
E . .
```

Entries:

```json
[
  {
    "X": 1,
    "T": "SpaceBelt_Forward"
  },
  {
    "T": "Layout_ShapeMiner"
  },
  {
    "X": -1,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "X": -1,
    "Y": -1,
    "R": 1,
    "T": "Layout_ShapeMinerExtension"
  }
]
```

Copy string:

```text
SHAPEZ2-4-H4sIAAAAAAAC/31QTQuCQBD9L4+O20E6BHuUDIQC0ZAiRAbbaGFbZXelRPzvrRoRBDEww8yb9+ajRw4eBKs1Q5iA91i4rhHgiK0ifQFDXNV6BDbkCPwM6XOeKHLX2twtmG6Vmh3sjRrB03Y2FANDpJ2Rwnpij6OfxHDw4llDlQiFcuW2Ng8yFwysn5AddXXrymxU2kstzIR45vJN/WmInk5oK/2SX52nOaSfif9ohb9dajJdLsxUmR4yDC89o1Q/HAEAAA==
```

## m2e_03 — M + 2E

```text
E M B
. E .
```

Entries:

```json
[
  {
    "X": 1,
    "T": "SpaceBelt_Forward"
  },
  {
    "T": "Layout_ShapeMiner"
  },
  {
    "X": -1,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "Y": -1,
    "R": 1,
    "T": "Layout_ShapeMinerExtension"
  }
]
```

Copy string:

```text
SHAPEZ2-4-H4sIAAAAAAAC/31QzQqCQBB+l4+O20E6BHuUDIQC0ZAiRAbdaGFbZXelRHz3Vo0uQQwMzHw/8zMgBw+CzZYhTMAHrFzfCnDEVpGuwRBXjZ6AHTkCv0L6mieK3K0xDwumO6WWBHunVvC0WwLFyBBpZ6SwXjjg7CcxnLx51lIlQqFcuW/Mk0yNkQ0zcqC+6VyZTU5HqYWZEa9cf6Q/hOjlhLbSLzkxLwsz/Y76xy/80VKT6XNh5s78iXF8AwdwCj8VAQAA
```

## m2e_04 — M + 2E

```text
E .
M B
E .
```

Entries:

```json
[
  {
    "X": 1,
    "T": "SpaceBelt_Forward"
  },
  {
    "T": "Layout_ShapeMiner"
  },
  {
    "Y": -1,
    "R": 1,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "Y": 1,
    "R": 3,
    "T": "Layout_ShapeMinerExtension"
  }
]
```

Copy string:

```text
SHAPEZ2-4-H4sIAAAAAAAC/4VQzQqCQBB+l4+O20E8BHuUDIIC0ZAiRAbdaGFbZXelRHz3Vo0uHWJgYOb7mZ8BOXgQhBuGKAEfsHJ9K8Cxt4p0DYZ91egJ2JIj8Cukr3miyN0a87BgulNqSbB3agVPuyVQjAyxdkYK64UDzn4Sw8mbZy1VIhLKlbvGPMnUGNkwIwfqm86V2eR0lFqYGbmAr700/Rr80OKXE9pKv+qHv9DD//TCXy41mT4XZu7M7xjHN1C0/dAaAQAA
```

## m3e_01 — M + 3E

```text
E E E M B
```

Entries:

```json
[
  {
    "X": 1,
    "T": "SpaceBelt_Forward"
  },
  {
    "T": "Layout_ShapeMiner"
  },
  {
    "X": -1,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "X": -2,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "X": -3,
    "T": "Layout_ShapeMinerExtension"
  }
]
```

Copy string:

```text
SHAPEZ2-4-H4sIAAAAAAAC/41QTQuCQBD9L4+O28E6BHuUDIQCyZAgRAbdaGFbZXelRPzvrVqnDsXAwMz7mOH1yMCDYL1hCBPwHgvXNQIcsVWkKzDEZa1HYEuOwC+QfuaJInetzd2C6VapucHeqBH82M6FfGCItDNSWC/scfaXGE7ePG2oFKFQrtjV5kGmwsD6CdlTV7euSEeng9TCTIhXLt/SL0L0dEJb6Z/8MFd/M9e/mbkPRmoyXSbMtJnSGoYXsXok8zkBAAA=
```

## m3e_02 — M + 3E

```text
E E M B
E . . .
```

Entries:

```json
[
  {
    "X": 1,
    "T": "SpaceBelt_Forward"
  },
  {
    "T": "Layout_ShapeMiner"
  },
  {
    "X": -1,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "X": -2,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "X": -2,
    "Y": -1,
    "R": 1,
    "T": "Layout_ShapeMinerExtension"
  }
]
```

Copy string:

```text
SHAPEZ2-4-H4sIAAAAAAAC/5VQTQvCMAz9Lw+P9aAehB5FBUFhbDIUEQlasVDb0XboGP3v1k69CIIEAsn7yCMtSvDBYDRmmGTgLXq+qQQ4Fk6RPoFhcTT6CUzJE/gOMs48U+TPxl4dmK6V6hrchSrB87or7APDTHsrhYvCFpt4iWEdzYuKjmIilD/Mjb2RPSGwNiFLakztD8XTaSW1sAmJyv5L+kWY3b3QTsaQb+bwH+a2s84/2X7J9vFLUpNtSmHTJr0uhAfigm+4RgEAAA==
```

## m3e_03 — M + 3E

```text
. E M B
E E . .
```

Entries:

```json
[
  {
    "X": 1,
    "T": "SpaceBelt_Forward"
  },
  {
    "T": "Layout_ShapeMiner"
  },
  {
    "X": -1,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "X": -1,
    "Y": -1,
    "R": 1,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "X": -2,
    "Y": -1,
    "T": "Layout_ShapeMinerExtension"
  }
]
```

Copy string:

```text
SHAPEZ2-4-H4sIAAAAAAAC/42QwQrCMAyG3+XHYz2oB6FHUWGgMDYZioiEWbFQu9F26Ch9d+smInhQAgnJny8J8SjAR6PJlGGWgnsMXFsLcCRWkT6BISkr/RTm5Ah8Dxlznipy58pcLZhulOod7IVqwbOmNxwCw0I7I4WNoMc2bmLYxOF5TaWYCeWOy8rcyJwQmO+UFbVV4475c9JaamE6JZLDF/rVsLg7oa2MR3507vqQvTf+gY3f2C/gEJ8lNZm2EKardB8M4QHLYxEZTQEAAA==
```

## m3e_04 — M + 3E

```text
. . M B
E E E .
```

Entries:

```json
[
  {
    "X": 1,
    "T": "SpaceBelt_Forward"
  },
  {
    "T": "Layout_ShapeMiner"
  },
  {
    "Y": -1,
    "R": 1,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "X": -1,
    "Y": -1,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "X": -2,
    "Y": -1,
    "T": "Layout_ShapeMinerExtension"
  }
]
```

Copy string:

```text
SHAPEZ2-4-H4sIAAAAAAAC/42QwQrCMBBE/2XwGA/Vg5BjsYKgUFRKRYosGjEQk5KkaCn9d9NUvHiRQCA782bDdCjAk2S+YEhz8A4T39YCHGunSF/BsL4YPQhL8gR+ggxvnivyN2MfDkw3So0X3J1qwXfNeFD1DJn2VgoXwA5l2MRwCOH7mi4iFcqfV8Y+yV7Rsy4qG2pN48/7IWkrtbBROYJPA7r7BvzYspcX2snw1cFfjv4P9icw+xuoQllSk20LYeMkNtj3bxtmk3ZNAQAA
```

## m3e_05 — M + 3E

```text
E E M B
. E . .
```

Entries:

```json
[
  {
    "X": 1,
    "T": "SpaceBelt_Forward"
  },
  {
    "T": "Layout_ShapeMiner"
  },
  {
    "X": -1,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "X": -2,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "X": -1,
    "Y": -1,
    "R": 1,
    "T": "Layout_ShapeMinerExtension"
  }
]
```

Copy string:

```text
SHAPEZ2-4-H4sIAAAAAAAC/41QzQrCMAx+lw+P9aAehB5FBUFhbDIUEQlasVDb0XboGH13a6deBJFAQvL9JKRFCT4YjMYMkwy8Rc83lQDHwinSJzAsjkY/gSl5At9Bxp5nivzZ2KsD07VSXYK7UCV4XneBfWCYaW+lcFHYYhM3MayjeVHRUUyE8oe5sTeyJwTWJmRJjan9oXg6raQWNiFR2X9JvwizuxfayXjkmzn8mxk9t13JP7f9ku3jl6Qm25TCpkl6XQgPH3ADkUYBAAA=
```

## m3e_06 — M + 3E

```text
E E M B
. . E .
```

Entries:

```json
[
  {
    "X": 1,
    "T": "SpaceBelt_Forward"
  },
  {
    "T": "Layout_ShapeMiner"
  },
  {
    "X": -1,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "Y": -1,
    "R": 1,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "X": -2,
    "T": "Layout_ShapeMinerExtension"
  }
]
```

Copy string:

```text
SHAPEZ2-4-H4sIAAAAAAAC/4WQwQrCMBBE/2XwGA/qQcixqFBQKCpFkVKWNmIgJiVJ0VL676atePFQAgvZeTO7bIsUfLFYrRmiBLzFzDeVAEfsFOkSDHFhdC9syBP4DTL8eaLI3419OjBdKzUWuAdVgh/r8SHrGLbaWylcMLa4hEkM5xB+qqgQkVA+3xn7IluiY+2g7Kkxtc9PfdJBamEHJTjnX+sfsH17oZ0MS/bkdSSPv1ETfJ+8nCazcB6pyTapsENnuFnXfQCIcTSkPwEAAA==
```

## m3e_07 — M + 3E

```text
E .
M B
E .
E .
```

Entries:

```json
[
  {
    "X": 1,
    "T": "SpaceBelt_Forward"
  },
  {
    "T": "Layout_ShapeMiner"
  },
  {
    "Y": -1,
    "R": 1,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "Y": 1,
    "R": 3,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "Y": -2,
    "R": 1,
    "T": "Layout_ShapeMinerExtension"
  }
]
```

Copy string:

```text
SHAPEZ2-4-H4sIAAAAAAAC/41QTQuCQBD9L4+O28E8BHuUDISC0JAiQgbdaGFbZXelRPzvbRpdusjAwMz7mOH1yMGDIFwzRAfwHgvXNQIciVWkKzAkZa0/wIYcgV8g/cwPitytNg8LplulpgZ7p0bwtJ0K14Eh1s5IYb2wx8lfYjh686yhUkRCuWJbmyeZCgPrR2RHXd26Ivs47aUWZkTO4EsvTX8Gf7T45YS20r/65U/0cC59uZprf/VJSU2my4UZN2N8w/AGsXqC6EoBAAA=
```

## m3e_08 — M + 3E

```text
E . .
E M B
E . .
```

Entries:

```json
[
  {
    "X": 1,
    "T": "SpaceBelt_Forward"
  },
  {
    "T": "Layout_ShapeMiner"
  },
  {
    "X": -1,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "X": -1,
    "Y": -1,
    "R": 1,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "X": -1,
    "Y": 1,
    "R": 3,
    "T": "Layout_ShapeMinerExtension"
  }
]
```

Copy string:

```text
SHAPEZ2-4-H4sIAAAAAAAC/42QwQrCMAyG3+XHYz2IB6HH4QRBYWwyFBEJWrFQu9F26Ch7d7tORPCgBBKSP18S4lGCTybTGUOSgXuMXFsLcCytIn0Gw/JU6V6YkyPwPWTIeabIXSpzs2C6UWpwsFeqBc+bwXDoGFLtjBQ2gB7bsIlhE4YXNZ1EIpQ7LipzJ3NGx3xUVtRWjTsW/aS11MJEJZDjF/rVkD6c0FaGIz86d0PI3xv/xgZq+ps6hI9JTaYthYmV+MauewIXvMn4UgEAAA==
```

## m3e_09 — M + 3E

```text
E M B
E E .
```

Entries:

```json
[
  {
    "X": 1,
    "T": "SpaceBelt_Forward"
  },
  {
    "T": "Layout_ShapeMiner"
  },
  {
    "X": -1,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "Y": -1,
    "R": 2,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "X": -1,
    "Y": -1,
    "R": 1,
    "T": "Layout_ShapeMinerExtension"
  }
]
```

Copy string:

```text
SHAPEZ2-4-H4sIAAAAAAAC/41QzQrCMAx+lw+P9TA9CD0OJwgKY5OhyJCgFQu1G22HjtF3t/sBD14kEEi+v5AOBXgULVcMcQreYebaWoBjaxXpGxi210r3wJocgZ8hw8xTRe5emacF041SY4N9UC141oyF0jMk2hkpbBB2OIYkhkMwz2u6ilgod9lU5kXmBs+6AdlRWzXukvdOe6mFGZCgnE/SH0LydkJbGY7smaeRmYEv/uJPzl/ZHzFl+JXUZNpCmGEzPND7DwBEQblMAQAA
```

## m3e_10 — M + 3E

```text
E M B
E E .
```

Entries:

```json
[
  {
    "X": 1,
    "T": "SpaceBelt_Forward"
  },
  {
    "T": "Layout_ShapeMiner"
  },
  {
    "X": -1,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "Y": -1,
    "R": 1,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "X": -1,
    "Y": -1,
    "R": 1,
    "T": "Layout_ShapeMinerExtension"
  }
]
```

Copy string:

```text
SHAPEZ2-4-H4sIAAAAAAAC/5VQzQrCMAx+lw+P9TA8CD0OJwgKY5OhiEjQioXajbZDR+m7223ixYNIIJB8fyEeFXiSzOYMaQ7uMXFdI8Cxsor0BQyrc617YEGOwA+Qcea5Inetzd2C6VapscHeqBG8aMfCMTBk2hkpbBR67GISwzaalw2dRSqUOy1r8yBzQWB+QNbU1a07lb3TRmphBiQqp2/pFyF7OqGtjEf2zP3ILD5RP/hv579kx/grqcl0lTDDZnhgCC+4OUg7TAEAAA==
```

## m3e_11 — M + 3E

```text
. E .
E M B
E . .
```

Entries:

```json
[
  {
    "X": 1,
    "T": "SpaceBelt_Forward"
  },
  {
    "T": "Layout_ShapeMiner"
  },
  {
    "X": -1,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "Y": 1,
    "R": 3,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "X": -1,
    "Y": -1,
    "R": 1,
    "T": "Layout_ShapeMinerExtension"
  }
]
```

Copy string:

```text
SHAPEZ2-4-H4sIAAAAAAAC/41QzQrCMAx+lw+P9TB2EHocThgoyJThkCFBKxZqN9oOHWPvbteJF0EkkJB8PwnpUYBHUbxgSLbgPWauawQ4MqtIX8CQnWs9AktyBH6E9D3fKnLX2twtmG6VmhLsjRrB83YKVANDqp2Rwnphj4PfxLD35ruGziIRyp1WtXmQuWBgfUDW1NWtO+1Gp43UwgTEK+dv6RchfTqhrfRHjswy7MjB47/ob+NyKvnnwF+yyr9KajJdIUyYhP8NwwsGKxHSSwEAAA==
```

## m3e_12 — M + 3E

```text
. E .
. M B
E E .
```

Entries:

```json
[
  {
    "X": 1,
    "T": "SpaceBelt_Forward"
  },
  {
    "T": "Layout_ShapeMiner"
  },
  {
    "Y": -1,
    "R": 1,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "Y": 1,
    "R": 3,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "X": -1,
    "Y": -1,
    "T": "Layout_ShapeMinerExtension"
  }
]
```

Copy string:

```text
SHAPEZ2-4-H4sIAAAAAAAC/41QzQrCMAx+lw+P9TB2EHocThgoiBNRRCRsFQu1HW2HjrF3t3bixYMSCCTfX0iPHXiSpDOGbA3eY+K7RoCjcIp0DYaiMvoFzMkT+BEyzHytyF+MvTkw3So1NrgrNYJv2rFwGhhy7a0ULgh77EMSwzaYlw1VIhPKnxfG3snWGFgfkSV1pvXn8uW0klrYiBzAp0G6+Rh80fKHF9rJcOqbP9LTv+j70f6d8ktwCq+Smmy3EzZu4v+G4QkAbu/tSwEAAA==
```

## m3e_13 — M + 3E

```text
. E .
E M B
. E .
```

Entries:

```json
[
  {
    "X": 1,
    "T": "SpaceBelt_Forward"
  },
  {
    "T": "Layout_ShapeMiner"
  },
  {
    "X": -1,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "Y": -1,
    "R": 1,
    "T": "Layout_ShapeMinerExtension"
  },
  {
    "Y": 1,
    "R": 3,
    "T": "Layout_ShapeMinerExtension"
  }
]
```

Copy string:

```text
SHAPEZ2-4-H4sIAAAAAAAC/4WQQQvCMAyF/8vDYz2MHYQehxMEBXEyFBkjaMVC7UbboWP0v9ut4sWDBALJ+14SMqAET5J0wZDtwAfMXN8KcKytIn0Fw/rS6FFYkiPwM2So+U6RuzXmYcF0p1RMsHdqBd93MVB5hlw7I4UNxgHHsInhEIYXLV1EJpSrV415krnCs2FSNtQ3nauLcdJWamEmJTjnH+sPkL+c0FaGI0fyFMn9d9V/PuLpf7wKP5KaTF8KM3Wmx3n/BsHYT+hEAQAA
```
