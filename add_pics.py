import pickle

pics = {}
try:
    with open("pics.pickle", "rb") as f:
        pics = pickle.load(f)
except FileNotFoundError:
    pics = {}

while(True):
    inp = input("Введите команду(add showall delete quit)\n")
    if inp == "add":
        print("Введите имя файла рецепта")
        filename = input()
        print("Введите ссылку на картинку")
        link = input()
        pics[filename] = link
        with open("pics.pickle", "wb") as f:
            pickle.dump(pics, f)
    elif inp == "showall":
        for i in pics.keys():
            print(i)
    elif inp == "delete":
        print("Введите имя файла рецепта")
        filename = input()
        pics.pop(filename)
        with open("pics.pickle", "wb") as f:
            pickle.dump(pics, f)
    elif inp == "quit":
        break