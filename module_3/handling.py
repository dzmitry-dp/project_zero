import re
import math
import numpy as np
import pandas as pd


def format_str_values_to_list(text):
    '''
    Функция форматирует строку в список:
    str("['European', 'French', 'International']") --> [European, French, International]
    '''
    def replaces(text):
        rep = {"[": "", "]": "", "'": ""}
        rep = dict((re.escape(k), v) for k, v in rep.items())
        pattern = re.compile("|".join(rep.keys()))
        return pattern.sub(lambda m: rep[re.escape(m.group(0))], str(text))

    if not pd.isna(text):
        if text == '[[], []]': # для колонки Reviews
            return None
        new_str = replaces(text)
        return new_str.split(', ')


class ConfigWrapper:
    def __init__(self, data):
        self.raw_data = data
        self.final_data = self.raw_data.copy()
        # удаляю не нужные для модели признаки
        self.final_data.drop(['Restaurant_id','ID_TA',], axis = 1, inplace=True)

    def processing_city(self):
        self.final_data = pd.get_dummies(self.final_data, columns=['City'], dummy_na=True)

    def processing_cuisine_style(self):
        # зафиксирую где отсутствует информации в колонке Cuisine Style
        self.final_data['Cuisine_Style_isNAN'] = pd.isna(self.final_data['Cuisine Style']).astype('uint8')
        # форматируем данные в столбце
        self.final_data['Cuisine Style'] = self.final_data['Cuisine Style']\
                                                .apply(format_str_values_to_list)
        
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

        # создаю столбец "Количество кухонь в одном ресторане"
        self.final_data['Amount_Cuisine_Style'] = self.final_data['Cuisine Style'].str.len()

        # удаляю столбец Cuisine Style
        self.final_data = self.final_data.drop(columns='Cuisine Style')

    def processing_ranking(self):
        pass

    def processing_price_range(self):
        # первым делом зафиксируем места пропусков информации
        self.final_data['Price_Range_isNAN'] = pd.isna(self.raw_data['Price Range']).astype('uint8')

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
        # фиксирую места пропусков информации
        self.final_data['Number_of_Reviews_isNAN'] = pd.isna(self.raw_data['Number of Reviews']).astype('uint8')

    def processing_reviews(self):
        # форматируем данные в удобные списки
        self.final_data['Reviews'] = self.final_data['Reviews']\
                                                .apply(format_str_values_to_list)
        # фиксирую места пропусков информации
        self.final_data['Reviews_isNAN'] = pd.isna(self.raw_data['Reviews']).astype('uint8')

        # создаю столбец "Количество отзывов". Норма =2. None =0
        self.final_data['Amount_Reviews'] = self.final_data['Reviews'].str.len()
        self.final_data['Amount_Reviews'].fillna(0, inplace=True)

        # вычислить время между двумя отзывами. В данных предоставлены последние 2 отзыва, на тот момент
        # отзывы которые написаны КАПСОМ

    def processing_url_ta(self):
        # выделить уникальные части ссылки. Ссылка состоит из 2х частей: Название ресторана - Место
        pass


class CuisineStyle:
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
    df_obj.processing_city()
    df_obj.processing_cuisine_style()
    df_obj.processing_ranking()
    df_obj.processing_price_range()
    df_obj.processing_number_of_reviews()
    df_obj.processing_reviews()
    df_obj.processing_url_ta()

