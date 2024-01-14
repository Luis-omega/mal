def read(text: str) -> str:
    return text


def eval(text: str) -> str:
    return text


def print_mal(text: str) -> str:
    return text


def rep(text: str) -> str:
    return text


def main():
    while True:
        try:
            text = input("user> ")
        except EOFError:
            break
        result = rep(text)
        print(result)


if __name__ == "__main__":
    main()
