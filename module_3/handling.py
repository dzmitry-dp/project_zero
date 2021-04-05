import re
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
        self.raw_data = data.copy()
        self.final_data = self.raw_data.copy()
        # зафиксирую где отсутствует информация
        # self.final_data['Cuisine_Style_isNAN'] = pd.isna(self.raw_data['Cuisine Style']).astype('int64')
        self.final_data['Price_Range_isNAN'] = pd.isna(self.raw_data['Price Range']).astype('int64')
        # self.final_data['Reviews_isNAN'] = pd.isna(self.raw_data['Reviews']).astype('int64')
        # обрабатываю каждый признак
        self.processing_ranking() # до обработки id, т.к. заполняю средним по сети ресторанов
        self.processing_restaurant_id()
        self.processing_cuisine_style()
        self.processing_price_range()
        self.processing_reviews()
        self.processing_number_of_reviews()
        self.processing_city() # после cuisine style, price range и number of reviews, т.к. заполняем средним по городам
        self.processing_url_ta()
        self.processing_id_ta() # ?первым обрабатываю признак ID_TA т.к. есть дублирующая информация

    def processing_restaurant_id(self):
        # приводим id к числовому формату
        self.final_data['Restaurant_id'] = self.raw_data['Restaurant_id'].apply(lambda x: int(x.replace('id_', '')))
        # выделяем отдельным признаком средний рейтинг сети ресторанов
        self.final_data['Average_Rating_Series_Restaurant'] = self.final_data['Restaurant_id'].apply(lambda x: round(self.final_data.Rating[self.final_data.Restaurant_id == x].mean(), 1))
        # удаляю столбец Restaurant_id
        self.final_data = self.final_data.drop(columns='Restaurant_id')

    def processing_city(self):
        # big_cities = ['London', 'Paris', 'Madrid', 'Barcelona', 'Berlin', 'Milan']
        big_cities_data = pd.get_dummies(self.final_data[
                                            (self.final_data['City'] == 'London') |\
                                            (self.final_data['City'] == 'Paris') |\
                                            (self.final_data['City'] == 'Madrid') |\
                                            (self.final_data['City'] == 'Barcelona') |\
                                            (self.final_data['City'] == 'Berlin') |\
                                            (self.final_data['City'] == 'Milan')
                                            ], columns=['City'], dummy_na=True, dtype='int64')
        self.final_data = self.final_data.merge(big_cities_data, how='left') 
        # удаляем дубликаты
        self.final_data.drop_duplicates(inplace=True)
        # представители малых городов 0, крупные города 1
        self.final_data['City_London'].fillna(0, inplace=True)
        self.final_data['City_Paris'].fillna(0, inplace=True)
        self.final_data['City_Madrid'].fillna(0, inplace=True)
        self.final_data['City_Barcelona'].fillna(0, inplace=True)
        self.final_data['City_Berlin'].fillna(0, inplace=True)
        self.final_data['City_Milan'].fillna(0, inplace=True)
        # рестораны в небольших городах 1, в крупных 0
        self.final_data['City_nan'].fillna(1, inplace=True)
        # удаляю столбец City
        self.final_data = self.final_data.drop(columns='City')

    def processing_cuisine_style(self):
        # форматируем данные в столбце
        self.final_data['Cuisine Style'] = self.final_data['Cuisine Style']\
                                                .apply(format_str_values_to_list)
        # копирую столбец для удобства обращения
        self.raw_data['Cuisine Style'] = self.final_data['Cuisine Style'].copy()
        # создаю столбец "Количество кухонь в одном ресторане"
        self.final_data['Amount_Cuisine_Style'] = self.final_data['Cuisine Style'].str.len()
        # заполняем пропуски средним значением ресторанов такого же рейтинга
        for idx in self.final_data[self.final_data['Amount_Cuisine_Style'].isnull()].index:
            self.final_data.at[idx, 'Amount_Cuisine_Style'] = round(self.final_data['Amount_Cuisine_Style'][self.final_data['Rating'] == self.final_data['Rating'].iloc[idx]].mean())
 
        # создаем список из уникальных стилей кухонь, присутствующих в датафрейме
        unique_cuisine_style = CuisineStyle.get_unique_values_cuisine_style(self.final_data['Cuisine Style'])
        # добавляем колонки для каждой кухни
        for elem in unique_cuisine_style:
            self.final_data[elem] = pd.Series(np.zeros(len(self.raw_data.index), dtype=int))
        # # # заполняем пропуски Cuisine Style самой популярной кухней в городе
        # # # nan_series = self.raw_data[self.raw_data['Cuisine Style'].isnull()]
        # # # for idx in nan_series.index:
        # # #     self.final_data.at[idx, 'Cuisine Style'] = CuisineStyle.get_most_popular_cuisine(self.raw_data['Cuisine Style'][self.raw_data['City'] == self.raw_data.iloc[idx]['City']])
        # раставляем 1 в соответствующей колонке кухни
        explode_series = self.final_data['Cuisine Style'].explode()
        for cuisine in unique_cuisine_style:
            for index_ in explode_series.loc[explode_series.isin([cuisine])].index.values:
                self.final_data.at[index_, cuisine] = 1
        # удаляю столбец Cuisine Style
        self.final_data = self.final_data.drop(columns='Cuisine Style')

    def processing_ranking(self):
        # удаляем выбросы
        # mean = self.raw_data['Ranking'][self.raw_data['Rating'] == 5].mean()
        mean = self.raw_data['Ranking'][self.raw_data['Rating'] == 5].mean()
        # sigma = mean + 3*self.raw_data['Ranking'][self.raw_data['Rating'] == 5].std()
        sigma = mean + 3*self.raw_data['Ranking'][self.raw_data['Rating'] == 5].std()
        self.final_data['Ranking'] = self.final_data['Ranking'].apply(lambda x: None if x > sigma else x)
        # заполняем пропуски средним значением сети ресторанов
        # for idx in self.final_data[self.final_data['Ranking'].isnull()].index:
        #     self.final_data.at[idx, 'Ranking'] = self.final_data['Ranking'][self.final_data['Restaurant_id'] == self.final_data['Restaurant_id'].iloc[idx]].median()

        for idx in self.final_data[self.final_data['Ranking'].isnull()].index:
            self.final_data.at[idx, 'Ranking'] = self.final_data['Ranking'][self.final_data['Rating'] == self.final_data['Rating'].iloc[idx]].mean()
        # self.final_data['Ranking'].fillna(self.final_data['Ranking'].median(), inplace=True)
        # удаляю столбец Ranking
        # self.final_data = self.final_data.drop(columns='Ranking')

    def processing_price_range(self):
        # Для некоторых алгоритмов МЛ даже для не категориальных 
        # признаков можно применить One-Hot Encoding, и это может улучшить качество модели. Пробуйте разные подходы к кодированию признака - никто не знает заранее, что может взлететь.
        self.final_data['Price Range'] = pd.get_dummies(self.final_data, columns=['Price Range'], dummy_na=True, dtype='int64')
        
        def create_conditions_for_changes(data):
            if pd.isna(data):
                pass
            elif data == '$':
                return 1
            elif data == '$$ - $$$':
                return 2
            elif data == '$$$$':
                return 3

        self.final_data['Price Range'] = self.raw_data['Price Range'].apply(create_conditions_for_changes)
        # заполняем пропуски срезним значение цен по городам
        for idx in self.final_data[self.final_data['Price Range'].isnull()].index:
            self.final_data.at[idx, 'Price Range'] = round(self.final_data['Price Range'][self.final_data['Rating'] == self.final_data['Rating'].iloc[idx]].mean())
        # удаляю столбец
        # self.final_data = self.final_data.drop(columns='Price Range')

    def processing_number_of_reviews(self):
        # удаляем выбросы
        mean = self.raw_data['Number of Reviews'].mean()
        sigma = mean + 3*self.raw_data['Number of Reviews'].std()
        self.final_data['Number of Reviews'] = self.final_data['Number of Reviews'].apply(lambda x: None if x > sigma else x)
        # заполняем пропуски средним значением по городам
        for idx in self.final_data[self.final_data['Number of Reviews'].isnull()].index:
            self.final_data.at[idx, 'Number of Reviews'] = round(self.final_data['Number of Reviews'][self.final_data['Rating'] == self.final_data['Rating'].iloc[idx]].mean())
        # удаляю столбец Number of Reviews
        # self.final_data = self.final_data.drop(columns='Number of Reviews')

    def processing_reviews(self):
        # форматируем данные в удобные списки
        self.final_data['Reviews'] = self.final_data['Reviews']\
                                                .apply(format_str_values_to_list)
        # количество БОЛЬШИХ букв в 2х отзывах
        self.final_data['Caps_Reviews'] = self.final_data['Reviews'].apply(Reviews.find_number_of_caps)
        # серия состоящая даты публикации последних отзывов
        self.raw_data['First_Reviews_Date'] = self.final_data['Reviews'].apply(Reviews.get_date_from_reviews, args=(1,))
        self.raw_data['Second_Reviews_Date'] = self.final_data['Reviews'].apply(Reviews.get_date_from_reviews, args=(2,))
        # время в сутках между публикациями отзывов
        self.final_data['Span_Reviews'] = self.raw_data['First_Reviews_Date'] - self.raw_data['Second_Reviews_Date']
        self.final_data['Span_Reviews'] = self.final_data['Span_Reviews'].apply(Reviews.get_days_between_reviews)
        # затираем выбросы
        sigma = self.final_data['Span_Reviews'].mean() + 3*self.final_data['Span_Reviews'].std()
        self.final_data['Span_Reviews'] = self.final_data['Span_Reviews'].apply(lambda x: None if x > sigma else x)
        # заполняем пропуски
        # self.final_data['Span_Reviews'].fillna(round(self.final_data['Span_Reviews'].mean()), inplace=True)
        # заполняем пропуски средним значением по городам
        for idx in self.final_data[self.final_data['Span_Reviews'].isnull()].index:
            self.final_data.at[idx, 'Span_Reviews'] = round(self.final_data['Span_Reviews'][self.final_data['Rating'] == self.final_data['Rating'].iloc[idx]].mean())
        for idx in self.final_data[self.final_data['Caps_Reviews'].isnull()].index:
            self.final_data.at[idx, 'Caps_Reviews'] = round(self.final_data['Caps_Reviews'][self.final_data['Rating'] == self.final_data['Rating'].iloc[idx]].mean())
        # self.final_data['Caps_Reviews'].fillna(round(self.final_data['Caps_Reviews'].mean()), inplace=True)
        # удаляю столбец Reviews
        self.final_data = self.final_data.drop(columns='Reviews')

    def processing_url_ta(self):
        # выделить уникальные части ссылки. Ссылка состоит из 2х частей: Название ресторана - Место
        # self.raw_data['Unique_URL_Part'] = self.raw_data['URL_TA'].apply(Url.get_unique_link_part)
        # удаляю столбец URL_TA
        self.final_data = self.final_data.drop(columns='URL_TA')

    def processing_id_ta(self):
        # удаляем дубли, которые имеют одинаковый id в базе даных
        self.final_data = self.final_data.drop_duplicates(subset=['ID_TA'], keep='last')
        # удаляю столбец ID_TA
        self.final_data = self.final_data.drop(columns='ID_TA')


class CuisineStyle:
    def get_most_popular_cuisine(city_series):
        cuisine_dict = {}
        for list_ in city_series:
            if list_ != None:
                for elem in list_:
                    if elem in cuisine_dict:
                        cuisine_dict[elem] += 1
                    else:
                        cuisine_dict[elem] = 1
        return [max(cuisine_dict, key=cuisine_dict.get)]

    def get_unique_values_cuisine_style(series):
        cuisine = set()
        for list_ in series:
            if list_ != None:
                for elem in list_:
                    cuisine.add(elem)
        return list(cuisine)


class Reviews:
    def get_date_from_reviews(reviews_list, arg):
        reviews_date_list = []
        if reviews_list != None:
            for value in reviews_list[-2:]:
                try:
                    reviews_date_list.append(datetime.strptime(value, '%m/%d/%Y'))
                except:
                    continue
            if arg == 1:
                return reviews_date_list[0]
            elif arg == 2:
                try:
                    return reviews_date_list[1]
                except IndexError:
                    return None

    def get_days_between_reviews(span_date):
        if not pd.isna(span_date):
            days = span_date.days
            if days < 0:
                return int(-days)
            else:
                return int(days)

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
