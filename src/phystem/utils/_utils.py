def number_to_string(x, decimal_char="-", ndigits=2):
    x = str(round(x, ndigits=ndigits))
    x = x.replace(".", decimal_char)
    return x

if __name__ == "__main__":
    print(number_to_string(2**.5, ndigits=4, decimal_char="_"))
