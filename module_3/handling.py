import re
import math
import numpy as np
import pandas as pd
from datetime import datetime


def format_str_values_to_list(text):
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
        # обрабатываю каждый признак
        self.processing_city()
        self.processing_cuisine_style()
        self.processing_ranking()
        self.processing_price_range()
        self.processing_number_of_reviews()
        self.processing_reviews()
        self.processing_url_ta()

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
            self.final_data[elem] = pd.Series(np.zeros(len(self.raw_data.index), dtype=int))

        # раставляем 1 в соответствующей колонке кухни
        explode_series = self.final_data['Cuisine Style'].explode()
        for cuisine in unique_cuisine_style:
            for index_ in explode_series.loc[explode_series.isin([cuisine])].index.values:
                self.final_data.at[index_, cuisine] = 1

        # создаю столбец "Количество кухонь в одном ресторане"
        self.final_data['Amount_Cuisine_Style'] = self.final_data['Cuisine Style'].str.len()

        # удаляю столбец Cuisine Style
        self.final_data = self.final_data.drop(columns='Cuisine Style')
        # заполняем пропуски
        self.final_data['Amount_Cuisine_Style'].fillna(self.final_data['Amount_Cuisine_Style'].mean(), inplace=True)

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
        # заполняем пропуски
        self.final_data['Price Range'].fillna(0, inplace=True)


    def processing_number_of_reviews(self):
        # фиксирую места пропусков информации
        self.final_data['Number_of_Reviews_isNAN'] = pd.isna(self.raw_data['Number of Reviews']).astype('uint8')
        # заполняем пропуск
        self.final_data['Number of Reviews'].fillna(0, inplace=True)

    def processing_reviews(self):
        # форматируем данные в удобные списки
        self.final_data['Reviews'] = self.final_data['Reviews']\
                                                .apply(format_str_values_to_list)
        # фиксирую места пропусков информации
        self.final_data['Reviews_isNAN'] = pd.isna(self.raw_data['Reviews']).astype('uint8')
        # количество БОЛЬШИХ букв в 2х отзывах
        self.final_data['Caps_Reviews'] = self.final_data['Reviews'].apply(Reviews.find_number_of_caps)
        # серия состоящая из списков в которых 2 даты публикации 2х последний отзывов
        self.raw_data['Reviews_Date'] = self.final_data['Reviews'].apply(Reviews.get_date_from_reviews)
        # время в сутках между публикациями отзывов
        self.final_data['Span_Reviews'] = self.raw_data['Reviews_Date'].apply(Reviews.get_days_between_reviews)
        # удаляю столбец Reviews
        self.final_data = self.final_data.drop(columns='Reviews')
        # заполняем пропуск
        self.final_data['Span_Reviews'].fillna(0, inplace=True)
        self.final_data['Caps_Reviews'].fillna(self.final_data['Caps_Reviews'].mean(), inplace=True)

    def processing_url_ta(self):
        # выделить уникальные части ссылки. Ссылка состоит из 2х частей: Название ресторана - Место
        self.raw_data['Unique_URL_Part'] = self.raw_data['URL_TA'].apply(Url.get_unique_link_part)
        # удаляю столбец URL_TA
        self.final_data = self.final_data.drop(columns='URL_TA')


class CuisineStyle:
    def get_unique_values_cuisine_style(series):
        cuisine = set()
        for list_ in series:
            if list_ != None:
                for elem in list_:
                    cuisine.add(elem)
        return list(cuisine)


class Reviews:
    def get_date_from_reviews(reviews_list):
        reviews_date_list = []
        if reviews_list != None:
            for value in reviews_list[-2:]:
                try:
                    reviews_date_list.append(datetime.strptime(value, '%m/%d/%Y'))
                except:
                    continue
            return reviews_date_list

    def get_days_between_reviews(reviews_date):
        if reviews_date != None:
            if len(reviews_date) == 2:
                delta = reviews_date[0] - reviews_date[1]
            elif len(reviews_date) == 1:
                return None
            return delta.days

    def find_number_of_caps(reviews_list):
        if reviews_list != None:
            caps_list = []
            for elem in reviews_list:
                caps = [l for l in elem if l.isupper()]
                if len(caps) != 0:
                    caps_list += caps
            return len(caps_list)


class Url:
    def get_unique_link_part(str_link):
        parts = str_link.replace('.html', '').split('-')
        return parts[-2:]

if __name__ == '__main__':
    pd.set_option('display.max_columns', None)
    df = pd.read_csv('main_task.xls')
    df_obj = ConfigWrapper(df)

