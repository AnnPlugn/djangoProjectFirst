import os
import numpy as np
import pandas as pd
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
import joblib

def load_data():
    path = os.path.join('C:/Users/aplyg/PycharmProjects/djangoProjectFirst/static/housing.csv')
    df = pd.read_csv(path)
    df.dropna(inplace=True)
    return df
def visualize_results(y_true, y_pred):
    plt.figure(figsize=(10, 6))
    plt.scatter(y_true, y_pred, color='blue', alpha=0.5)
    plt.plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], '--', color='red')
    plt.xlabel("Actual Values")
    plt.ylabel("Predicted Values")
    plt.title("Actual vs Predicted Values")
    plt.grid(True)
    plt.xlim(0, 450000)
    plt.ylim(0, 450000)
    plt.savefig('C:/Users/aplyg/PycharmProjects/djangoProjectFirst/static/imagepolinom.png')
    return 'C:/Users/aplyg/PycharmProjects/djangoProjectFirst/static/imagepolinom.png'

def train_polynomial_regression_model():
    df = load_data()

    X = df[['longitude', 'latitude', 'housing_median_age', 'total_rooms', 'total_bedrooms', 'population', 'households', 'median_income']]
    y = df['median_house_value']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    poly = PolynomialFeatures(degree=3)
    X_train_poly = poly.fit_transform(X_train)

    model = LinearRegression()
    model.fit(X_train_poly, y_train)

    joblib.dump(model, os.path.join('C:/Users/aplyg/PycharmProjects/djangoProjectFirst/static/polynomial_regression_model.pkl'))  # Используйте относительный путь для сохранения модели
    joblib.dump(poly, os.path.join('C:/Users/aplyg/PycharmProjects/djangoProjectFirst/static/polynomial_features_transformer.pkl'))  # Используйте относительный путь для сохранения трансформера

    print("Модель полиномиальной регрессии успешно обучена и сохранена.")

    X_test_poly = poly.transform(X_test)
    y_pred = model.predict(X_test_poly)
    image_path = visualize_results(y_test, y_pred)

    return 'Модель успешно обучена и результаты визуализированы'

train_polynomial_regression_model()