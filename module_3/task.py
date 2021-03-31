import re
import math
import numpy as np
import pandas as pd


"""
Restaurant_id — идентификационный номер ресторана / сети ресторанов;
City — город, в котором находится ресторан;
Cuisine Style — кухня или кухни, к которым можно отнести блюда, предлагаемые в ресторане;
Ranking — место, которое занимает данный ресторан среди всех ресторанов своего города;
Rating — рейтинг ресторана по данным TripAdvisor (именно это значение должна будет предсказывать модель);
Price Range — диапазон цен в ресторане;
Number of Reviews — количество отзывов о ресторане;
Reviews — данные о двух отзывах, которые отображаются на сайте ресторана;
URL_TA — URL страницы ресторана на TripAdvisor;
ID_TA — идентификатор ресторана в базе данных TripAdvisor.
"""

class ConfigWrapper:
    def __init__(self, data):
        self.raw_data = data
        self.final_data = self.raw_data.copy()

    def processing_restaurant_id(self):
        self.final_data['Restaurant_id'] = self.final_data['Restaurant_id']\
                                                .apply(lambda x: x.replace('id_', ''))

    def processing_city(self):
        self.final_data = pd.get_dummies(self.final_data, columns=['City'], dummy_na=True)

    def processing_cuisine_style(self):
        # форматируем данные в столбце
        self.final_data['Cuisine Style'] = self.final_data['Cuisine Style']\
                                                .apply(CuisineStyle.format_cuisine_style_values_to_list)
        # создаем список из уникальных стилей, присутствующих в датафрейме
        unique_cuisine_style = CuisineStyle.get_unique_values_cuisine_style(self.final_data['Cuisine Style'])
        # добавляем колонки для каждой кухни
        for elem in unique_cuisine_style:
            self.final_data[elem] = pd.Series(np.zeros(len(df.index), dtype=int))
        # раставляем 1 в соответствующей колонке кухни
        explode_series = self.final_data['Cuisine Style'].explode()
        for cuisine in unique_cuisine_style:
            for index_ in explode_series.loc[explode_series.isin([cuisine])].index.values:
                self.final_data.at[index_, cuisine] = 1

        # создать столбец "Количество кухонь в одном ресторане"
        self.final_data['Cuisine Style'] = self.final_data['Cuisine Style']\
                                                .apply(lambda x: len(x) if not pd.isna(x))


    def processing_ranking(self):
        pass

    def processing_price_range(self):
        def create_conditions_for_changes(data):
            if pd.isna(data):
                pass
            elif data == '$':
                return 1
            elif data == '$$ - $$$':
                return 2
            elif data == '$$$$':
                return 3

        self.final_data['Price Range'] = self.final_data['Price Range'].apply(create_conditions_for_changes)


    def processing_number_of_reviews(self):
        pass

    def processing_reviews(self):
        pass

    def processing_url_ta(self):
        pass

    def processing_id_ta(self):
        self.final_data['ID_TA'] = self.final_data['ID_TA'].apply(lambda x: x.replace('d', ''))


class CuisineStyle:
    def format_cuisine_style_values_to_list(text):
        '''
        str("['European', 'French', 'International']") --> [European, French, International]
        '''
        if not pd.isna(text):
            rep = {"[": "", "]": "", "'": ""}
            rep = dict((re.escape(k), v) for k, v in rep.items())
            pattern = re.compile("|".join(rep.keys()))
            new_str = pattern.sub(lambda m: rep[re.escape(m.group(0))], str(text))
            return new_str.split(', ')

    def get_unique_values_cuisine_style(series):
        cuisine = set()
        for list_ in series:
            if list_ != None:
                for elem in list_:
                    cuisine.add(elem)
        return list(cuisine)


if __name__ == '__main__':
    pd.set_option('display.max_columns', None)
    df = pd.read_csv('main_task.xls')
    df_obj = ConfigWrapper(df)
    df_obj.processing_restaurant_id()
    df_obj.processing_city()
    df_obj.processing_cuisine_style()
    df_obj.processing_ranking()
    df_obj.processing_price_range()
    df_obj.processing_number_of_reviews()
    df_obj.processing_reviews()
    df_obj.processing_url_ta()
    df_obj.processing_id_ta()

