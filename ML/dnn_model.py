
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.utils import to_categorical

data = pd.read_csv("data.csv")
feature_names = ['packet_count', 'byte_count', 'packet_count_per_second',
                  'byte_count_per_second', 'flow_duration_sec', 'ip_proto',
                  'tp_src', 'tp_dst', 'flags']
X = data[feature_names]
y = data['label']

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# Chuyển đổi nhãn thành categorical (one-hot)
y_train_cat = to_categorical(y_train)
y_test_cat = to_categorical(y_test)

model = Sequential()
model.add(Dense(64, input_dim=X_train.shape[1], activation='relu'))
model.add(Dense(32, activation='relu'))
model.add(Dense(y_train_cat.shape[1], activation='softmax'))

model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
model.fit(X_train, y_train_cat, epochs=10, batch_size=32, verbose=1)

loss, acc = model.evaluate(X_test, y_test_cat, verbose=0)
print("Test Accuracy:", acc)

model.save("dnn_model.h5")
