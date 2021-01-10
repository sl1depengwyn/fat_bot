import datetime

class search():
    def find_similar(updated_form):
        import pandas as pd
        from copy import deepcopy
        from diet_generator.models import FormsDiets
        queryset = FormsDiets.objects.values()
        df_from_query = pd.DataFrame.from_records(queryset)
        form = df_from_query[df_from_query['id'] == int(updated_form.pk)]
        data = df_from_query[(df_from_query['id'] != int(updated_form.pk)) & (df_from_query['form_version'] == "oldv1")]

        """ 
        # db access
        engine = create_engine('mysql+pymysql://root:SmartDiet@51.15.137.250/SmartDiet?charset=utf8')

        # print('engine created')
        # load data
        data = pd.read_sql('SELECT * FROM dietForm_formsdiets where form_version="oldv1" and id<>' + str(form.pk),
                           con=engine)
        form = pd.read_sql('SELECT * FROM dietForm_formsdiets where id=' + str(form.pk), con=engine)
        # print('data and form success')
        """
        point2 = datetime.datetime.now()
        # print("RUNTIME 2", point2 - point1)
        # clear data and preprocess
        del data['created']
        del form['created']
        del data['last_updated']
        del form['last_updated']
        del data['olddietfile']
        del form['olddietfile']
        del data['form_version']
        del form['form_version']
        del data['diet_text']
        del form['diet_text']
        del data['calories']
        del form['calories']

        # TODO: Workaround for pandas key error
        form["currentWeight"] = updated_form.currentWeight
        form["age"] = updated_form.age
        form["currentWeight"] = updated_form.currentWeight
        form["height"] = updated_form.height
        # TODO: End

        # calculated fields
        form['weight_change'] = form['currentWeight'] - form['desiredWeight']
        data['weight_change'] = data['currentWeight'] - data['desiredWeight']
        form['height_weight'] = form['height'] / form['currentWeight']
        data['height_weight'] = data['height'] / data['currentWeight']

        # synonym groups and exclusive foods
        synonym_groups = [
            ["мясо", "птица", "рыба", "телятина", "курица", "свинина", "бекон", "тушенка",
             "красное мясо", "яйца", "веган", "вегетарианец", "травоядный", "утка",
             "утиное мясо", "утиное мясо", "баранина", "конина", "крольчатина"]
            , ["молочные продукты", "молоко", "сметана", "ряженка", "творог", "лактоза", "лактаза"]
        ]
        stop_words = ["аллергия на", "аллергия", "тошнит от", "нельзя", "тошнит"]

        def contains_fuzzy(example_in, example_ex, row):
            example_ex = example_ex.strip().lower()
            if not example_ex: return False
            # remove stop words
            for aa, bb in enumerate(stop_words):
                example_ex = example_ex.replace(bb, "")
            # explode ex
            parts = example_ex.strip().split(',')
            # clear examples
            for key, val in enumerate(parts):
                parts[key] = val.lower().strip()
            # extend ex with synonyhms
            extended_parts = deepcopy(parts)
            for key, val in enumerate(parts):
                for key2, group in enumerate(synonym_groups):
                    if val in group:
                        # extend parts with group
                        extended_parts += group
            parts = set(extended_parts)
            # foreach ex find ex in row and return true
            for key, val in enumerate(parts):
                if row['diet_raw_text'].lower().find(val) > -1:
                    # # print(row['id'],val) filter reason
                    return True
            # return false
            return False

        def relative_number_distance_old(maxv, n1, n2):
            return abs((maxv - abs(n1 - n2)) / maxv)

        def relative_number_distance(maxv, minv, n1, n2):
            return abs((maxv - minv - abs(n1 - n2)) / (maxv - minv))

        def gender_comparison(n1, n2):
            if (n1 == n2):
                return 1
            else:
                return 0

        def jacard_similarity(n1, n2):
            # explode and clear
            if not n1: return 0
            n1 = n1.split(',')
            for key, val in enumerate(n1):
                n1[key] = val.strip().lower()
            if not n2: return 0
            n2 = n2.split(',')
            for key, val in enumerate(n2):
                n2[key] = val.strip().lower()
            # calculate
            intersection = len(list(set(n1) & set(n2)))
            s1 = len(set(n1))
            s2 = len(set(n2))
            return (intersection / (s1 + s2 - intersection))

        def equality(n1, n2):
            if n1 == n2:
                return 1
            else:
                return 0

        # define features, weights, exclusion lambda functions, and similarity lambda functions
        features = {
            'dietgoal': {
                'weight': 0,
                'exclude_function': lambda example_in, example_ex, row: example_in == example_ex,
                'comparison_function': lambda example_in, example_ex, row: 50
            },
            'gender': {
                'weight': 50,
                'exclude_function': lambda example_in, example_ex, row: True,
                'comparison_function': lambda example_in, example_ex: gender_comparison(example_in, example_ex)
            },
            'age': {
                'weight': 60,
                'exclude_function': lambda example_in, example_ex, row: True,
                'comparison_function': lambda example_in, example_ex: relative_number_distance(
                    data["age"].max(),
                    data["age"].min(),
                    example_in, example_ex
                    )
            },
            'drugs': {
                'weight': 70,
                'exclude_function': lambda example_in, example_ex, row: True,
                'comparison_function': lambda example_in, example_ex: jacard_similarity(example_in, example_ex)
            },
            'forbiddenFood': {
                'weight': 0,
                'exclude_function': lambda example_in, example_ex, row: not (
                contains_fuzzy(example_in, example_ex, row)),
                'comparison_function': lambda example_in, example_ex, row: 50
            },
            'ration': {
                'weight': 40,
                'exclude_function': lambda example_in, example_ex, row: True,
                'comparison_function': lambda example_in, example_ex: jacard_similarity(example_in, example_ex)
            },
            'breastFeeding': {
                'weight': 0,
                'exclude_function': lambda example_in, example_ex, row: example_in == example_ex,
                'comparison_function': lambda example_in, example_ex, row: 50
            },
            'pregnant': {
                'weight': 0,
                'exclude_function': lambda example_in, example_ex, row: example_in == example_ex,
                'comparison_function': lambda example_in, example_ex, row: 50
            },
            'activity': {
                'weight': 20,
                'exclude_function': lambda example_in, example_ex, row: True,
                'comparison_function': lambda example_in, example_ex: equality(example_in, example_ex)
            },
            'saturation_speed': {
                'weight': 40,
                'exclude_function': lambda example_in, example_ex, row: True,
                'comparison_function': lambda example_in, example_ex: relative_number_distance(
                    data["saturation_speed"].max(), data["saturation_speed"].min(), example_in, example_ex)
            },
            'disease': {
                'weight': 70,
                'exclude_function': lambda example_in, example_ex, row: True,
                'comparison_function': lambda example_in, example_ex: jacard_similarity(example_in, example_ex)
            },
            'height_weight': {
                'weight': 80,
                'exclude_function': lambda example_in, example_ex, row: True,
                'comparison_function': lambda example_in, example_ex: relative_number_distance(
                    data["height_weight"].max(), data["height_weight"].min(), example_in, example_ex)
            },
            'weight_change': {
                'weight': 90,
                'exclude_function': lambda example_in, example_ex, row: True,
                'comparison_function': lambda example_in, example_ex: relative_number_distance(
                    data["weight_change"].max(), data["weight_change"].min(), example_in, example_ex)
            },
            'currentWeight': {
                'weight': 20,
                'exclude_function': lambda example_in, example_ex, row: True,
                'comparison_function': lambda example_in, example_ex: relative_number_distance(
                    data["currentWeight"].max(), data["currentWeight"].min(), example_in, example_ex)
            }

        }
        point3 = datetime.datetime.now()
        # print("RUNTIME 3", point3 - point2)
        working_datatable = deepcopy(data)

        # apply filter functions
        for key, value in features.items():
            for index, row in data.iterrows():
                if (value['exclude_function'](row[key], form[key][0], row) == False):
                    working_datatable = working_datatable[working_datatable.id != row['id']]

        pd.options.mode.chained_assignment = None
        for key, value in features.items():
            # print("ROW", index)

            if (value['weight'] != 0):
                working_datatable[key + '_similarity'] = working_datatable['id'].astype(float)
                for index, row in working_datatable.iterrows():
                    working_datatable[key + '_similarity'][index] = value['comparison_function'](
                        working_datatable[key][index], form[key][0])

        working_datatable['similarity_rating'] = working_datatable['id'].astype(float)
        for index, row in working_datatable.iterrows():
            similarity = 0
            for feature_name, feature in features.items():
                if (feature['weight'] != 0):
                    similarity += (row[feature_name + '_similarity'] * feature['weight'])
            working_datatable['similarity_rating'][index] = similarity

        if (len(working_datatable) > 0):
            # print('result id counted')
            result = working_datatable.sort_values('similarity_rating', ascending=False)['id'].iloc[0]
            end = datetime.datetime.now()
            # print("RUNTIME 4", end - point3)
            return result
        else:
            return None
