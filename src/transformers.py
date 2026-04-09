import re

from sklearn.base import BaseEstimator, TransformerMixin


class TextCleaner(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        return [re.sub(r'[^a-záéíóúñ\s]', '', str(text).lower()) for text in X]