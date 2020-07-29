import argparse
import gym
import numpy as np
import tensorflow as tf
from GAIL.network_models.PPO_Discrete import Agent
from GAIL.network_models.discriminator import Discriminator


def argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--logdir', help='log directory', default='log/train/gail')
    parser.add_argument('--savedir', help='save directory', default='models/gail')
    parser.add_argument('--iteration', default=int(1e4))
    parser.add_argument('--gamma', type=float, default=0.99)
    parser.add_argument('--update_interval', type=int, default=5)
    parser.add_argument('--actor_lr', type=float, default=0.0005)
    parser.add_argument('--critic_lr', type=float, default=0.001)
    parser.add_argument('--clip_ratio', type=float, default=0.1)
    parser.add_argument('--lmbda', type=float, default=0.95)
    parser.add_argument('--epochs', type=int, default=3)
    return parser.parse_args()


def main(args):
    env = gym.make('CartPole-v1')
    env.seed(42)

    agent = Agent(env, args)
    discriminator = Discriminator(env, lr=0.01)

    # 得到专家的观测和行动
    expert_observations = np.genfromtxt('trajectory/observations.csv')
    expert_actions = np.genfromtxt('trajectory/actions.csv', dtype=np.int32)

    obs = env.reset()
    success_num = 0

    for iteration in range(args.iteration):
        observations = []
        actions = []
        rewards = []
        v_preds = []
        run_policy_steps = 0

        while True:
            run_policy_steps += 1
            act = agent.actor.get_action(state=obs)
            v_pred = agent.critic.model.predict(obs[np.newaxis])[0][0]

            next_obs, reward, done, info = env.step(act)

            observations.append(obs)
            actions.append(act)
            rewards.append(reward)
            v_preds.append(v_pred)

            if done:
                v_pred = agent.critic.model.predict(next_obs[np.newaxis])[0][0]
                v_preds_next = v_preds[1:] + [v_pred]
                obs = env.reset()
                break
            else:
                obs = next_obs

        print(sum(rewards))
        if sum(rewards) >= 475:
            success_num += 1
            if success_num >= 100:
                agent.save_model(args.savedir + '/gail_ppo.h5')
                print('Clear!! Model saved.')
                break
        else:
            success_num = 0

        observations = np.array(observations)
        actions = np.array(actions).astype(dtype=np.int32)

        for i in range(2):
            discriminator.train(expert_s=expert_observations, expert_a=expert_actions,
                                agent_s=observations, agent_a=actions)

        d_rewards = discriminator.get_rewards(agent_s=observations, agent_a=actions)
        gaes, td_targets = agent.gae_target(d_rewards, v_preds, v_preds_next, done)

        # train policy
        for epoch in range(10):
            actor_loss = agent.actor.train(observations, actions, gaes)
            # print(actor_loss)
            critic_loss = agent.critic.model.train_on_batch(observations, td_targets)
            # print(critic_loss/len(observations))


if __name__ == '__main__':
    args = argparser()
    main(args)
