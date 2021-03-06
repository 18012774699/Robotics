from tensorflow import keras
import tensorflow as tf
import random
import numpy as np

model = keras.models.Sequential([
    # 将输入转换为7 x 7 128通道的feature map
    keras.layers.Dense(7 * 7 * 128, input_shape=[64]),
    keras.layers.Reshape([7, 7, 128]),
    keras.layers.BatchNormalization(),
    # 对应上面，上采样至 14 x 14
    keras.layers.Conv2DTranspose(256, kernel_size=3, strides=2, padding="same", activation="selu"),
    keras.layers.BatchNormalization(),
    # keras.layers.Conv2DTranspose(64, kernel_size=3, strides=2, padding="same", activation="selu"),
    # keras.layers.BatchNormalization(),
    # 此处1为颜色通道数
    keras.layers.Conv2DTranspose(1, kernel_size=7, strides=2, padding="same", activation="tanh"),
    keras.layers.Reshape([28, 28, 1])
])

X_train = np.array([1])
lr = 0.01
s = 20 * len(X_train) // 32

embedding = tf.one_hot(X_train, depth=3)
ground_truth_labels = keras.utils.to_categorical(X_train)

learning_rate = keras.optimizers.schedules.ExponentialDecay(lr, s, 0.1)
# optimizer = keras.optimizers.Adam(learning_rate)
optimizer = keras.optimizers.Adam(learning_rate, clipvalue=1.0)
model.compile(loss="binary_crossentropy", optimizer="RMSprop")
print(model.summary())

keras.backend.set_value(model.optimizer.lr, 0.01)

model.save_weights('my_keras_model.h5')
model.load_weights("my_keras_model.h5")

early_stopping = keras.callbacks.EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)
save_model = keras.callbacks.ModelCheckpoint("my_keras_model.h5", save_best_only=True, save_weights_only=True)

noise = tf.random.normal(shape=[64, 128])

index = [i for i in range(len(X_train))]
random.shuffle(index)
image_org = X_train[index]

# ========================
lr = 3e-3           # most important
batch_size = 128    # big

kl = tf.keras.losses.KLDivergence()
loss_fn = keras.losses.Huber()
loss_fn = keras.losses.mean_squared_error

keras.layers.LeakyReLU(0.2)
keras.layers.tanh()
keras.layers.BatchNormalization()

"RMSprop"
