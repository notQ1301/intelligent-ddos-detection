
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import classification_report, accuracy_score
import joblib

data = pd.read_csv("data.csv")
feature_names = ['packet_count', 'byte_count', 'packet_count_per_second',
                  'byte_count_per_second', 'flow_duration_sec', 'ip_proto',
                  'tp_src', 'tp_dst', 'flags']
X = data[feature_names]
y = data['label']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

nb = GaussianNB()
nb.fit(X_train, y_train)

y_pred = nb.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))

joblib.dump(nb, "nb_model.pkl")
