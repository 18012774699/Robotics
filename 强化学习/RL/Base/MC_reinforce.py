# 策略梯度（PG）
import gym
import tensorflow as tf
import numpy as np
from tensorflow import keras

env = gym.make("CartPole-v1")
obs = env.reset()
# obs: 推车的水平位置（0.0 为中心）、速度（正是右）、杆的角度（0.0 为垂直）及角速度（正为顺时针）

# img = env.render(mode="rgb_array")    # 渲染
print(env.action_space)     # Discrete(2)

n_inputs = 4  # == env.observation_space.shape[0]

model = keras.models.Sequential([
    keras.layers.Dense(5, activation="elu", input_shape=[n_inputs]),
    keras.layers.Dense(env.action_space.n, activation="softmax"),
])
# print(model.summary())


def play_one_step(env, obs, model, loss_fn):
    with tf.GradientTape() as tape:
        # 此处有问题prob
        prob = model.predict(obs[np.newaxis])[0]
        action_prob = model(obs[np.newaxis])[0]
        action = np.random.choice(env.action_space.n, 1, p=prob)[0]
        y_target = np.zeros([env.action_space.n], dtype=np.float32)
        y_target[action] = 1
        loss = tf.reduce_mean(loss_fn(y_target, action_prob))
    grads = tape.gradient(loss, model.trainable_variables)
    obs, reward, done, info = env.step(action)
    return obs, reward, done, grads


# 执行多个周期的函数
def play_multiple_episodes(env, n_episodes, n_max_steps, model, loss_fn):
    all_rewards = []
    all_grads = []
    for episode in range(n_episodes):
        current_rewards = []
        current_grads = []
        obs = env.reset()
        for step in range(n_max_steps):
            obs, reward, done, grads = play_one_step(env, obs, model, loss_fn)
            current_rewards.append(reward)
            current_grads.append(grads)
            if done:
                break
        all_rewards.append(current_rewards)
        all_grads.append(current_grads)
    return all_rewards, all_grads


def discount_rewards(rewards, discount_factor):
    discounted = np.array(rewards)
    for step in range(len(rewards) - 2, -1, -1):
        discounted[step] += discounted[step + 1] * discount_factor
    return discounted


def discount_and_normalize_rewards(all_rewards, discount_factor):
    all_discounted_rewards = [discount_rewards(rewards, discount_factor) for rewards in all_rewards]
    flat_rewards = np.concatenate(all_discounted_rewards)
    reward_mean = flat_rewards.mean()
    reward_std = flat_rewards.std()
    return [(discounted_rewards - reward_mean) / reward_std for discounted_rewards in all_discounted_rewards]


n_iterations = 150
n_episodes_per_update = 10
n_max_steps = 200
discount_factor = 0.95

optimizer = keras.optimizers.Adam(lr=0.01)
loss_fn = keras.losses.categorical_crossentropy

for iteration in range(n_iterations):
    all_rewards, all_grads = play_multiple_episodes(env, n_episodes_per_update, n_max_steps, model, loss_fn)
    total_rewards = sum(map(sum, all_rewards))
    print("\rIteration: {}, mean rewards: {:.1f}".format(iteration, total_rewards / n_episodes_per_update), end="")

    all_final_rewards = discount_and_normalize_rewards(all_rewards, discount_factor)
    all_mean_grads = []
    # 循环每个可训练变量，计算每个变量的梯度加权平均，权重是final_reward
    for var_index in range(len(model.trainable_variables)):
        mean_grads = tf.reduce_mean([final_reward * all_grads[episode_index][step][var_index]
                                     for episode_index, final_rewards in enumerate(all_final_rewards)
                                     for step, final_reward in enumerate(final_rewards)], axis=0)
        all_mean_grads.append(mean_grads)
    # 将这些平均梯度应用于优化器：微调模型的变量
    optimizer.apply_gradients(zip(all_mean_grads, model.trainable_variables))
