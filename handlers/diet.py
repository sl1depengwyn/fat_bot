import asyncio
import sqlite3

import requests
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from bs4 import BeautifulSoup
from telegraph import Telegraph
from telegraph.utils import html_to_content

import config
from SQLighter import SQLighter
from misc import dp, bot


class Diet(StatesGroup):
    initial = State()
    waiting_for_start = State()
    waiting_for_dietgoal = State()
    waiting_for_gender = State()
    waiting_for_age = State()
    waiting_for_height = State()
    waiting_for_weight = State()
    waiting_for_desired_weight = State()
    waiting_for_diet = State()
    done = State()


genders = {"женский": "f",
           "мужской": "m"}

dietgoals = {"похудение": "losing",
             "поддержание": "support",
             "набор веса": "increase"}


async def get_diet_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('✅ Сделать расчет')
    return keyboard


async def make_keyboard(d):
    inline_btns = []
    for item in d.keys():
        inline_btns.append(types.InlineKeyboardButton(item.upper(), callback_data=d[item]))
    inline_kb = types.InlineKeyboardMarkup()
    for btn in inline_btns:
        inline_kb.add(btn)
    return inline_kb


async def scheduled_message(message, text, bot):
    await asyncio.sleep(30 * 60)
    await message.answer(text.format(bot))


@dp.message_handler(commands=['start'], state='*')
async def initial_step(message: types.Message):
    if Diet.initial:
        try:
            db = SQLighter(config.db)
            db.add_line(message.from_user.id)
            db.close()
        except sqlite3.IntegrityError:
            pass
    inline_btn = types.InlineKeyboardButton('ПОЛУЧИТЬ ПЛАН ПИТАНИЯ ⤵', callback_data='get_diet')
    inline_kb = types.InlineKeyboardMarkup().add(inline_btn)
    await message.answer('''Привет, {} 👋

Я твой персональный помощник по умной диете 🍏   

Чтобы составить твой персональный план питания ответь на несколько простых вопросов, после чего Я СГЕНЕРИРУЮ для тебя результат'''.format(
        message.from_user.first_name), reply_markup=inline_kb)
    await Diet.waiting_for_start.set()


@dp.callback_query_handler(lambda c: c.data == 'get_diet', state=Diet.waiting_for_start)
async def process_callback_initial_button(callback_query: types.CallbackQuery):
    return await diet_step_start(callback_query.message)


@dp.message_handler(lambda m: m.text == '✅ Сделать расчет', state='*')
async def diet_step_start(message: types.Message):
    await message.answer("1️⃣Выбери свою цель:", reply_markup=await make_keyboard(dietgoals))
    await Diet.waiting_for_dietgoal.set()


@dp.callback_query_handler(lambda c: c.data in dietgoals.values(), state=Diet.waiting_for_dietgoal)
async def process_callback_button_for_dietgoal(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(dietgoal=callback_query.data)
    await callback_query.message.answer("2️⃣Укажите ваш пол:", reply_markup=await make_keyboard(genders))
    await Diet.waiting_for_gender.set()


@dp.message_handler(state=Diet.waiting_for_dietgoal, content_types=types.ContentTypes.TEXT)
async def diet_step_dietgoal(message: types.Message, state: FSMContext):
    if message.text.lower() not in dietgoals.keys():
        await message.reply("Пожалуйста, выбери цель, используя клавиатуру ниже",
                            reply_markup=await make_keyboard(dietgoals))
        return
    await state.update_data(dietgoal=dietgoals[message.text.lower()])
    await message.answer("2️⃣Укажите ваш пол:", reply_markup=await make_keyboard(genders))
    await Diet.waiting_for_gender.set()


@dp.callback_query_handler(lambda c: c.data in genders.values(), state=Diet.waiting_for_gender)
async def process_callback_button_for_gender(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(gender=callback_query.data)
    await callback_query.message.answer("3️⃣Укажите возраст (целое число)")
    await Diet.waiting_for_age.set()


@dp.message_handler(state=Diet.waiting_for_gender, content_types=types.ContentTypes.TEXT)
async def diet_step_gender(message: types.Message, state: FSMContext):
    if message.text.lower() not in genders.keys():
        await message.reply("Пожалуйста, выбери пол, используя клавиатуру ниже",
                            reply_markup=await make_keyboard(genders))
        return
    await state.update_data(gender=dietgoals[message.text.lower()])
    await message.answer("3️⃣Укажите возраст (целое число)")
    await Diet.waiting_for_age.set()


@dp.message_handler(state=Diet.waiting_for_age, content_types=types.ContentTypes.TEXT)
async def diet_step_height(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or message.text.isdigit() and int(message.text) < 0:
        await message.reply("Укажите возраст:")
        return
    await state.update_data(age=message.text)
    await message.answer("4️⃣Рост в сантиметрах (целое число)")
    await Diet.waiting_for_height.set()


@dp.message_handler(state=Diet.waiting_for_height, content_types=types.ContentTypes.TEXT)
async def diet_step_current_weight(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or message.text.isdigit() and int(message.text) < 0:
        await message.reply("Укажите рост:")
        return
    await state.update_data(height=message.text)
    await message.answer("5️⃣Масса тела на сегодняшний день, кг (целое число)")
    await Diet.waiting_for_weight.set()


@dp.message_handler(state=Diet.waiting_for_weight, content_types=types.ContentTypes.TEXT)
async def diet_step_desired_weight(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or message.text.isdigit() and int(message.text) < 0:
        await message.reply("Укажите вес:")
        return
    await state.update_data(currentWeight=message.text)
    if (await state.get_data())['dietgoal'] != 'support':
        await message.answer("6️⃣Масса тела желаемая, кг (целое число)")
        await Diet.waiting_for_desired_weight.set()
    else:
        await Diet.waiting_for_desired_weight.set()
        await diet_step_final(message, state)


@dp.message_handler(state=Diet.waiting_for_desired_weight, content_types=types.ContentTypes.TEXT)
async def diet_step_final(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or message.text.isdigit() and int(message.text) < 0:
        await message.reply("Укажите желаемый вес:")
        return
    await state.update_data(desiredWeight=message.text)
    await Diet.done.set()

    user_data = await state.get_data()
    user_data['saturation_speed'] = 10
    user_data['pregnant'] = 'n'
    user_data['breastFeeding'] = 'n'
    user_data['email'] = 'bot@bot.bot'
    user_data['form_version'] = 'v2'
    user_data['olddietfile'] = ''
    user_data['drugs'] = ''
    user_data['forbiddenFood'] = ''
    user_data['ration'] = ''
    user_data['activity'] = ''
    user_data['diet_text'] = ''
    user_data['diet_raw_text'] = ''
    user_data['disease'] = ''
    user_data['calories'] = ''
    user_data['mass_time'] = ''
    user_data['date_to_goal'] = ''
    user_data['factors'] = ''
    user_data['episodes_of_something'] = ''
    user_data['physical_activity'] = ''
    user_data['do_you_want_special_fitfood'] = ''
    user_data['time_of_phis_training'] = ''
    user_data['pref_products'] = ''
    await message.answer('Наш искусственный интеллект формирует для Вас индивидуальный план питания 🍽, подождите.', reply_markup=await get_diet_keyboard())

    await bot.send_chat_action(message.chat.id, 'typing')

    r = requests.post(config.backend_url + "/dietform/fillproductionform_api/", user_data)

    if r.status_code == 200:
        data = requests.get(config.backend_url + r.json()['url'])

        telegraph_user = Telegraph().create_account(message.from_user.first_name)
        telegraph = Telegraph(telegraph_user.access_token)

        soup = BeautifulSoup(data.text, 'html.parser')
        blocks = soup.find_all('div', {'class': 'row w-row'})
        days = [{'0': '0'}] * 7

        for block in blocks:
            html_content = ''

            day_number = block.find('span', {'class': 'day_number'}).text
            html_content += f'<h3>День {day_number.strip()}</h3>\n'

            daily_fppcal_vals = block.find_all('div', {'class': 'daily-fpccal-value'})
            html_content += f'<p>Белки: {daily_fppcal_vals[0].text.strip()}\n'
            html_content += f'Жиры: {daily_fppcal_vals[1].text.strip()}\n'
            html_content += f'Углеводы: {daily_fppcal_vals[2].text.strip()}\n'
            html_content += f'Калории: {daily_fppcal_vals[3].text.strip()}</p>\n\n'

            daily_product_list = block.find_all('p', {'class': 'daily-products-list'})
            html_content += '<p><b>Продукты:</b></p>\n<p>'
            for prod in daily_product_list:
                html_content += prod.text.strip() + '\n'

            html_content += '</p>\n'

            rations = block.find_all('div', {'class': 'ration-div2'})
            for ration in rations:
                html_content += f'<h4>{ration.find("h2", {"class": "ration-name"}).text.strip()}</h4>\n'

                fppcal_vals = ration.find_all('div', {'class': 'fpccal-value'})
                html_content += f'<p>Белки: {fppcal_vals[0].text.strip()}\n' \
                                f'Жиры: {fppcal_vals[1].text.strip()}\n' \
                                f'Углеводы: {fppcal_vals[2].text.strip()}\n' \
                                f'Калории: {fppcal_vals[3].text.strip()}</p>\n\n'

                html_content += f'<p><b>{ration.find("div", {"class": "meal-name"})}</b></p>\n<p>'

                products = ration.find_all('div', {'class': 'product-div'})
                for product in products:
                    name = product.find('div', {'class': 'product-name'})
                    weight = product.find('div', {'class': 'product-weight'})

                    html_content += f'{name.text.strip()} <b>{weight.text.strip()}</b>\n'

            html_content += '</p><br>'

            page = telegraph.create_page(title=f'Рацион ({day_number})', content=html_to_content(html_content))

            day = {'url': page.url,
                   'day_number': day_number,
                   'plate': f'План на {day_number}-й день'}

            days[int(day_number) - 1] = day

        day_keyboard = {}
        for day in days:
            day_keyboard[day['plate']] = 'get_d' + '-_-' + day['day_number'] + '-_-' + day['url']
        await message.answer('Готово!👌 ', reply_markup=await get_diet_keyboard())
        await message.answer('Используйте кнопки ниже⬇️, чтобы увидеть рацион для этого дня:', reply_markup=await make_keyboard(day_keyboard))

        await scheduled_message(message, '''Для того, чтобы: 
        ✅получить рекомендации к рациону
        ✅узнать как правильно готовить продукты
        ✅чем можно заменять продукты
        ✅какие продукты можно сократить и удалить, а какие есть без ограничений
        ✅как гармонично сочетать меню с различными видами тренировок и физической нагрузки...
    
        ПЕРЕХОДИТЕ В НАШЕГО ОСНОВНОГО ПОМОЩНИКА ➡️  {}''', config.redirect_bot)
    else:
        await message.answer('К сожалению, наш алгоритм не смог сформировать под Ваш запрос план питания, попробуйте изменить исходные данные 🤷‍♀️', reply_markup=await get_diet_keyboard())


@dp.callback_query_handler(lambda c: c.data.split('-_-')[0] == 'get_d', state=Diet.done)
async def process_callback_initial_button(callback_query: types.CallbackQuery):
    callback_data = callback_query.data.split('-_-')
    await callback_query.message.edit_text(f'<a href="{callback_data[2]}">План</a> на {callback_data[1]}-й день',
                                           parse_mode='HTML', reply_markup=callback_query.message.reply_markup)
