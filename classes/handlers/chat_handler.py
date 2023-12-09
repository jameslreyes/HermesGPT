import random

class ChatHandler():
    def __init__(self):
        pass

    async def unstable_text_transform(text):
        result = []
        for char in text:
            if char.isalpha():
                repeat_count = random.choice([1, 1, 2, 3, 3])
                random_case = random.choices([True, False], weights=[0.8, 0.2], k=1)[0]
                if random_case:
                    char = char.upper()
                else:
                    char = char.lower()
                result.append(char * repeat_count)
            else:
                result.append(char)
        return "".join(result)