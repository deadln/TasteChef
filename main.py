#TODO: автоматический парсер, БД

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api import VkUpload
import pickle
import os
import random
import requests


instruction = "Команды для работы с ботом:\n"
instruction += "Рецепт - вывести случайный рецепт\n"
instruction += "Помощь - вывести эту инструкцию снова\n"

userlist = {}#Словарь пользователей и рецептов, которые они уже просматривали
recipes = []#Список названий файлов рецептов
user_recipe_flag = {}#Рецепт, который был последним выведен пользователю
user_stats = {}#Статистика использований по пользователям

def update_recipes():#Обновление списка рецептов
    os.chdir(os.getcwd() + r'/recipes')#Переход в папку с рецептами
    files = os.listdir()
    recipes.clear()
    for file in files:
        recipes.append(file)
    os.chdir(os.getcwd()[:len(os.getcwd()) - 8])
    print(recipes)

def main():



    #Инициализация бота
    tk = ""
    with open("token.txt", "r") as f:
        tk = f.read()
    vk_session = vk_api.VkApi(token = tk)
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    upload = VkUpload(vk_session)
    session = requests.Session()

    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button("Да", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("Нет", color=VkKeyboardColor.NEGATIVE)

    try:
        with open("users.pickle", "rb") as f:
            userlist = pickle.load(f)
    except FileNotFoundError:
        userlist = {}

    try:
        with open("stats.pickle", "rb") as f:
            user_stats = pickle.load(f)
    except FileNotFoundError:
        user_stats = {}

    update_recipes()

    while(True):
        try:
            for event in longpoll.listen():
                # Первое использование бота
                if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.user_id not in userlist:
                    vk.messages.send(
                        user_id=event.user_id,
                        random_id=get_random_id(),
                        message=instruction
                    )
                    userlist[event.user_id] = []#Добавление нового пользователя
                    with open("users.pickle", "wb") as f:
                        pickle.dump(userlist, f)

                elif event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text.lower() == "помощь":
                    vk.messages.send(user_id = event.user_id,
                                     random_id = get_random_id(),
                                     message = instruction
                                     )

                elif event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text.lower() == "update":
                    update_recipes()
                    vk.messages.send(user_id = event.user_id,
                                     random_id = get_random_id(),
                                     message = "Рецепты обновлены"
                                     )

                elif event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text.lower() == "рецепт":
                    vk.messages.send(user_id=event.user_id,
                                     random_id=get_random_id(),
                                     message="Подождите, идет загрузка рецепта"
                                     )

                    if event.user_id in user_stats:
                        user_stats[event.user_id] += 1
                    else:
                        user_stats[event.user_id] = 1
                    with open("stats.pickle", "wb") as f:
                        pickle.dump(user_stats, f)

                    attachments = []
                    pic_links = {}
                    # os.chdir(os.getcwd()[:len(os.getcwd()) - 10])  # Возврат в главную директорию
                    with open("pics.pickle", "rb") as f:  # Открытие словаря со ссылками на картинки
                        pic_links = pickle.load(f)

                    os.chdir(os.getcwd() + r'/recipes')#Переход в папку с рецептами
                    if len(userlist[event.user_id]) >= len(recipes):#Сброс номеров рецептов
                        userlist[event.user_id] = []
                    curr_rec = []
                    for i in range(len(recipes)):#Добавление номеров еще не выводившихся рецептов
                        if recipes[i] not in userlist[event.user_id]:
                            curr_rec.append(i)

                    random.seed()
                    num = random.randint(0,len(curr_rec) - 1)#Номер в списке невыведенных ранее
                    userlist[event.user_id].append(recipes[curr_rec[num]])
                    try:
                        with open(recipes[curr_rec[num]], "r", encoding='utf-8') as f:
                            print(recipes[curr_rec[num]])
                            text = f.read()
                            if recipes[curr_rec[num]] not in pic_links.keys():  # Если картинки к рецепту нет
                                vk.messages.send(user_id=event.user_id,
                                                random_id=get_random_id(),
                                                message=text + "\nВывести полный рецепт?",
                                                keyboard = keyboard.get_keyboard()
                                                )
                            else:
                                image = requests.get(pic_links[recipes[curr_rec[num]]],
                                                     stream=True)  # Добавление картинки
                                photo = upload.photo_messages(photos=image.raw)[0]
                                attachments.append("photo{}_{}".format(photo["owner_id"], photo["id"]))
                                print(attachments[0])
                                vk.messages.send(user_id=event.user_id,
                                                 random_id=get_random_id(),
                                                 message=text + "\nВывести полный рецепт?",
                                                 keyboard=keyboard.get_keyboard(),
                                                 attachment=",".join(attachments)
                                                 )
                            user_recipe_flag[event.user_id] = recipes[curr_rec[num]]#Пометка о выпавшем рецепте

                    except FileNotFoundError:
                        vk.messages.send(user_id=event.user_id,
                                         random_id=get_random_id(),
                                         message="Ошибка при выводе рецепта. Попробуйте еще раз."
                                         )
                    os.chdir(os.getcwd()[:len(os.getcwd()) - 8])#Возврат главную директорию
                    with open("users.pickle", "wb") as f:
                        pickle.dump(userlist, f)

                elif event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text.lower() == "да":
                    if event.user_id not in user_recipe_flag.keys():
                        continue
                    os.chdir(os.getcwd() + r'/recipes_f')#Переход в папку с полными рецептами
                    try:
                        with open(user_recipe_flag[event.user_id][:len(recipes[curr_rec[num]]) - 4] + "_f.txt", "r", encoding='utf-8') as f:
                            text = f.read()#Открытие полного рецепта
                        attachments = []
                        pic_links = {}
                        os.chdir(os.getcwd()[:len(os.getcwd()) - 10])#Возврат в главную директорию
                        with open("pics.pickle", "rb") as f:#Открытие словаря со ссылками на картинки
                            pic_links = pickle.load(f)
                        os.chdir(os.getcwd() + r'/recipes_f')#Переход в папку с полными рецептами
                        print(user_recipe_flag[event.user_id])

                        vk.messages.send(user_id=event.user_id,
                                         random_id=get_random_id(),
                                         message=text,
                                         )

                        user_recipe_flag.pop(event.user_id)

                    except FileNotFoundError:
                        vk.messages.send(user_id=event.user_id,
                                         random_id=get_random_id(),
                                         message="Ошибка при выводе рецепта. Обратитесь к администрации."
                                         )
                    os.chdir(os.getcwd()[:len(os.getcwd()) - 10])

                elif event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text.lower() == "нет":
                    if event.user_id not in user_recipe_flag.keys():
                        continue

                elif event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text.lower() == "stats":
                    s = ""
                    for key, value in user_stats.items():
                        s += str(key) + " - " + str(value) + " использований\n"
                    vk.messages.send(
                        user_id=event.user_id,
                        random_id=get_random_id(),
                        message=s
                    )

                elif event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    vk.messages.send(
                    user_id = event.user_id,
                    random_id = get_random_id(),
                    message = "Неизвестная команда"
                    )
        except:
            continue


if __name__ == "__main__":
    main()
