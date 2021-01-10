import requests
import asyncio
import sqlite3
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

import config
from misc import dp

from SQLighter import SQLighter


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
    user_is_admin = State()


genders = {"женский": "f",
           "мужской": "m"}

dietgoals = {"похудение": "losing",
             "поддержание": "support",
             "набор веса": "increase"}


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


@dp.message_handler(state=Diet.done, content_types=types.ContentTypes.TEXT)
async def echo(message: types.Message):
    await message.answer("Вкусно?")


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


@dp.message_handler(commands=['reset'], state='*')
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
    await message.answer("6️⃣Масса тела желаемая, кг (целое число)")
    await Diet.waiting_for_desired_weight.set()


@dp.message_handler(state=Diet.waiting_for_desired_weight, content_types=types.ContentTypes.TEXT)
async def diet_step_final(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or message.text.isdigit() and int(message.text) < 0:
        await message.reply("Укажите желаемый вес:")
        return
    await state.update_data(desiredWeight=message.text)
    user_data = await state.get_data()
    user_data["secret_key"] = "#uzgth-s)yjp$yyltthol+nrq$t4(nvg_qa!yf%b2grrpx^hf("
    user_data["email"] = "bot@bot.bot"
    await message.answer('''ОТЛИЧНО, {} 👍

Первый шаг к твоему идеальному Я сделан 🤗

Держи свой персональный недельный план питания для твоей цели ⤵️'''.format(message.from_user.first_name))

    r = requests.post("http://personalcoach.pro/api/v1/save_form_and_get_diet/", user_data)
    print(user_data)

    await scheduled_message(message, '''Для того, чтобы: 
    ✅получить рекомендации к рациону
    ✅узнать как правильно готовить продукты
    ✅чем можно заменять продукты
    ✅какие продукты можно сократить и удалить, а какие есть без ограничений
    ✅как гармонично сочетать меню с различными видами тренировок и физической нагрузки...

    ПЕРЕХОДИТЕ В НАШЕГО ОСНОВНОГО ПОМОЩНИКА ➡️  {}''', config.redirect_bot)


