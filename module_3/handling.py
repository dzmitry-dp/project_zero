import re
import numpy as np
import pandas as pd
from datetime import datetime


def find_anomalies(random_data):
    random_data_std = random_data.std()
    random_data_mean = random_data.mean()
    anomaly_cut_off = random_data_std * 3
    
    lower_limit  = random_data_mean - anomaly_cut_off 
    upper_limit = random_data_mean + anomaly_cut_off
    
    return random_data[(random_data > upper_limit) | (random_data < lower_limit)]

def reviews_decor(func): # для колонки Reviews
    def wrapper(*args, **kwargs):
        if args[0] == '[[], []]':
            return None
        else:
            return func(*args, **kwargs)
    return wrapper

def replaces(text):
    "Функция возвращает строку без перечисленных знаков"
    rep = {"[": "", "]": "", "'": ""}
    rep = dict((re.escape(k), v) for k, v in rep.items())
    pattern = re.compile("|".join(rep.keys()))
    return pattern.sub(lambda m: rep[re.escape(m.group(0))], str(text))

@reviews_decor
def format_str_values_to_list(text, replaces=replaces):
    "Функция форматирует строку в список элементов"
    if not pd.isna(text):
        new_str = replaces(text)
        return new_str.split(', ')

def create_conditions_for_changes(data):
    """Функция замены символов признака 'Price Range'
         на соответствующие числа по возрастанию"""
    if pd.isna(data):
        pass
    elif data == '$':
        return 1
    elif data == '$$ - $$$':
        return 2
    elif data == '$$$$':
        return 3

class ConfigWrapper:
    "Класс для обработки и создания новых признаков."
    def __init__(self, data):
        self.raw_data = data.copy()
        self.final_data = self.raw_data.copy()
        # обрабатываю каждый признак
        self.processing_restaurant_id() # Restaurant_id — идентификационный номер ресторана/сети ресторанов
        print('10% ...')
        self.processing_ranking() # Ranking — место, которое занимает данный ресторан среди всех ресторанов своего города
        print('20% ...')
        self.processing_cuisine_style() # Cuisine Style — кухня или кухни, к которым можно отнести блюда, предлагаемые в ресторане
        print('30% ...')
        self.processing_city() # City — город, в котором находится ресторан
        print('40% ...')
        self.processing_price_range() # Price Range — диапазон цен в ресторане
        print('50% ...')
        self.processing_number_of_reviews() # Number of Reviews — количество отзывов о ресторане
        print('60%...')
        self.processing_reviews() # Reviews — данные о двух отзывах, которые отображаются на сайте ресторана
        print('70% ...')
        self.processing_url_ta() # URL_TA — URL страницы ресторана на TripAdvisor
        print('80% ...')
        self.processing_id_ta() # ID_TA — идентификатор ресторана в базе данных TripAdvisor.
        print('90% ...')

        self.final_data.drop(columns='Restaurant_id', inplace=True) # удаляю столбец Restaurant_id
        # # self.final_data.drop(columns='City', inplace=True) # удаляю столбец City
        self.final_data.drop(columns='Cuisine Style', inplace=True) # удаляю столбец Cuisine Style
        # # self.final_data = self.final_data.drop(columns='Ranking') # удаляю столбец Ranking
        # # self.final_data = self.final_data.drop(columns='Price Range') # удаляю столбец Price Range
        # # self.final_data = self.final_data.drop(columns='Number of Reviews') # удаляю столбец Number of Reviews
        self.final_data.drop(columns='Reviews', inplace=True) # удаляю столбец Reviews
        self.final_data.drop(columns='URL_TA', inplace=True)# удаляю столбец URL_TA
        self.final_data.drop(columns='ID_TA', inplace=True) # удаляю столбец ID_TA
        # # self.final_data.drop(columns='City_Rome', inplace=True) # признак сильно коррелирует с Median_Number_of_Reviews_by_City

    def processing_restaurant_id(self):
        id_counts = self.final_data['Restaurant_id'].value_counts()\
                                                        .rename_axis('Restaurant_id')\
                                                            .reset_index(name='Restaurant_Counts')
        id_counts['Mean_Rating'] = id_counts['Restaurant_id']\
                                        .apply(lambda x : self.final_data['Rating'][self.final_data['Restaurant_id'] == x].mean())
        self.id_counts_test = id_counts
        one_restaurant = id_counts['Mean_Rating'][id_counts['Restaurant_Counts'] == 1] # значения рейтинга для ресторанов "одиночек" (= 1 ресторан)
        # отдельным признаком выделяем средний рейтинг сети ресторанов (Average_Rating_Restaurant_Chain)
        for idx in id_counts['Restaurant_id'].values:
            work_data = self.final_data[self.final_data['Restaurant_id'].isin([idx, ])]
            number_of_restaurants = id_counts['Restaurant_Counts'][id_counts['Restaurant_id'] == idx].values[0]
            if  number_of_restaurants > 1: # если сеть ресторанов (> 1 ресторана)
                self.final_data.loc[work_data.index, 'Average_Rating_Restaurant_Chain'] = id_counts['Mean_Rating'][id_counts['Restaurant_id'] == idx].values[0]
            else:
                self.final_data.loc[work_data.index.values[0], 'Average_Rating_Restaurant_Chain'] = one_restaurant.mean()
        
    def processing_city(self):
        unique_cities = self.raw_data['City'].value_counts()
        countries = {
            'London' : 'England', 'Paris' : 'France', 'Madrid' : 'Spain', 
            'Barcelona' : 'Spain', 'Berlin' : 'Germany', 'Milan' : 'Italy', 
            'Rome' : 'Italy', 'Prague' : 'Czech_c', 'Lisbon' : 'Portugal', 
            'Vienna' : 'Austria', 'Amsterdam' : 'Holland', 
            'Brussels' : 'Belgium', 'Hamburg' : 'Germany', 'Munich' : 'Germany', 
            'Lyon' : 'France', 'Stockholm' : 'Sweden', 'Budapest' : 'Romania', 
            'Warsaw' : 'Poland', 'Dublin' : 'Ireland', 'Copenhagen' : 'Denmark', 
            'Athens' : 'Greece', 'Edinburgh' : 'Scotland', 'Zurich' : 'Switzerland', 
            'Oporto' : 'Portugal', 'Geneva' : 'Switzerland', 'Krakow' : 'Poland', 
            'Oslo' : 'Norway', 'Helsinki' : 'Finland', 'Bratislava' : 'Slovakia', 
            'Luxembourg' : 'Luxembourg_c', 'Ljubljana' : 'Slovenia'
        }
        big_cities = ['London', 'Paris', 'Madrid', 'Barcelona', 'Berlin', 'Rome']

        # Big_City - рестораны в небольших городах 1, в крупных 0
        self.final_data['Big_City'] = 1
        for city in big_cities:
            self.final_data.loc[self.raw_data[self.raw_data['City'] == city].index, 'Big_City'] = 0

        # отдельным признаком выделим страны в которых находятся города
        for city in unique_cities.index:
            self.final_data.loc[self.final_data[self.final_data['City'] == city].index, 'Country'] = countries[city]   

        #  закодируем признаки City и Country методом One-Hot Encoding
        # для One-Hot Encoding в pandas есть готовая функция - get_dummies
        self.final_data = pd.get_dummies(self.final_data, columns=['City'], dtype='int64')
        self.final_data = pd.get_dummies(self.final_data, columns=['Country'], dtype='int64')

    def processing_cuisine_style(self):
        # форматируем данные в столбце
        self.final_data['Cuisine Style'] = self.final_data['Cuisine Style']\
                                                .apply(format_str_values_to_list)
        # создаю столбец "Количество кухонь в одном ресторане"
        self.final_data['Amount_Cuisine_Style'] = self.final_data['Cuisine Style'].str.len()
        # создаю признак "Среднее количество кухонь в сети ресторанов"
        self.final_data['Average_Number_of_Kitchens_Restaurant_Chain'] = \
            self.final_data['Restaurant_id'].apply(lambda x: self.final_data['Amount_Cuisine_Style'][self.final_data['Restaurant_id'] == x].mean())
        # заполняем пропуски средним значением ресторанов такого же рейтинга
        for idx in self.final_data.loc[pd.isna(self.final_data['Amount_Cuisine_Style']), :].index:
            self.final_data.at[idx, 'Amount_Cuisine_Style'] = \
                self.final_data['Amount_Cuisine_Style'][self.final_data['Rating'] == self.final_data['Rating'].iloc[idx]].mean()
        # заполняем пропуски средним значением ресторанов такого же рейтинга
        for idx in self.final_data.loc[pd.isna(self.final_data['Average_Number_of_Kitchens_Restaurant_Chain']), :].index:
            self.final_data.at[idx, 'Average_Number_of_Kitchens_Restaurant_Chain'] = \
                self.final_data['Average_Number_of_Kitchens_Restaurant_Chain'][self.final_data['Rating'] == self.final_data['Rating'].iloc[idx]].mean()
        # создаем список из уникальных стилей кухонь, присутствующих в датафрейме
        unique_cuisine_style = CuisineStyle.get_unique_values_cuisine_style(self.final_data['Cuisine Style'])
        # добавляем колонки для каждой кухни, чтобы потом не париться заполняя пропуски
        for elem in unique_cuisine_style:
            self.final_data[elem.replace(' ', '_')] = pd.Series(np.zeros(len(self.raw_data.index), dtype=int))
        # раставляем 1 в соответствующей колонке кухни
        explode_frame = self.final_data.explode('Cuisine Style')
        for cuisine in unique_cuisine_style:
            self.final_data.loc[explode_frame[explode_frame['Cuisine Style'].isin([cuisine])].index, cuisine.replace(' ', '_')] = 1

    def processing_ranking(self):
        unique_cities = self.raw_data['City'].value_counts()
        mean_ranking_on_city = self.raw_data.groupby(['City'])['Ranking'].mean()
        for city in unique_cities.index:
            self.final_data.loc[self.final_data['City'] == city, 'Mean_Ranking_on_City'] = mean_ranking_on_city.loc[city]
            self.final_data.loc[self.final_data['City'] == city, 'Count_Restorant_in_City'] = unique_cities.loc[city]
        self.final_data['Norm_Ranking'] = (self.final_data['Ranking'] - self.final_data['Mean_Ranking_on_City']) / self.final_data['Count_Restorant_in_City']

    def processing_price_range(self):
        # примением One-Hot Encoding для этого признака
        self.final_data = pd.get_dummies(self.final_data, columns=['Price Range'], dummy_na=True, dtype='int64')
        # переименовываем колонки
        self.final_data.rename(columns={'Price Range_$': 'Low_Price_Range', 'Price Range_$$ - $$$': 'Middle_Price_Range', 'Price Range_$$$$': 'High_Price_Range'}, inplace=True)
        # заменяем символы на числа в соответствующей последовательности $ - 1, $$$$ - 3
        self.final_data['Price Range'] = self.raw_data['Price Range']\
                                                .apply(create_conditions_for_changes)
        # заполняем пропуски срезним значение цен по рейтингу
        for idx in self.final_data.loc[pd.isna(self.final_data['Price Range']), :].index:
            self.final_data.at[idx, 'Price Range'] = round(self.final_data['Price Range'][self.final_data['Rating'] == self.final_data['Rating'].iloc[idx]].mean())
        # создаю признак максимальная ценовая категория у сети ресторанов
        self.final_data['Max_Price_Range_Restaurant_Chain'] = self.final_data['Restaurant_id']\
                                                                    .apply(lambda x: self.final_data['Price Range'][self.final_data['Restaurant_id'] == x].max())
        # создаю признак минимальная ценовая категория у сети ресторанов                                               
        self.final_data['Min_Price_Range_Restaurant_Chain'] = self.final_data['Restaurant_id']\
                                                                    .apply(lambda x: self.final_data['Price Range'][self.final_data['Restaurant_id'] == x].min())
        # копируем данные для удобства обращения
        self.raw_data['Price Range'] = self.final_data['Price Range'].copy()
        # среднее значение ценовой категории в зависимости от города
        self.final_data['Average_Price_Range_by_City'] = self.raw_data['City']\
                                                                .apply(lambda x: self.raw_data['Price Range'][self.raw_data['City'] == x].mean())

    def processing_number_of_reviews(self):
        # Данные принимают очень широкий диапазон значений
        # применим логорифмирование к переменной Number of Reviews
        log_number_of_reviews = np.log(self.raw_data['Number of Reviews'][~pd.isna(self.raw_data['Number of Reviews'])])
        anomalies = find_anomalies(log_number_of_reviews)
        # сохраним информацию о выбросах
        anomalies_series = self.final_data['Number of Reviews'].iloc[anomalies.index]
        self.final_data['outliers_Number_of_Reviews'] = self.final_data['Number of Reviews'].isin(anomalies_series.values).astype('int')

        # удаляю выбросы
        self.final_data.loc[self.final_data['outliers_Number_of_Reviews'] == 1, 'Number of Reviews'] = None
        # заполняем пропуски средним значением среди ресторанов с рейтингами 1, 1.5, 2, 2.5, 3, 5
        mean_number = self.final_data['Number of Reviews'][~self.final_data['Rating'].isin([3.5, 4, 4.5])].mean()
        self.final_data['Number of Reviews'] = self.final_data['Number of Reviews'].fillna(mean_number)

        # медианное значение количества отзывов по городам
        self.final_data['Median_Number_of_Reviews_by_City'] = self.raw_data['City']\
                                                                    .apply(lambda x: self.raw_data['Number of Reviews'][self.raw_data['City'] == x].median())

    def processing_reviews(self):
        # форматируем данные в удобные списки
        self.final_data['Reviews'] = self.final_data['Reviews']\
                                            .apply(format_str_values_to_list)
        # добавляем признак количество БОЛЬШИХ букв в 2х отзывах
        self.final_data['Caps_Reviews'] = self.final_data['Reviews']\
                                                .apply(Reviews.find_number_of_caps)
        # создаю серии состоящие из даты публикации последних отзывов
        self.raw_data['First_Reviews_Date'] = self.final_data['Reviews']\
                                                    .apply(Reviews.get_date_from_reviews, args=(1,))
        self.raw_data['Second_Reviews_Date'] = self.final_data['Reviews']\
                                                    .apply(Reviews.get_date_from_reviews, args=(2,))
        # время в сутках между публикациями отзывов
        self.final_data['Span_Reviews'] = self.raw_data['First_Reviews_Date'] - self.raw_data['Second_Reviews_Date']
        self.final_data['Span_Reviews'] = self.final_data['Span_Reviews']\
                                                .apply(Reviews.get_days_between_reviews)
        # затираем выбросы
        sigma = self.final_data['Span_Reviews'].mean() + 3*self.final_data['Span_Reviews'].std()
        self.final_data['Span_Reviews'] = self.final_data['Span_Reviews']\
                                                .apply(lambda x: None if x > sigma else x)
        # заполняю пропуски средним значение у такого же рейтинга
        for idx in self.final_data.loc[pd.isna(self.final_data['Span_Reviews']), :].index:
            self.final_data.at[idx, 'Span_Reviews'] = self.final_data['Span_Reviews'][self.final_data['Rating'] == self.final_data['Rating'].iloc[idx]].mean()
        for idx in self.final_data.loc[pd.isna(self.final_data['Caps_Reviews']), :].index:
            self.final_data.at[idx, 'Caps_Reviews'] = self.final_data['Caps_Reviews'][self.final_data['Rating'] == self.final_data['Rating'].iloc[idx]].mean()

    def processing_url_ta(self):
        # выделить уникальные части ссылки. Ссылка состоит из 2х частей: Название ресторана - Место
        self.raw_data['Unique_URL_Part'] = self.raw_data['URL_TA']\
                                                .apply(Url.get_unique_link_part)
        # количество символов в названии ресторана
        self.final_data['Number_of_Characters_in_the_Name'] = self.raw_data['Unique_URL_Part']\
                                                                    .apply(lambda x: len(''.join(x[0].split('_'))))

    def processing_id_ta(self):
        # удаляем дубли, которые имеют одинаковый id в базе даных
        self.final_data = self.final_data.drop_duplicates(subset=['ID_TA'], keep='last')


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
