import re
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.base import BaseEstimator, TransformerMixin

from db import SessionLocal, Review

class TextCleaner(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None): 
        return self

    def transform(self, X, y=None):
        return [re.sub(r'[^a-záéíóúñ\s]', '', str(text).lower()) for text in X]


def train_model():
    db = SessionLocal()

    records = db.query(Review.review, Review.label).all()
    X = [r[0] for r in records]
    y = [r[1] for r in records]

    db.close()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, shuffle=True, test_size=0.2, random_state=42
    )
    
    mlflow.set_experiment("Sentiment_Classifier_MVP")
    with mlflow.start_run():
        max_features_tfidf = 2500
        ngrams = (1, 2)
        min_doc_freq = 5
        reg_c = 1.0
        max_iter_lr = 1000

        pipeline = Pipeline([
            ('limpiador', TextCleaner()),
            ('vectorizador', TfidfVectorizer(
                max_features=max_features_tfidf,
                stop_words='english',
                ngram_range=ngrams,
                min_df=min_doc_freq
            )),
            ('clasificador', LogisticRegression(
                C=reg_c,
                max_iter=max_iter_lr
            ))
        ])

        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        print(f"Accuracy del modelo: {(acc*100):.1f}%")

        mlflow.log_param("max_features", max_features_tfidf)
        mlflow.log_param("ngram_range", str(ngrams))
        mlflow.log_param("stop_words", "english")
        mlflow.log_param("min_df", min_doc_freq)
        mlflow.log_param("C_LogisticRegression", reg_c)
        mlflow.log_metric("accuracy", acc)

        mlflow.sklearn.log_model(pipeline, "nlp_model_producc")

if __name__ == "__main__":
    train_model()