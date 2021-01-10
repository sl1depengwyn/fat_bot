import json
import pandas as pd
from emoji import emojize
import random
from diet_generator.search import search
from diet_generator.models import FormsDiets


def get_context(form):

    def rand_add():
        min_v = 0.5
        max_v = 1.5
        if random.randint(0,1) == 0:
            return round(random.uniform(min_v,max_v), 3)
        else:
            return round(random.uniform(-min_v,-max_v), 3)

    # TODO: Workaround - here we get rid of error when pandas finds
    # some key issue. So we add small random number to users weight,
    # height, age and makes attempt again while will not get success
    attempts = 0
    success = False
    _weight = form.currentWeight
    _age = form.age
    _target_weight = form.currentWeight
    _height = form.height
    while not success and attempts < 5:
        if attempts != 0:
            form.currentWeight = _weight + rand_add()
            form.age = _age + rand_add()
            form.currentWeight = _target_weight + rand_add()
            form.height = _height + rand_add()
        try:
            resultid = search.find_similar(form)
            print ("RESULT ID: " + str(resultid))
        except Exception as e:
            #logger.info("ERROR {}".format(e))
            print("ERROR", e)
            resultid = None
        if resultid is None:
            attempts += 1
        else:
            success = True
            diet = FormsDiets.objects.get(pk=resultid)
            diet_id = diet.olddietfile.replace('.txt', '')
            form.currentWeight = _weight
            form.age = _age
            form.currentWeight = _target_weight
            form.height = _height
            form.calculated_diet_id = diet_id
            form.save()
            context = generate_context(diet_id, form_id=form.pk)
            return context
    # TODO: BAD THING
    diet = FormsDiets.objects.filter(form_version="oldv1").order_by("?").first()
    diet_id = diet.olddietfile.replace('.txt', '')
    return generate_context(diet_id, form_id=form.pk)


def diet_json(form):

    if form.calculated_diet_id == '':
        context = get_context(form)
        return context
    else:
        context = generate_context(form.calculated_diet_id, form_id=form.pk)
        return context


def generate_context(json_file_id, form_id=0):
    user = None
    if form_id != 0:
        user = FormsDiets.objects.get(pk=form_id)
    JSON_FOLDER = '/jsons/'
    json_file = open(JSON_FOLDER + str(json_file_id) + '.json', 'r')
    lines = json_file.read()
    json_obj = json.loads(lines)
    products_csv = pd.read_csv('products.csv', delimiter=',', error_bad_lines=False, )

    for day in json_obj:  # Day 1
        daily_products = {}
        d_p_value = 0.0
        d_f_value = 0.0
        d_c_value = 0.0
        d_cal_value = 0.0
        for ration in json_obj[day]:  # Завтрак
            r_p_value = 0.0
            r_f_value = 0.0
            r_c_value = 0.0
            r_cal_value = 0.0
            for i, product_array in enumerate(json_obj[day][ration]['products']):  # array
                try:
                    daily_products[product_array['product name']] = daily_products[product_array['product name']] + \
                                                                    product_array['weight']
                except:
                    daily_products[product_array['product name']] = product_array['weight']
                weight = product_array['weight']
                product = product_array['product name']
                p_csv = products_csv[products_csv['product_name'] == product]
                row_index = p_csv.index.values[0]
                p = p_csv.get_value(row_index, 'proteins')
                f = p_csv.get_value(row_index, 'fats')
                c = p_csv.get_value(row_index, 'carbohydrates')
                cal = p_csv.get_value(row_index, 'calories')
                p_value = weight * 0.01 * p
                f_value = weight * 0.01 * f
                c_value = weight * 0.01 * c
                cal_value = weight * 0.01 * cal
                r_p_value = r_p_value + p_value
                r_f_value = r_f_value + f_value
                r_c_value = r_c_value + c_value
                r_cal_value = r_cal_value + cal_value
                d_p_value = d_p_value + p_value
                d_f_value = d_f_value + f_value
                d_c_value = d_c_value + c_value
                d_cal_value = d_cal_value + cal_value
                json_obj[day][ration]['products'][i]['product_name'] = json_obj[day][ration]['products'][i].pop(
                    'product name')
            json_obj[day][ration]['ration_fpccal'] = {
                'f': int(r_f_value), 'p': int(r_p_value), 'c': int(r_c_value), 'cal': int(r_cal_value)
            }
        json_obj[day]['daily_fpccal'] = {
            'f': int(d_f_value), 'p': int(d_p_value), 'c': int(d_c_value), 'cal': int(d_cal_value)
        }
        json_obj[day]['daily_products'] = daily_products

    diet = []
    for day in ['1', '2', '3', '4', '5', '6', '7']:
        ration_array = []
        for ration in ['Завтрак', 'Перекус', 'Обед', 'Перекус 2', 'Ужин']:
            ration_array.append(json_obj[day][ration])
        diet.append(
            {'daily_total':
                 {'day': day,
                  'daily_fpccal': json_obj[day]['daily_fpccal'],
                  'daily_products': json_obj[day]['daily_products']},
             'ration': ration_array
             })
    context = {'diet': diet, 'user_info': user, 'json_file_id': json_file_id}
    return context


def random_icon(arg=""):
    if arg == "day":
        return random.sample([':princess:', ':heart_eyes:', ':kissing_heart:'], 1)[0]
    elif arg == "breakfast":
        return random.sample([':strawberry:', ':cherries:', ':apple:'], 1)[0]
    else:
        return ":tomato:"


def generate_diet_text_for_day(day, form, ration="whole_day"):

    fpccal = day["daily_total"]["daily_fpccal"]
    text = ""

    if ration == "whole_day" or ration == "daily_products":
        text += "Белки: {} г, \nЖиры: {} г, \nУглеводы: {} г, \nКаллории: {} Ккал\n".format(fpccal["p"], fpccal["f"], fpccal["c"], fpccal["cal"])

        for product, total_weight in day["daily_total"]["daily_products"].items():
            text += "{} - {} г\n".format(product, total_weight)

    if ration == "whole_day":
        for i, ration_obj in enumerate(day["ration"]):
            if i == 0:
                text += emojize("\nЗавтрак" + random_icon("breakfast"), use_aliases=True)
            elif i == 1 or i==3:
                text += emojize("\nПерекус:sunny:", use_aliases=True)
            elif i == 2:
                text += emojize("\nОбед:tomato:", use_aliases=True)
            elif i == 4:
                text += emojize("\nУжин:milky_way:", use_aliases=True)

            ration_fpccal = ration_obj["ration_fpccal"]
            text += """\nБелки: {} г, \nЖиры: {} г, \nУглеводы: {} г, \nКаллории: {} ккал""".format(ration_fpccal["p"], ration_fpccal["f"], ration_fpccal["c"], ration_fpccal["cal"])

            text += "\n" + ration_obj["ration_name"] + "\n"
            for product in ration_obj["products"]:
                text += "{} {} г\n".format(product["product_name"], product["weight"])

    if ration in ["breakfast", "snack1", "lunch", "snack2", "dinner"]:
        if ration == "breakfast":
            text += emojize("\nЗавтрак" + random_icon("breakfast"), use_aliases=True)
            ration_obj = day["ration"][0]
        elif "snack1" in ration:
            text += emojize("\nПерекус:sunny:", use_aliases=True)
            ration_obj = day["ration"][1]
        elif ration == "lunch":
            text += emojize("\nОбед:tomato:", use_aliases=True)
            ration_obj = day["ration"][2]
        elif "snack2" in ration:
            text += emojize("\nПерекус:sunny:", use_aliases=True)
            ration_obj = day["ration"][3]
        elif ration == "dinner":
            text += emojize("\nУжин:milky_way:", use_aliases=True)
            ration_obj = day["ration"][4]

        ration_fpccal = ration_obj["ration_fpccal"]

        text += """\nБелки: {} г, \nЖиры: {} г, \nУглеводы: {} г, \nКаллории: {} ккал""".format(ration_fpccal["p"], ration_fpccal["f"], ration_fpccal["c"], ration_fpccal["cal"])

        text += "\n" + ration_obj["ration_name"] + "\n"
        for product in ration_obj["products"]:
            text += "{} {} г\n".format(product["product_name"], product["weight"])
    if ration != "daily_fpccal":
        if isinstance(form.currentWeight, int):
            water = form.currentWeight * 39.2
            text += "\nЕжедневно для вас рекомендуется {} л воды, не считая других напитков: чая, кофе, морсов\n".format(round(water / 1000, 1))
        text += "Между каждым приемом пищи старайтесь выдержать перерыв от 2 до 4 часов"

    return text


def generate_diet_text_for_day_json(day, form, ration="whole_day"):

    del day["daily_total"]["day"]

    if ration == "whole_day" or ration == "daily_products":
        products_text = ""
        for product, total_weight in day["daily_total"]["daily_products"].items():
            products_text += "{} - {} г\n".format(product, total_weight)
        day["daily_total"]["daily_products"] = products_text

    if ration == "whole_day":
        for i, ration_obj in enumerate(day["ration"]):
            if i == 0:
                ration_time = "breakfast"
            elif i == 1:
                ration_time = "snack1"
            elif i == 2:
                ration_time = "lunch"
            elif i==3:
                ration_time = "snack2"
            elif i == 4:
                ration_time = "dinner"

            ration_fpccal = ration_obj["ration_fpccal"]

            ration_product_text = ""
            for product in ration_obj["products"]:
                ration_product_text += "{} {} г\n".format(product["product_name"], product["weight"])

            day[ration_time] = {
                "ration_fpccal": ration_obj["ration_fpccal"],
                "ration_name": ration_obj["ration_name"],
                "products": ration_product_text
            }

    del day["ration"]
    day["status_code"] = 1
    day["status_message"] = "ok"

    return day


def generate_products_list(all_days, form, number_of_days):

    all_days = all_days[:number_of_days]

    array = []
    for day in all_days:
        for product, _ in day["daily_total"]["daily_products"].items():
            array.append(product)
    product_list = { v: 0 for v in set(array)}

    for day in all_days:
        for product, total_weight in day["daily_total"]["daily_products"].items():
            product_list[product] += total_weight

    text = ""
    for product, total_weight in product_list.items():
        text += "{} - {} г\n".format(product, total_weight)

    return text


def generate_products_list_json(all_days, form, number_of_days, start_day):

    end_day = start_day + number_of_days if start_day + number_of_days <= 21 else 21

    all_days = all_days[start_day:end_day]

    array = []
    for day in all_days:
        for product, _ in day["daily_total"]["daily_products"].items():
            array.append(product)
    product_list = { v: 0 for v in set(array)}

    for day in all_days:
        for product, total_weight in day["daily_total"]["daily_products"].items():
            product_list[product] += total_weight

    text = ""
    for product, total_weight in product_list.items():
        text += "{} - {} г\n".format(product, total_weight)

    day = {}
    day["status_code"] = 1
    day["status_message"] = "ok"
    day["products"] = text
    return day
